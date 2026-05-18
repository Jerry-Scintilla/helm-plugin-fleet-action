from datetime import datetime

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class CreateActionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=2048)
    fc_character_id: int = Field(..., description="FC 的角色 ID，必须属于当前登录用户")


class IssuePapRequest(BaseModel):
    action_id: int
    fc_character_id: int = Field(..., description="FC 角色 ID，用于获取舰队成员及 ESI token")
    update_motd: bool = Field(default=True, description="发放 PAP 后是否更新舰队 MOTD")
    pap_count: int = Field(default=1, ge=1, le=10, description="每人发放 PAP 数量（1-10）")


# ── Response schemas ──────────────────────────────────────────────────────────

class PapRecordResponse(BaseModel):
    id: int
    character_id: int
    character_name: str
    issued_at: datetime
    issued_by_character_id: int

    model_config = {"from_attributes": True}


class ActionResponse(BaseModel):
    id: int
    name: str
    description: str
    fleet_id: int | None
    fc_character_id: int
    fc_character_name: str
    status: str
    created_at: datetime
    ended_at: datetime | None
    pap_count: int = 0

    model_config = {"from_attributes": True}


class ActionDetailResponse(ActionResponse):
    pap_records: list[PapRecordResponse] = []


class IssuePapResponse(BaseModel):
    action_id: int
    issued_count: int       # 本次新建的记录总条数（新成员 + 覆盖成员）
    new_member_count: int   # 首次获得 PAP 的成员数
    overwritten_count: int  # PAP 数量被调整的成员数
    member_ids: list[int]
    motd_updated: bool


class PapStatsItem(BaseModel):
    action_id: int
    action_name: str
    action_date: datetime
    fc_character_name: str
    fleet_id: int | None


class CharacterPapStatsResponse(BaseModel):
    character_id: int
    total_count: int
    this_month_count: int
    this_year_count: int
    records: list[PapStatsItem]
