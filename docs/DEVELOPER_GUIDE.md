# MineOpt Pro - Developer Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

App runs at: http://localhost:5173

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── domain/         # SQLAlchemy models
│   │   ├── routers/        # FastAPI endpoints
│   │   ├── services/       # Business logic
│   │   └── main.py         # App entry point
│   └── tests/              # Pytest tests
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   └── styles/         # CSS
│   └── public/
└── docs/                   # Documentation
```

---

## Key Services

### LP Solver (`lp_solver.py`)
Linear programming optimization using SciPy.

```python
from app.services.lp_solver import LPModel

model = LPModel()
model.add_variable("x1", lb=0, ub=100)
model.add_constraint([("x1", 1)], "<=", 50)
model.set_objective([("x1", -1)], "minimize")
result = model.solve()
```

### Quality Simulator (`quality_simulator.py`)
Monte Carlo simulation for quality uncertainty.

```python
from app.services.quality_simulator import QualitySimulator

simulator = QualitySimulator(n_simulations=1000)
result = simulator.simulate_blend(parcels, specs)
```

### Wash Plant Service (`wash_plant_service.py`)
Multi-stage coal washing with cutpoint optimization.

```python
from app.services.wash_plant_service import WashPlantService

service = WashPlantService(db)
result = service.process_multi_stage(node_id, feed, quality, stage_configs)
```

---

## Adding New Features

### 1. Add Domain Model
```python
# app/domain/models_new.py
from sqlalchemy import Column, String
from ..database import Base

class NewEntity(Base):
    __tablename__ = "new_entities"
    id = Column(String, primary_key=True)
    name = Column(String)
```

### 2. Add Service
```python
# app/services/new_service.py
class NewService:
    def __init__(self, db=None):
        self.db = db
    
    def create(self, data):
        # Business logic
        pass
```

### 3. Add Router
```python
# app/routers/new_router.py
from fastapi import APIRouter

router = APIRouter(prefix="/new", tags=["New"])

@router.get("/")
def list_entities():
    return {"items": []}
```

### 4. Register Router
```python
# app/main.py
from .routers import new_router
app.include_router(new_router.router)
```

### 5. Add Tests
```python
# tests/test_new.py
def test_new_feature():
    assert True
```

---

## Testing

### Run All Tests
```bash
cd backend
pytest -v
```

### Run Specific Tests
```bash
pytest tests/test_services.py -v
pytest -k "test_blend" -v
```

### Coverage Report
```bash
pytest --cov=app --cov-report=html
```

---

## Database

### SQLite (Development)
Default: `mineopt.db` in backend folder

### Migrations
```bash
python migrate_schema.py
```

### Reset Database
```bash
rm mineopt.db
python -m uvicorn app.main:app --reload  # Auto-creates
```

---

## Security

### Authentication Flow
1. User logs in → receives JWT token
2. Token includes session_id for tracking
3. Sessions limited to 3 concurrent per user
4. All actions logged to audit trail

### Protected Endpoints
```python
from app.services.security import get_current_user, require_role

@router.get("/admin")
def admin_only(user = Depends(require_role("admin"))):
    return {"message": "Admin access"}
```

---

## Deployment

### Production Build
```bash
# Frontend
cd frontend
npm run build

# Backend
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Environment Variables
```bash
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://your-domain.com
```

---

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Module Not Found
```bash
pip install -r requirements.txt
```

### Frontend Build Errors
```bash
rm -rf node_modules
npm install
```

---

## Contact

For questions, open an issue on GitHub.
