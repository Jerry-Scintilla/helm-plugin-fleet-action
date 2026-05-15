# helm-plugin-fleet-action

A [Helm](https://github.com/join-Helm/Helm) plugin for EVE Online fleet management, providing fleet action tracking and PAP (Participation Attendance Record) management.

## Features

- **Fleet Action Management**: Create, view, and close fleet actions
- **PAP Issuance**: Manually issue PAP records to all current fleet members via EVE ESI
- **Fleet Member Stats**: View character PAP statistics (total, monthly, yearly)
- **ESI Integration**: Real-time fleet info and member list via EVE ESI API
- **Character Extension**: PAP stats displayed in character profile widget
- **MOTD Notification**: Auto-update fleet MOTD when issuing PAP

## Requirements

- Python >= 3.12
- Helm >= 1.0

## Installation

```bash
# Development installation
make dev-install

# Or install from wheel
pip install dist/helm-plugin-fleet-action-*.whl
```

## Development

```bash
# Build frontend
cd fleet_action/frontend && npm install && npm run build

# Build Python wheel
make python

# Clean build artifacts
make clean
```

## Plugin Structure

```
fleet_action/
├── plugin.py          # Plugin entry point
├── routers.py         # API endpoints
├── models.py          # Database models (FleetAction, PapRecord)
├── schemas.py         # Pydantic request/response schemas
├── esi.py             # EVE ESI API helpers
├── frontend/          # Vue.js frontend
│   └── src/views/
│       ├── ActionsListView.vue     # Fleet action list
│       ├── ActionDetailView.vue    # Action detail + member management
│       ├── CreateActionView.vue     # Create new action
│       └── CharacterPapView.vue    # Character PAP stats
└── migrations/        # Alembic database migrations
```

## API Endpoints

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/characters` | - | List user's EVE characters |
| GET | `/fleet/info` | fleet-action.manage | Get FC's current fleet |
| GET | `/actions` | fleet-action.read | List all fleet actions |
| POST | `/actions` | fleet-action.manage | Create new fleet action |
| GET | `/actions/{id}` | fleet-action.read | Get action detail |
| POST | `/actions/{id}` | fleet-action.manage | End fleet action |
| DELETE | `/actions/{id}` | fleet-action.manage | Delete fleet action |
| GET | `/actions/{id}/members` | fleet-action.manage | Get fleet members via ESI |
| POST | `/actions/{id}/pap` | fleet-action.pap | Issue PAP to fleet members |
| GET | `/pap-stats/{character_id}` | - | Get character PAP statistics |

## ESI Scopes Required

- `esi-fleets.read_fleet.v1` - Read fleet info and members
- `esi-fleets.write_fleet.v1` - Update fleet MOTD

## Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| fleet-action.read | global | View fleet actions and PAP records |
| fleet-action.manage | global | Create/end/delete fleet actions |
| fleet-action.pap | global | Issue PAP and update MOTD |

## Status

**Alpha** - This plugin is under active development. No official releases yet.

## Contributing

Contributions are welcome! Feel free to fork the repository and extend the functionality.

## License

MIT License