from pathlib import Path

from sqlalchemy import select
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

from fleet_action.models import PapRecord


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
