from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.plugins.base import (
    CharacterExtension,
    CharacterExtensionProvider,
    CharacterSubmodule,
    CharacterSubmoduleProvider,
    HelmPlugin,
    PermissionDef,
    PluginContext,
    SidebarItem,
)
from app.plugins.registry import extension_registry

from fleet_action.models import ActionStatus, FleetAction, PapRecord

try:
    from helm_mcp.protocols import MCPToolDef
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False

_MOTD_TEMPLATE = (
    "[PAP 行动通知] 行动「{action_name}」(ID:{action_id}) "
    "已由舰队指挥官 {fc_name} 手动发放出勤记录 (PAP)，"
    "当前累计出勤人数：{total_pap_count}。"
    "请确保您已加入舰队以获得本次出勤记录。"
)


class FleetActionPlugin(HelmPlugin, CharacterExtensionProvider, CharacterSubmoduleProvider):
    name = "fleet-action"
    version = "0.1.1"
    author = "Jerry_Scintilla"
    description = "EVE Online 舰队行动管理，支持手动发放 PAP 出勤记录"
    helm_sdk_version = ">=1.0,<2.0"

    def get_router(self):
        from fleet_action.routers import router
        return router

    def get_permissions(self) -> list[PermissionDef]:
        return [
            PermissionDef("fleet-action.read", "global", "查看舰队行动列表和 PAP 记录"),
            PermissionDef("fleet-action.manage", "global", "创建/结束舰队行动"),
            PermissionDef("fleet-action.pap", "global", "向当前舰队成员发放 PAP 并更新 MOTD"),
        ]

    def get_esi_scopes(self) -> list[str]:
        return [
            "esi-fleets.read_fleet.v1",
            "esi-fleets.write_fleet.v1",
        ]

    def get_sidebar_items(self) -> list[SidebarItem]:
        return [
            SidebarItem(
                label="舰队行动",
                route="/plugins/fleet-action",
                icon="⚔️",
                order=150,
            )
        ]

    def get_static_dir(self):
        return Path(__file__).parent / "frontend" / "dist"

    def get_frontend_dev_url(self):
        return None

    def on_enable(self, ctx: PluginContext) -> None:
        extension_registry.register("character.extension", self, self.name)
        if _MCP_AVAILABLE:
            extension_registry.register("mcp.tool_provider", self, self.name)

    async def get_character_extension(
        self, character_id: int, db: AsyncSession
    ) -> CharacterExtension | None:
        result = await db.execute(
            select(PapRecord)
            .where(PapRecord.character_id == character_id)
            .options(selectinload(PapRecord.action))
            .order_by(PapRecord.issued_at.desc())
        )
        records = result.scalars().all()

        if not records:
            return CharacterExtension(
                character_id=character_id,
                title="PAP 出勤记录",
                widget="stats",
                content=[
                    {"label": "总出勤次数", "value": 0},
                    {"label": "最近行动", "value": "暂无"},
                    {"label": "最近出勤", "value": "暂无"},
                ],
                order=10,
            )

        total_count = len(records)
        latest_record = records[0]
        last_action_name = latest_record.action.name if latest_record.action else "未知行动"
        last_issued_at = latest_record.issued_at.strftime("%Y-%m-%d %H:%M") if latest_record.issued_at else "暂无"

        return CharacterExtension(
            character_id=character_id,
            title="PAP 出勤记录",
            widget="stats",
            content=[
                {"label": "总出勤次数", "value": total_count},
                {"label": "最近行动", "value": last_action_name},
                {"label": "最近出勤", "value": last_issued_at},
            ],
            order=10,
        )

    def get_character_submodules(self) -> list[CharacterSubmodule]:
        return [
            CharacterSubmodule(
                slug="pap",
                label="PAP 出勤",
                iframe_url_template="/plugin-ui/fleet-action/pap?character_id={character_id}",
                icon="📋",
                order=50,
            )
        ]

    # ── MCP Tool Provider ─────────────────────────────────────────────────────

    def get_mcp_tools(self) -> list:
        if not _MCP_AVAILABLE:
            return []
        return [
            MCPToolDef(
                name="fleet_action_list_actions",
                description="列出舰队行动记录，可按状态（active/ended）和FC名称筛选，支持分页",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["active", "ended"],
                            "description": "按状态过滤：active=进行中，ended=已结束",
                        },
                        "fc_character_name": {
                            "type": "string",
                            "description": "按舰队指挥官角色名称模糊搜索",
                        },
                        "page": {"type": "integer", "default": 1, "minimum": 1},
                        "page_size": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
                    },
                },
                required_permission="fleet-action.read",
            ),
            MCPToolDef(
                name="fleet_action_get_action",
                description="获取指定舰队行动的详情，包含所有 PAP 出勤记录",
                input_schema={
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "integer", "description": "舰队行动 ID"},
                    },
                    "required": ["action_id"],
                },
                required_permission="fleet-action.read",
            ),
            MCPToolDef(
                name="fleet_action_get_pap_stats",
                description="获取指定 EVE 角色的 PAP 出勤统计，包含总次数、本月、本年及明细",
                input_schema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "integer", "description": "EVE 角色 ID"},
                    },
                    "required": ["character_id"],
                },
                required_permission="fleet-action.read",
            ),
            MCPToolDef(
                name="fleet_action_create_action",
                description="创建新舰队行动。fc_character_id 必须是当前用户绑定的角色。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "行动名称"},
                        "description": {"type": "string", "description": "行动描述（可选）"},
                        "fc_character_id": {
                            "type": "integer",
                            "description": "担任FC的角色ID，必须属于当前用户",
                        },
                    },
                    "required": ["name", "fc_character_id"],
                },
                required_permission="fleet-action.manage",
            ),
            MCPToolDef(
                name="fleet_action_end_action",
                description="结束一个进行中的舰队行动",
                input_schema={
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "integer", "description": "要结束的舰队行动 ID"},
                    },
                    "required": ["action_id"],
                },
                required_permission="fleet-action.manage",
            ),
            MCPToolDef(
                name="fleet_action_issue_pap",
                description=(
                    "向当前舰队所有成员发放 PAP 出勤记录。"
                    "FC 必须处于一个舰队中，系统通过 ESI 实时读取舰队成员列表。"
                    "支持幂等：相同成员相同次数不会重复写入。"
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "integer", "description": "行动 ID"},
                        "fc_character_id": {
                            "type": "integer",
                            "description": "FC 的 EVE 角色 ID，必须属于当前用户",
                        },
                        "pap_count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 1,
                            "description": "每人发放 PAP 次数",
                        },
                        "update_motd": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否同步更新舰队 MOTD 通知",
                        },
                    },
                    "required": ["action_id", "fc_character_id"],
                },
                required_permission="fleet-action.pap",
            ),
        ]

    async def call_mcp_tool(self, name: str, args: dict, user, db: AsyncSession) -> dict:
        if name == "fleet_action_list_actions":
            return await self._mcp_list_actions(args, db)
        if name == "fleet_action_get_action":
            return await self._mcp_get_action(args, db)
        if name == "fleet_action_get_pap_stats":
            return await self._mcp_get_pap_stats(args, db)
        if name == "fleet_action_create_action":
            return await self._mcp_create_action(args, user, db)
        if name == "fleet_action_end_action":
            return await self._mcp_end_action(args, db)
        if name == "fleet_action_issue_pap":
            return await self._mcp_issue_pap(args, user, db)
        raise ValueError(f"Unknown tool: {name}")

    async def _mcp_verify_char(self, fc_character_id: int, user, db: AsyncSession):
        from app.models.character import Character
        result = await db.execute(
            select(Character).where(
                Character.character_id == fc_character_id,
                Character.user_id == user.id,
            )
        )
        char = result.scalar_one_or_none()
        if char is None:
            raise ValueError("该角色不属于您的账号，无法代为操作")
        return char

    async def _mcp_list_actions(self, args: dict, db: AsyncSession) -> dict:
        status = args.get("status")
        fc_character_name = args.get("fc_character_name")
        page = int(args.get("page", 1))
        page_size = int(args.get("page_size", 20))

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

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "fleet_id": a.fleet_id,
                    "fc_character_id": a.fc_character_id,
                    "fc_character_name": a.fc_character_name,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "ended_at": a.ended_at.isoformat() if a.ended_at else None,
                    "pap_count": pap_counts.get(a.id, 0),
                }
                for a in actions
            ],
        }

    async def _mcp_get_action(self, args: dict, db: AsyncSession) -> dict:
        action_id = int(args["action_id"])
        result = await db.execute(select(FleetAction).where(FleetAction.id == action_id))
        action = result.scalar_one_or_none()
        if action is None:
            raise ValueError(f"行动 {action_id} 不存在")

        pap_result = await db.execute(
            select(PapRecord)
            .where(PapRecord.action_id == action_id)
            .order_by(PapRecord.issued_at.desc())
        )
        paps = pap_result.scalars().all()

        return {
            "id": action.id,
            "name": action.name,
            "description": action.description,
            "fleet_id": action.fleet_id,
            "fc_character_id": action.fc_character_id,
            "fc_character_name": action.fc_character_name,
            "status": action.status.value,
            "created_at": action.created_at.isoformat() if action.created_at else None,
            "ended_at": action.ended_at.isoformat() if action.ended_at else None,
            "pap_count": len(paps),
            "pap_records": [
                {
                    "id": p.id,
                    "character_id": p.character_id,
                    "character_name": p.character_name,
                    "issued_at": p.issued_at.isoformat() if p.issued_at else None,
                    "issued_by_character_id": p.issued_by_character_id,
                }
                for p in paps
            ],
        }

    async def _mcp_get_pap_stats(self, args: dict, db: AsyncSession) -> dict:
        character_id = int(args["character_id"])
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

        return {
            "character_id": character_id,
            "total_count": total_count,
            "this_month_count": this_month_count,
            "this_year_count": this_year_count,
            "records": [
                {
                    "action_id": r.action_id,
                    "action_name": r.action.name if r.action else "未知行动",
                    "action_date": (
                        r.action.created_at.isoformat()
                        if r.action and r.action.created_at
                        else (r.issued_at.isoformat() if r.issued_at else None)
                    ),
                    "fc_character_name": r.action.fc_character_name if r.action else "未知",
                    "fleet_id": r.action.fleet_id if r.action else None,
                }
                for r in records
            ],
        }

    async def _mcp_create_action(self, args: dict, user, db: AsyncSession) -> dict:
        name = args["name"]
        description = args.get("description", "")
        fc_character_id = int(args["fc_character_id"])

        char = await self._mcp_verify_char(fc_character_id, user, db)

        action = FleetAction(
            name=name,
            description=description,
            fleet_id=None,
            fc_character_id=fc_character_id,
            fc_character_name=char.character_name,
            status=ActionStatus.active,
            created_at=datetime.now(UTC),
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)

        return {
            "id": action.id,
            "name": action.name,
            "description": action.description,
            "fc_character_id": action.fc_character_id,
            "fc_character_name": action.fc_character_name,
            "status": action.status.value,
            "created_at": action.created_at.isoformat() if action.created_at else None,
        }

    async def _mcp_end_action(self, args: dict, db: AsyncSession) -> dict:
        action_id = int(args["action_id"])
        result = await db.execute(select(FleetAction).where(FleetAction.id == action_id))
        action = result.scalar_one_or_none()
        if action is None:
            raise ValueError(f"行动 {action_id} 不存在")
        if action.status == ActionStatus.ended:
            raise ValueError("行动已经结束")
        action.status = ActionStatus.ended
        action.ended_at = datetime.now(UTC)
        await db.commit()
        return {
            "id": action.id,
            "status": action.status.value,
            "ended_at": action.ended_at.isoformat() if action.ended_at else None,
        }

    async def _mcp_issue_pap(self, args: dict, user, db: AsyncSession) -> dict:
        from app.services.esi_names import resolve_entity_names
        from fleet_action import esi as fleet_esi

        action_id = int(args["action_id"])
        fc_character_id = int(args["fc_character_id"])
        pap_count = int(args.get("pap_count", 1))
        update_motd = bool(args.get("update_motd", False))

        result = await db.execute(select(FleetAction).where(FleetAction.id == action_id))
        action = result.scalar_one_or_none()
        if action is None:
            raise ValueError(f"行动 {action_id} 不存在")
        if action.status == ActionStatus.ended:
            raise ValueError("行动已结束，无法继续发放 PAP")

        await self._mcp_verify_char(fc_character_id, user, db)
        token, refresh_tok = await fleet_esi.get_valid_token(fc_character_id, db)

        fleet_id = action.fleet_id
        if fleet_id is None:
            fleet_data = await fleet_esi.get_character_fleet(fc_character_id, token, refresh_tok)
            fleet_id = fleet_data.get("fleet_id")
            if not fleet_id:
                raise ValueError("该行动未关联舰队，且 FC 当前不在任何舰队中，无法发放 PAP")
            action.fleet_id = fleet_id

        members = await fleet_esi.get_fleet_members(fleet_id, token, refresh_tok, fc_character_id)

        char_ids = [m.get("character_id") for m in members if m.get("character_id")]
        name_map = await resolve_entity_names(char_ids)
        for m in members:
            cid = m.get("character_id")
            m["character_name"] = name_map.get(cid, {}).get("name") if cid else None

        existing_result = await db.execute(
            select(PapRecord.character_id, func.count().label("cnt"))
            .where(PapRecord.action_id == action_id)
            .group_by(PapRecord.character_id)
        )
        existing_counts: dict[int, int] = {row[0]: row[1] for row in existing_result.all()}

        issued_at = datetime.now(UTC)
        new_records: list[PapRecord] = []
        chars_to_overwrite: list[int] = []

        for member in members:
            char_id = member.get("character_id")
            if not char_id:
                continue
            current_count = existing_counts.get(char_id, 0)
            if current_count == pap_count:
                continue
            if current_count > 0:
                chars_to_overwrite.append(char_id)
            char_name = name_map.get(char_id, {}).get("name")
            for _ in range(pap_count):
                new_records.append(
                    PapRecord(
                        action_id=action_id,
                        character_id=char_id,
                        character_name=char_name or f"ID:{char_id}",
                        issued_at=issued_at,
                        issued_by_character_id=fc_character_id,
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
        if update_motd:
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
                pass

        new_member_count = len(new_records) // pap_count - len(chars_to_overwrite) if new_records else 0
        await db.commit()
        return {
            "action_id": action_id,
            "issued_count": len(new_records),
            "new_member_count": new_member_count,
            "overwritten_count": len(chars_to_overwrite),
            "member_ids": list({r.character_id for r in new_records}),
            "motd_updated": motd_updated,
        }
