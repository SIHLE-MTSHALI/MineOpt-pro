# MineOpt Pro

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)

**Coal mine production scheduling and optimization system**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API Reference](#api-reference) • [Contributing](#contributing)

</div>

---

## Overview

MineOpt Pro is a comprehensive production scheduling system designed for open-cast coal mining operations. It combines advanced optimization algorithms with an intuitive user interface to help mining engineers create optimal short-term production schedules that meet quality targets, equipment constraints, and production goals.

### Key Capabilities

- **Multi-period scheduling** with 12-hour shift granularity
- **Quality blending optimization** to meet product specifications
- **Material flow network** modeling from pit to product
- **Wash plant integration** with cutpoint optimization
- **Real-time stockpile tracking** with FIFO/LIFO reclaim strategies
- **Equipment assignment** and utilization optimization
- **Comprehensive reporting** with export capabilities

---

## Features

### 🗓️ Scheduling Engine

| Feature | Description |
|---------|-------------|
| **Fast Pass** | Greedy algorithm for quick feasible schedules (~3 seconds) |
| **Full Pass** | Iterative optimization with constraint relaxation |
| **8-Stage Pipeline** | Validation → Candidates → Resources → Flow → Quality → Constraints → Finalize → Persist |
| **Variable Production Control** | Per-period rate factors and manual overrides |

### ⚗️ Quality Management

- **Blending optimization** across multiple sources
- **Spec compliance checking** with Min/Max/Range constraints
- **Penalty curve evaluation** (Linear, Quadratic, Step, Exponential)
- **Basis conversion** (ARB, ADB, DAF)
- **Quality field tracking**: CV, Ash, Moisture, Sulphur, VM, HGI

### 📦 Stockpile Management

| Type | Features |
|------|----------|
| **Simple Stockpile** | Capacity tracking, FIFO/LIFO/Proportional reclaim |
| **Staged Stockpile** | Multi-pile state machine (Receiving → Resting → Available → Depleted) |
| **Parcel Tracking** | Individual tonnes with quality preservation |

### 🏭 Wash Plant Integration

- **Wash table interpolation** for RD cutpoint selection
- **Cutpoint optimization modes**: Fixed, Target Quality, Optimizer
- **Product/Discard yield calculation**
- **Operating point tracking** per schedule period

### 🔒 Security & Audit

- **Role-Based Access Control** with 6 predefined roles
- **18 granular permissions** (view, edit, execute, admin)
- **Complete audit trail** for all entity changes
- **Schedule immutability** after publishing
- **Version forking** for change management

### 📊 Reporting

9 standard report types:
1. Daily Plan Summary
2. Shift Plan
3. Equipment Utilisation
4. Production by Material
5. Haulage Routes
6. Stockpile Balances
7. Plant Performance
8. Quality Compliance
9. Planned vs Actual

---

## Technology Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **FastAPI** | REST API framework |
| **SQLAlchemy 2.0** | ORM with async support |
| **SQLite/PostgreSQL** | Database |
| **Pydantic v2** | Data validation |
| **Uvicorn** | ASGI server |

### Frontend

| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool |
| **React Three Fiber** | 3D visualization |
| **Lucide React** | Icons |
| **Tailwind CSS** | Styling |

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/SIHLE-MTSHALI/MineOpt-pro.git
cd MineOpt-pro

# Create virtual environment
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

---

## Quick Start

### 1. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

The UI will be available at `http://localhost:5173`

### 3. Access the API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ 3D View │ │  Gantt  │ │ Reports │ │  Flow   │            │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘            │
└───────┼──────────┼──────────┼──────────┼────────────────────┘
        │          │          │          │
        └──────────┴──────────┴──────────┘
                         │
                    REST API
                         │
┌────────────────────────┼────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Routers                           │    │
│  │  config │ calendar │ schedule │ optimization │ ...   │    │
│  └───────────────────────┬─────────────────────────────┘    │
│  ┌───────────────────────┴─────────────────────────────┐    │
│  │                   Services                           │    │
│  │  ScheduleEngine │ BlendingService │ StockpileService │    │
│  └───────────────────────┬─────────────────────────────┘    │
│  ┌───────────────────────┴─────────────────────────────┐    │
│  │                 Domain Models                        │    │
│  │  Site │ Calendar │ Resource │ FlowNetwork │ Schedule │    │
│  └───────────────────────┬─────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │  Database   │
                    │  (SQLite)   │
                    └─────────────┘
```

### Project Structure

```
MineOpt-pro/
├── backend/
│   ├── app/
│   │   ├── domain/           # SQLAlchemy models
│   │   │   ├── models_core.py
│   │   │   ├── models_calendar.py
│   │   │   ├── models_resource.py
│   │   │   ├── models_flow.py
│   │   │   ├── models_scheduling.py
│   │   │   └── ...
│   │   ├── routers/          # FastAPI endpoints
│   │   │   ├── config_router.py
│   │   │   ├── schedule_router.py
│   │   │   ├── optimization_router.py
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── schedule_engine.py
│   │   │   ├── blending_service.py
│   │   │   ├── stockpile_service.py
│   │   │   └── ...
│   │   ├── database.py
│   │   └── main.py
│   ├── tests/                # pytest test suite
│   │   ├── test_domain_models.py
│   │   ├── test_services.py
│   │   ├── test_api_endpoints.py
│   │   └── test_integration.py
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── spatial/      # 3D visualization
│   │   │   ├── scheduler/    # Gantt and scheduling
│   │   │   ├── flow/         # Flow network editor
│   │   │   ├── reporting/    # Dashboard and reports
│   │   │   └── ui/           # Common UI components
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/config/sites` | List all sites |
| `GET` | `/calendar/calendars` | List calendars |
| `GET` | `/schedule/versions` | List schedule versions |
| `POST` | `/optimization/fast-pass` | Run fast optimization |
| `POST` | `/optimization/full-pass` | Run full optimization |

### Quality Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/quality/fields` | Get quality field definitions |
| `POST` | `/quality/calculate-blend` | Calculate blended quality |
| `POST` | `/quality/check-compliance` | Check spec compliance |

### Integration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/integration/fleet/actual-tonnes` | Import FMS actuals |
| `POST` | `/integration/survey/geometry` | Update geometry |
| `POST` | `/integration/publish` | Publish schedule |
| `GET` | `/integration/dispatch-targets/{id}` | Get dispatch targets |

### Security Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/security/roles` | List available roles |
| `GET` | `/security/permissions` | List permissions |
| `GET` | `/security/audit/logs` | Query audit logs |
| `POST` | `/security/schedule/fork` | Fork schedule version |

---

## Domain Model

### Core Entities

```
Site ──────┬──── Calendar ──── Period
           │
           ├──── Resource ──── ResourcePeriodParameters
           │
           ├──── ActivityArea ──── Slice
           │
           └──── FlowNetwork ──┬── FlowNode ──── StockpileConfig
                               │
                               └── FlowArc ──── ArcQualityObjective

ScheduleVersion ──── Task ──── FlowResult
                          │
                          └── InventoryBalance
```

### Quality Fields

| Field | Unit | Typical Range | Basis |
|-------|------|---------------|-------|
| CV | MJ/kg | 18-28 | ARB |
| Ash | % | 8-25 | ADB |
| Moisture | % | 4-15 | AR |
| Sulphur | % | 0.3-2.0 | ADB |
| VM | % | 20-35 | ADB |
| HGI | - | 40-80 | - |

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./mineopt.db

# Server
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Security
SECRET_KEY=your-secret-key-here
```

### Role Permissions

| Role | Permissions |
|------|-------------|
| `viewer` | view:schedule, view:resources, view:reports |
| `planner` | viewer + edit:schedule, run:optimization |
| `senior_planner` | planner + publish:schedule, edit:resources |
| `supervisor` | view + publish + audit |
| `admin` | all except manage:sites |
| `super_admin` | all permissions |

---

## Testing

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/test_services.py -v

# Integration tests
pytest -m integration

# With coverage
pytest --cov=app --cov-report=html
```

### Test Categories

| File | Coverage |
|------|----------|
| `test_domain_models.py` | Site, Calendar, Resource, Flow, Schedule |
| `test_services.py` | Quality, Blending, Stockpile, Audit, Security |
| `test_api_endpoints.py` | All REST endpoints |
| `test_integration.py` | E2E workflows, scenarios |

---

## Development

### Code Style

- Python: Black formatter, isort imports
- JavaScript: ESLint with React rules
- Commits: Conventional Commits format

### Adding a New Router

1. Create router file in `backend/app/routers/`
2. Define endpoints with Pydantic models
3. Import and register in `main.py`
4. Add tests in `tests/`

### Adding a New Model

1. Create model in appropriate `domain/models_*.py`
2. Import in `main.py` for table creation
3. Create service methods if needed
4. Add unit tests

---

## Deployment

### Docker (Recommended)

```dockerfile
# Backend Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL instead of SQLite
- [ ] Set up HTTPS with valid certificates
- [ ] Configure proper CORS origins
- [ ] Set strong `SECRET_KEY`
- [ ] Enable audit logging to persistent storage
- [ ] Set up monitoring and alerting

---

## Roadmap

### Completed ✅

- [x] Domain model with 25+ entities
- [x] 8-stage scheduling engine
- [x] Quality blending and constraints
- [x] Stockpile management (simple + staged)
- [x] Wash plant integration
- [x] 3D spatial visualization
- [x] Gantt chart scheduling
- [x] Flow network editor
- [x] Reporting dashboard
- [x] RBAC and audit logging
- [x] Test suite

### Future Enhancements

- [ ] Real-time GPS integration
- [ ] Machine learning predictions
- [ ] Mobile companion app
- [ ] Multi-tenant SaaS deployment
- [ ] Advanced constraint programming solver

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Acknowledgments

- Built for the mining industry by mining professionals
- Inspired by real-world coal mine scheduling challenges
- Special thanks to all contributors

---

<div align="center">

**MineOpt Pro** - Optimizing Mine Production, One Shift at a Time

[Report Bug](https://github.com/SIHLE-MTSHALI/MineOpt-pro/issues) • [Request Feature](https://github.com/SIHLE-MTSHALI/MineOpt-pro/issues)

</div>
