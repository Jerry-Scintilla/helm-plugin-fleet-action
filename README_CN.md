# helm-plugin-fleet-action

EVE Online 舰队行动管理插件，为 [Helm](https://github.com/join-Helm/Helm) 提供舰队行动追踪和 PAP（出勤记录）管理功能。

## 功能特性

- **舰队行动管理**：创建、查看和结束舰队行动
- **PAP 发放**：通过 EVE ESI 实时获取舰队成员，向当前舰队成员手动发放 PAP 出勤记录
- **出勤统计**：查看角色 PAP 统计（总计、本月、本年）
- **ESI 集成**：通过 EVE ESI API 实时获取舰队信息和成员列表
- **角色扩展**：在角色资料页显示 PAP 出勤统计 widget
- **MOTD 通知**：发放 PAP 后自动更新舰队 MOTD

## 环境要求

- Python >= 3.12
- Helm >= 1.0

## 安装

```bash
# 开发模式安装
make dev-install

# 或通过 wheel 安装
pip install dist/helm-plugin-fleet-action-*.whl
```

## 开发

```bash
# 构建前端
cd fleet_action/frontend && npm install && npm run build

# 构建 Python wheel
make python

# 清理构建产物
make clean
```

## 插件结构

```
fleet_action/
├── plugin.py          # 插件入口
├── routers.py         # API 路由
├── models.py          # 数据模型 (FleetAction, PapRecord)
├── schemas.py         # Pydantic 请求/响应模型
├── esi.py             # EVE ESI API 辅助函数
├── frontend/          # Vue.js 前端
│   └── src/views/
│       ├── ActionsListView.vue     # 行动列表
│       ├── ActionDetailView.vue    # 行动详情与成员管理
│       ├── CreateActionView.vue    # 创建行动
│       └── CharacterPapView.vue    # 角色 PAP 统计
└── migrations/        # Alembic 数据库迁移
```

## API 接口

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/characters` | - | 获取用户绑定的 EVE 角色列表 |
| GET | `/fleet/info` | fleet-action.manage | 获取 FC 当前所在舰队 |
| GET | `/actions` | fleet-action.read | 列出所有舰队行动 |
| POST | `/actions` | fleet-action.manage | 创建新舰队行动 |
| GET | `/actions/{id}` | fleet-action.read | 查看行动详情 |
| POST | `/actions/{id}` | fleet-action.manage | 结束行动 |
| DELETE | `/actions/{id}` | fleet-action.manage | 删除行动 |
| GET | `/actions/{id}/members` | fleet-action.manage | 通过 ESI 获取舰队成员 |
| POST | `/actions/{id}/pap` | fleet-action.pap | 向舰队成员发放 PAP |
| GET | `/pap-stats/{character_id}` | - | 获取角色 PAP 统计 |

## 需要的 ESI 权限范围

- `esi-fleets.read_fleet.v1` - 读取舰队信息和成员
- `esi-fleets.write_fleet.v1` - 更新舰队 MOTD

## 权限说明

| 权限 | 范围 | 说明 |
|------|------|------|
| fleet-action.read | global | 查看行动列表和 PAP 记录 |
| fleet-action.manage | global | 创建/结束/删除行动 |
| fleet-action.pap | global | 发放 PAP 并更新 MOTD |

## 状态

**Alpha** - 插件处于积极开发状态，暂不提供正式 Release。

## 欢迎参与开发

欢迎开发者加入开发！您可以 Fork 本仓库并进一步拓展功能。