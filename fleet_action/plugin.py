from pathlib import Path

from app.plugins.base import HelmPlugin, PermissionDef, SidebarItem


class FleetActionPlugin(HelmPlugin):
    name = "fleet-action"
    version = "0.1.0"
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
