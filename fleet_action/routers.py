from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import get_current_user, require_permission
from app.models.character import Character
from app.models.user import User

from fleet_action import esi as fleet_esi
from fleet_action.models import ActionStatus, FleetAction, PapRecord
from app.services.esi_names import resolve_entity_names
from fleet_action.schemas import (
    ActionDetailResponse,
    ActionResponse,
    CharacterPapStatsResponse,
    CreateActionRequest,
    IssuePapRequest,
    IssuePapResponse,
    PapRecordResponse,
    PapStatsItem,
)

router = APIRouter()

# MOTD 通知模板
_MOTD_TEMPLATE = (
    "[PAP 行动通知] 行动「{action_name}」(ID:{action_id}) "
    "已由舰队指挥官 {fc_name} 手动发放出勤记录 (PAP)，"
    "当前累计出勤人数：{total_pap_count}。"
    "请确保您已加入舰队以获得本次出勤记录。"
)


# ── 内部依赖 ─────────────────────────────────────────────────────────────────

async def _get_active_action(action_id: int, db: AsyncSession = Depends(get_db)) -> FleetAction:
    result = await db.execute(select(FleetAction).where(FleetAction.id == action_id))
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="行动不存在")
    return action


async def _verify_character_ownership(
    fc_character_id: int,
    current_user: User,
    db: AsyncSession,
) -> Character:
    """确认 fc_character_id 属于当前登录用户，防止 token 滥用。"""
    result = await db.execute(
        select(Character).where(
            Character.character_id == fc_character_id,
            Character.user_id == current_user.id,
        )
    )
    char = result.scalar_one_or_none()
    if char is None:
        raise HTTPException(
            status_code=403,
            detail="该角色不属于您的账号，无法代为操作"
        )
    return char


# ── GET /characters ──────────────────────────────────────────────────────────

@router.get("/characters", summary="当前用户的 EVE 角色列表（供表单动态选项使用）")
async def list_user_characters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回当前登录用户绑定的所有角色，格式：[{"label": name, "value": character_id}]"""
    result = await db.execute(
        select(Character).where(Character.user_id == current_user.id)
    )
    characters = result.scalars().all()
    return [
        {"label": c.character_name, "value": c.character_id}
        for c in characters
    ]


# ── GET /fleet/info ───────────────────────────────────────────────────────────

@router.get("/fleet/info", summary="查询 FC 当前所在舰队")
async def get_fleet_info(
    fc_character_id: int = Query(..., description="FC 的角色 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fleet-action.manage")),
):
    """通过 ESI 实时查询 fc_character_id 当前所在舰队。返回 fleet_id、role 等信息。"""
    await _verify_character_ownership(fc_character_id, current_user, db)
    token, refresh_tok = await fleet_esi.get_valid_token(fc_character_id, db)
    return await fleet_esi.get_character_fleet(fc_character_id, token, refresh_tok)


# ── GET /actions ──────────────────────────────────────────────────────────────

@router.get("/actions", summary="列出所有行动")
async def list_actions(
    status: str | None = Query(None, description="按状态过滤：active 或 ended"),
    fc_character_name: str | None = Query(None, description="按指挥官名称模糊搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("fleet-action.read")),
):
    stmt = select(FleetAction).order_by(FleetAction.created_at.desc())
    if status:
        stmt = stmt.where(FleetAction.status == status)
    if fc_character_name:
        stmt = stmt.where(FleetAction.fc_character_name.ilike(f"%{fc_character_name}%"))

    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    actions = result.scalars().all()

    action_ids = [a.id for a in actions]
    pap_counts: dict[int, int] = {}
    if action_ids:
        count_result = await db.execute(
            select(PapRecord.action_id, func.count(PapRecord.id))
            .where(PapRecord.action_id.in_(action_ids))
            .group_by(PapRecord.action_id)
        )
        pap_counts = dict(count_result.all())

    items = [
        ActionResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            fleet_id=a.fleet_id,
            fc_character_id=a.fc_character_id,
            fc_character_name=a.fc_character_name,
            status=a.status,
            created_at=a.created_at,
            ended_at=a.ended_at,
            pap_count=pap_counts.get(a.id, 0),
        )
        for a in actions
    ]
    return {"items": items, "total": total}


# ── POST /actions ─────────────────────────────────────────────────────────────

@router.post("/actions", status_code=201, summary="创建舰队行动")
async def create_action(
    body: CreateActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fleet-action.manage")),
):
    """
    创建行动，仅在 Helm 内流转数据，不请求 ESI。
    fc_character_id 必须属于当前登录用户。
    """
    char = await _verify_character_ownership(body.fc_character_id, current_user, db)

    action = FleetAction(
        name=body.name,
        description=body.description,
        fleet_id=None,
        fc_character_id=body.fc_character_id,
        fc_character_name=char.character_name,
        status=ActionStatus.active,
        created_at=datetime.now(UTC),
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)

    return ActionResponse(
        id=action.id,
        name=action.name,
        description=action.description,
        fleet_id=action.fleet_id,
        fc_character_id=action.fc_character_id,
        fc_character_name=action.fc_character_name,
        status=action.status,
        created_at=action.created_at,
        ended_at=action.ended_at,
        pap_count=0,
    )


# ── GET /actions/{action_id} ──────────────────────────────────────────────────

@router.get("/actions/{action_id}", summary="查看行动详情")
async def get_action(
    action_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("fleet-action.read")),
):
    result = await db.execute(select(FleetAction).where(FleetAction.id == action_id))
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="行动不存在")

    pap_result = await db.execute(
        select(PapRecord)
        .where(PapRecord.action_id == action_id)
        .order_by(PapRecord.issued_at.desc())
    )
    paps = pap_result.scalars().all()

    return ActionDetailResponse(
        id=action.id,
        name=action.name,
        description=action.description,
        fleet_id=action.fleet_id,
        fc_character_id=action.fc_character_id,
        fc_character_name=action.fc_character_name,
        status=action.status,
        created_at=action.created_at,
        ended_at=action.ended_at,
        pap_count=len(paps),
        pap_records=[
            PapRecordResponse(
                id=p.id,
                character_id=p.character_id,
                character_name=p.character_name,
                issued_at=p.issued_at,
                issued_by_character_id=p.issued_by_character_id,
            )
            for p in paps
        ],
    )


# ── POST /actions/{action_id} ─────────────────────────────────────────────────
# UIAction row_key 将行 ID 拼接到 endpoint 末尾，因此"结束行动"使用此路由

@router.post("/actions/{action_id}", summary="结束行动")
async def end_action(
    action_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("fleet-action.manage")),
):
    action = await _get_active_action(action_id, db)
    if action.status == ActionStatus.ended:
        raise HTTPException(status_code=400, detail="行动已经结束")
    action.status = ActionStatus.ended
    action.ended_at = datetime.now(UTC)
    await db.commit()
    return {"id": action.id, "status": action.status, "ended_at": action.ended_at}


# ── DELETE /actions/{action_id} ───────────────────────────────────────────────

@router.delete("/actions/{action_id}", status_code=204, summary="删除行动")
async def delete_action(
    action_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("fleet-action.manage")),
):
    action = await _get_active_action(action_id, db)
    await db.delete(action)
    await db.commit()


# ── GET /actions/{action_id}/members ─────────────────────────────────────────

@router.get("/actions/{action_id}/members", summary="查询当前舰队成员")
async def get_fleet_members(
    action_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("fleet-action.manage")),
):
    """通过 ESI 实时获取该行动关联舰队的当前成员列表。"""
    action = await _get_active_action(action_id, db)
    if action.status == ActionStatus.ended:
        raise HTTPException(status_code=400, detail="行动已结束，无法查询实时舰队成员")

    token, refresh_tok = await fleet_esi.get_valid_token(action.fc_character_id, db)

    fleet_data = await fleet_esi.get_character_fleet(action.fc_character_id, token, refresh_tok)
    fleet_id = fleet_data.get("fleet_id")
    if not fleet_id:
        raise HTTPException(
            status_code=400,
            detail="FC 当前不在任何舰队中，请先由 FC 创建一个舰队后再尝试"
        )

    members = await fleet_esi.get_fleet_members(fleet_id, token, refresh_tok, action.fc_character_id)

    char_ids = [m.get("character_id") for m in members if m.get("character_id")]
    name_map = await resolve_entity_names(char_ids)

    registered_ids: set[int] = set()
    if char_ids:
        reg_result = await db.execute(
            select(Character.character_id).where(Character.character_id.in_(char_ids))
        )
        registered_ids = {r[0] for r in reg_result.all()}

    for m in members:
        cid = m.get("character_id")
        m["character_name"] = name_map.get(cid, {}).get("name") if cid else None
        m["is_registered"] = cid in registered_ids if cid else False

    return members


# ── POST /actions/{action_id}/pap ─────────────────────────────────────────────

@router.post("/actions/{action_id}/pap", summary="发放 PAP 出勤记录")
async def issue_pap(
    action_id: int,
    body: IssuePapRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fleet-action.pap")),
):
    """
    向当前舰队所有成员手动发放 PAP。
    1. 通过 FC 的 ESI token 获取实时舰队成员列表
    2. 批量写入 PapRecord（跳过重复角色，保证幂等）
    3. 可选：更新舰队 MOTD 通知（失败不影响 PAP 记录）
    """
    if body.action_id != action_id:
        raise HTTPException(status_code=400, detail="请求体中的 action_id 与路径参数不一致")

    action = await _get_active_action(action_id, db)
    if action.status == ActionStatus.ended:
        raise HTTPException(status_code=400, detail="行动已结束，无法继续发放 PAP")

    await _verify_character_ownership(body.fc_character_id, current_user, db)
    token, refresh_tok = await fleet_esi.get_valid_token(body.fc_character_id, db)

    fleet_id = action.fleet_id
    if fleet_id is None:
        fleet_data = await fleet_esi.get_character_fleet(body.fc_character_id, token, refresh_tok)
        fleet_id = fleet_data.get("fleet_id")
        if not fleet_id:
            raise HTTPException(status_code=400, detail="该行动未关联舰队，且 FC 当前不在任何舰队中，无法发放 PAP")
        action.fleet_id = fleet_id

    members = await fleet_esi.get_fleet_members(
        fleet_id, token, refresh_tok, body.fc_character_id
    )

    # 解析成员角色名
    char_ids = [m.get("character_id") for m in members if m.get("character_id")]
    name_map = await resolve_entity_names(char_ids)
    for m in members:
        cid = m.get("character_id")
        m["character_name"] = name_map.get(cid, {}).get("name") if cid else None

    # 查询当前行动中每个角色已有的 PAP 数量
    existing_result = await db.execute(
        select(PapRecord.character_id, func.count().label("cnt"))
        .where(PapRecord.action_id == action_id)
        .group_by(PapRecord.character_id)
    )
    existing_counts: dict[int, int] = {row[0]: row[1] for row in existing_result.all()}

    issued_at = datetime.now(UTC)
    new_records: list[PapRecord] = []
    chars_to_overwrite: list[int] = []  # 已有 PAP 但数量与新设置不同

    for member in members:
        char_id = member.get("character_id")
        if not char_id:
            continue
        current_count = existing_counts.get(char_id, 0)
        if current_count == body.pap_count:
            continue  # 数量一致，跳过（幂等）
        if current_count > 0:
            chars_to_overwrite.append(char_id)  # 数量不同，先删后建
        char_name = name_map.get(char_id, {}).get("name")
        for _ in range(body.pap_count):
            new_records.append(
                PapRecord(
                    action_id=action_id,
                    character_id=char_id,
                    character_name=char_name or f"ID:{char_id}",
                    issued_at=issued_at,
                    issued_by_character_id=body.fc_character_id,
                )
            )

    if chars_to_overwrite:
        await db.execute(
            delete(PapRecord).where(
                PapRecord.action_id == action_id,
                PapRecord.character_id.in_(chars_to_overwrite),
            )
        )
    if new_records:
        db.add_all(new_records)
        await db.flush()

    motd_updated = False
    if body.update_motd:
        total_pap_result = await db.execute(
            select(func.count()).select_from(PapRecord).where(PapRecord.action_id == action_id)
        )
        total_pap = total_pap_result.scalar() or 0
        motd = _MOTD_TEMPLATE.format(
            action_name=action.name,
            action_id=action.id,
            fc_name=action.fc_character_name,
            total_pap_count=total_pap,
        )
        # 收集其他插件（如 SRP）注册的 MOTD 片段
        from app.plugins.registry import extension_registry
        for provider in extension_registry.get_all("srp.motd_fragment"):
            try:
                fragment = provider.get_motd_fragment(action.id)
                if fragment:
                    motd = motd + "\n" + fragment
            except Exception:
                pass
        try:
            await fleet_esi.put_fleet_motd(fleet_id, token, motd)
            motd_updated = True
        except Exception:
            # MOTD 更新失败不影响 PAP 记录入库
            pass

    new_member_count = len(new_records) // body.pap_count - len(chars_to_overwrite) if new_records else 0
    await db.commit()
    return IssuePapResponse(
        action_id=action_id,
        issued_count=len(new_records),
        new_member_count=new_member_count,
        overwritten_count=len(chars_to_overwrite),
        member_ids=list({r.character_id for r in new_records}),
        motd_updated=motd_updated,
    )


# ── GET /pap-stats/{character_id} ───────────────────────────────────────────────

@router.get("/pap-stats/{character_id}", summary="获取角色 PAP 统计")
async def get_character_pap_stats(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    """返回角色的完整 PAP 统计信息，包含出勤次数和明细记录。"""
    from fleet_action.models import FleetAction

    now = datetime.now(UTC)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(PapRecord)
        .where(PapRecord.character_id == character_id)
        .options(selectinload(PapRecord.action))
        .order_by(PapRecord.issued_at.desc())
    )
    records = result.scalars().all()

    total_count = len(records)
    this_month_count = sum(1 for r in records if r.issued_at and r.issued_at >= current_month_start)
    this_year_count = sum(1 for r in records if r.issued_at and r.issued_at >= current_year_start)

    pap_records = []
    for r in records:
        action = r.action
        pap_records.append(
            PapStatsItem(
                action_id=r.action_id,
                action_name=action.name if action else "未知行动",
                action_date=action.created_at if action else r.issued_at,
                fc_character_name=action.fc_character_name if action else "未知",
                fleet_id=action.fleet_id if action else None,
            )
        )

    return CharacterPapStatsResponse(
        character_id=character_id,
        total_count=total_count,
        this_month_count=this_month_count,
        this_year_count=this_year_count,
        records=pap_records,
    )
