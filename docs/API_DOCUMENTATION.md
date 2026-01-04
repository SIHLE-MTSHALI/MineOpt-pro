# MineOpt Pro Enterprise - API Documentation

## Overview

MineOpt Pro is a coal mine production optimization system that provides:
- Schedule optimization using Linear Programming
- Material flow and blending
- Quality management and simulation
- Multi-user collaboration
- Integration with external systems

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints (except `/auth/token` and `/auth/register`) require Bearer token authentication.

### Login
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

Response:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "session_id": "uuid"
}
```

### Using the Token
```http
Authorization: Bearer {access_token}
```

---

## Core Endpoints

### Sites & Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sites` | List all sites |
| GET | `/sites/{site_id}` | Get site details |
| POST | `/sites` | Create new site |
| GET | `/config/{site_id}` | Get site configuration |

### Scheduling

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/schedules/site/{site_id}` | List schedules for site |
| POST | `/schedules` | Create new schedule |
| GET | `/schedules/{id}` | Get schedule details |
| POST | `/schedules/{id}/run` | Run optimization pass |
| PUT | `/schedules/{id}/publish` | Publish draft schedule |
| GET | `/schedules/{id}/tasks` | Get scheduled tasks |

#### Schedule Run Types
- `fast` - Quick pass (~3 seconds)
- `full` - Complete optimization (~60 seconds)

### Flow Network

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/flow/networks/site/{site_id}` | List flow networks |
| POST | `/flow/networks` | Create network |
| GET | `/flow/networks/{id}/nodes` | Get network nodes |
| POST | `/flow/networks/{id}/nodes` | Add node |
| POST | `/flow/edges` | Connect nodes |
| POST | `/flow/simulate` | Run flow simulation |

### Stockpiles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stockpiles/{id}` | Get stockpile state |
| POST | `/stockpiles/{id}/deposit` | Deposit material |
| POST | `/stockpiles/{id}/reclaim` | Reclaim material |
| GET | `/stockpiles/{id}/balance-history` | Get balance history |

### Quality Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/quality/fields/site/{site_id}` | Get quality fields |
| POST | `/quality/blend` | Calculate blended quality |
| POST | `/quality/check-constraints` | Check spec compliance |
| POST | `/quality/simulate` | Monte Carlo simulation |

#### Quality Simulation Request
```json
{
  "sources": [
    {
      "parcel_id": "p1",
      "quantity_tonnes": 1000,
      "quality_vector": {"CV": 22.0, "Ash": 15.0}
    }
  ],
  "specs": [
    {"field_name": "Ash", "max_value": 16.0}
  ],
  "n_simulations": 1000,
  "include_wash_plant": false
}
```

### Wash Plants

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/wash-plants/tables/site/{site_id}` | List wash tables |
| POST | `/wash-plants/{id}/process` | Process through plant |
| POST | `/wash-plants/{id}/process-multi-stage` | Multi-stage wash |
| POST | `/wash-plants/{id}/optimize-schedule-cutpoints` | Optimize cutpoints |

### Reports & Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/schedule/{id}/pdf` | Export PDF report |
| GET | `/reports/schedule/{id}/bi` | Export BI data |

### Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/integration/fleet-actuals` | Import fleet data |
| POST | `/integration/survey-data` | Import survey data |
| GET | `/integration/connectors` | List connectors |
| POST | `/integration/webhooks` | Register webhook |

---

## Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/token` | Login |
| POST | `/auth/token/refresh` | Refresh token |
| POST | `/auth/logout` | Logout current session |
| POST | `/auth/logout/all` | Force logout all |
| GET | `/auth/sessions` | View active sessions |
| DELETE | `/auth/sessions/{id}` | Invalidate session |
| GET | `/auth/audit` | View audit log (admin) |

---

## WebSocket Endpoints

### Real-time Collaboration
```
ws://localhost:8000/ws/connect?site_id={site_id}&user_id={user_id}
```

Messages:
- `presence_update` - User joins/leaves
- `entity_changed` - Entity modified
- `editing_lock` - Lock acquired/released

---

## Error Responses

```json
{
  "detail": "Error message"
}
```

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Error |

---

## Rate Limits

- 100 requests per minute per user
- WebSocket: 10 connections per user

---

## Changelog

### v1.0.0 (2026-01-04)
- Initial release with all 13 work packages
- LP Solver, Scheduling, 3D View
- Flow Network, Gantt Chart
- Multi-User Collaboration
- PDF Reports, Integrations
- Quality Simulation (Monte Carlo)
- Wash Plant Enhancements
- Security & Session Management
