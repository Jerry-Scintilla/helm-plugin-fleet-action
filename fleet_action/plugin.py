from app.plugins.base import (
    HelmPlugin, PermissionDef, SidebarItem,
    UISchema, UIPage, UISection,
    UITable, UIColumn, UIAction, UIFilter,
    UIForm, UIFormField,
)


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
                route="/plugins/fleet-action/actions",
                icon="⚔️",
                order=150,
            )
        ]

    def get_dashboard_widgets(self) -> list:
        return []

    def get_ui_schema(self) -> UISchema:
        return UISchema(pages=[

            # ── 页面 1：行动列表 ───────────────────────────────────────────────
            UIPage(
                name="list",
                path="actions",
                title="舰队行动记录",
                sections=[
                    UISection(
                        type="table",
                        table=UITable(
                            endpoint="actions",
                            columns=[
                                UIColumn("id",               "ID",     type="number"),
                                UIColumn("name",             "行动名称"),
                                UIColumn("fc_character_name","舰队指挥官"),
                                UIColumn("pap_count",        "PAP 数", type="number", sortable=True),
                                UIColumn("status", "状态", type="badge", badge_map={
                                    "active": "#6abf69",
                                    "ended":  "#87867f",
                                }),
                                UIColumn("created_at", "创建时间", type="date"),
                            ],
                            page_actions=[
                                UIAction("新建行动",
                                         navigate_to="fleet-action-create",
                                         variant="primary"),
                            ],
                            row_actions=[
                                UIAction("结束",
                                         endpoint="actions",
                                         method="POST",
                                         row_key="id",
                                         variant="primary",
                                         confirm="确定结束此行动？结束后无法继续发放 PAP。"),
                                UIAction("删除",
                                         endpoint="actions",
                                         method="DELETE",
                                         row_key="id",
                                         variant="danger",
                                         confirm="确定删除此行动？此操作不可撤销。"),
                            ],
                            filters=[
                                UIFilter("status", "状态", type="select", options=[
                                    {"label": "进行中", "value": "active"},
                                    {"label": "已结束", "value": "ended"},
                                ]),
                                UIFilter("fc_character_name", "按指挥官搜索", type="text"),
                            ],
                            page_size=20,
                        ),
                    ),
                ],
            ),

            # ── 页面 2：新建行动 ───────────────────────────────────────────────
            UIPage(
                name="create",
                path="actions/create",
                title="新建舰队行动",
                sections=[
                    UISection(
                        type="form",
                        form=UIForm(
                            endpoint="actions",
                            method="POST",
                            fields=[
                                UIFormField("name", "行动名称", required=True,
                                            placeholder="如：Brave Newbies Roam"),
                                UIFormField("description", "行动描述", type="textarea",
                                            placeholder="可选描述"),
                                UIFormField("fc_character_id", "FC 角色 ID", type="number",
                                            required=True,
                                            placeholder="输入 FC 的 EVE 角色 ID"),
                            ],
                            submit_label="创建行动",
                            on_success_navigate="fleet-action-list",
                        ),
                    ),
                ],
            ),

        ])
