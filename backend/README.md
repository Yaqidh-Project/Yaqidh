# Yaqidh API

AI-powered child safety monitoring backend.

## Stack
- **Framework**: FastAPI (async-first)
- **DB**: PostgreSQL + SQLAlchemy async + Alembic
- **Auth**: JWT (access/refresh) + RBAC
- **AI**: ONNX Runtime (fall_detection + violence_detection)
- **Realtime**: WebSockets

## Quick Start

```bash
# Copy env
cp .env.example .env

# Run migrations
DATABASE_URL=<your-db-url> python3 -m alembic upgrade head

# Start server
bash start.sh
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | — | Register user |
| POST | /auth/login | — | Get tokens |
| POST | /auth/refresh | — | Refresh tokens |
| GET | /users/me | any | My profile |
| GET/PATCH/DELETE | /users | Manager | User management |
| CRUD | /zones | assigned | Zone management |
| CRUD | /cameras | assigned | Camera management |
| CRUD | /incidents | assigned | Incident records |
| POST | /reports | Manager/Parent | Generate report |
| GET | /reports | Manager/Parent | List reports |
| POST | /inference/predict | any | Run ONNX inference |
| GET | /inference/status | any | Model load status |
| WS | /ws/notifications | JWT query param | Real-time alerts |

## RBAC

| Role | Reports | Zones/Cameras | Incidents | Users |
|------|---------|---------------|-----------|-------|
| Manager | ✅ Full | ✅ All | ✅ All | ✅ |
| Parent | ✅ Own | Assigned only | Assigned only | Me only |
| Teacher | ❌ 403 | Assigned only | Assigned only | Me only |

## Model Files

Place ONNX weight files in `models/`:
- `models/fall_detection.onnx`
- `models/violence_detection.onnx`

If absent, the server starts with stub predictions (confidence 0.5, no incident auto-creation).
