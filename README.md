# MineOpt Pro

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)

**Enterprise Open-Cast Mine Production Scheduling and Optimization System**

[Quick Start](#quick-start) • [Features](#features) • [Setup Guide](#detailed-setup-guide) • [Usage Guide](#usage-guide) • [API Reference](#api-reference) • [Troubleshooting](#troubleshooting)

</div>

---

## What is MineOpt Pro?

MineOpt Pro is a comprehensive production scheduling and optimization platform designed for open-cast mining operations. It helps mining engineers:

- **Plan production schedules** with 12-hour shift granularity
- **Optimize material blending** to meet quality targets
- **Track equipment fleet** in real-time with GPS
- **Design drill & blast patterns** with fragmentation prediction
- **Monitor slope stability** and environmental conditions
- **Generate reports** and analytics dashboards

Whether you're a mining engineer, scheduler, or supervisor, MineOpt Pro provides the tools you need to optimize your mining operations.

---

## Quick Start

> **For Beginners**: Follow these steps exactly in order. Each step must complete before moving to the next.

### Prerequisites

Before you begin, make sure you have:

| Requirement | Version | How to Check | Download |
|-------------|---------|--------------|----------|
| Python | 3.10+ | `python --version` | [python.org](https://python.org) |
| Node.js | 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| Git | Any | `git --version` | [git-scm.com](https://git-scm.com) |

### Step 1: Clone the Repository

```bash
git clone https://github.com/SIHLE-MTSHALI/Open-Cast_Mine_Production_Optimization_Dashboard.git
cd Open-Cast_Mine_Production_Optimization_Dashboard
```

### Step 2: Set Up the Backend

```bash
# Navigate to the backend folder
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python packages (this may take 2-3 minutes)
pip install -r requirements.txt
```

### Step 3: Start the Backend Server

```bash
# Make sure you're in the backend folder with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**✅ Keep this terminal open and running!**

### Step 4: Set Up the Frontend (New Terminal)

Open a **new terminal window** (keep the backend running):

```bash
# Navigate to the frontend folder
cd frontend

# Install npm packages (this may take 2-3 minutes)
npm install

# Start the development server
npm run dev
```

You should see:
```
  VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### Step 5: Open the Application

Open your web browser and go to: **http://localhost:5173**

🎉 **Congratulations! MineOpt Pro is now running!**

---

## Features

### 📍 Fleet Management System

Track and manage your mining fleet in real-time.

| Feature | Description |
|---------|-------------|
| **GPS Tracking** | Live location of all equipment on the map |
| **Geofencing** | Set restricted zones and get violation alerts |
| **Haul Cycle Analysis** | Automatic detection of loading, hauling, dumping cycles |
| **Maintenance Scheduling** | Gantt-style calendar for planned maintenance |
| **Equipment Health** | ML-based failure prediction with risk scores |

**Frontend Components:**
- `FleetMapOverlay` - Equipment icons on interactive map
- `EquipmentDetailCard` - Popup with status and controls
- `HaulCycleDashboard` - Cycle KPIs and analytics
- `MaintenanceCalendar` - Maintenance schedule view
- `EquipmentHealthDashboard` - Health scores and alerts

---

### 💥 Drill & Blast Module

Design and simulate blast patterns with fragmentation prediction.

| Feature | Description |
|---------|-------------|
| **Pattern Designer** | Interactive 2D grid for hole placement |
| **Delay Timing** | Visual delay sequence visualization |
| **Kuz-Ram Prediction** | Calculate expected fragmentation (X50) |
| **Drill Log Generation** | Export drill hole specifications |

**How to Use:**
1. Go to the Drill & Blast section
2. Click "New Pattern" to create a blast design
3. Set burden and spacing parameters
4. Place drill holes on the grid
5. Assign delay numbers for sequencing
6. Click "Predict Fragmentation" to see expected results

**Frontend Component:** `BlastPatternDesigner`

---

### 📦 Material Tracking & Shift Operations

Track material movements and manage shift handovers.

| Feature | Description |
|---------|-------------|
| **Load Tickets** | Record each truck load with origin, destination, tonnage |
| **Material Flow** | Sankey diagram visualization of material movements |
| **Shift Handovers** | Digital handover forms with notes and tasks |
| **Incident Logging** | Record and track safety incidents |

**Frontend Components:**
- `MaterialFlowSankey` - Visual flow diagram
- `ShiftHandoverForm` - Digital handover form

---

### 🏔️ Geotechnical Monitoring

Monitor slope stability and water levels.

| Feature | Description |
|---------|-------------|
| **Prism Monitoring** | Track survey prism movements |
| **Displacement Alerts** | Automatic alerts when thresholds exceeded |
| **Water Level Tracking** | Monitor bore water levels |
| **Trend Analysis** | Historical movement visualization |

**How to Use:**
1. Navigate to Monitoring > Slope Stability
2. View prism status cards with color-coded alerts
3. Click a prism to see detailed displacement history
4. Set alert thresholds in Settings

**Frontend Component:** `SlopeMonitoringPanel`

---

### 🌬️ Environmental Monitoring

Track dust levels and air quality.

| Feature | Description |
|---------|-------------|
| **Dust Monitoring** | PM10 and PM2.5 real-time readings |
| **Exceedance Alerts** | Automatic alerts when limits exceeded |
| **Historical Trends** | View readings over time |
| **Weather Integration** | Wind speed and direction display |

**Frontend Component:** `DustMonitoringDashboard`

---

### ⚠️ Safety Management

Manage hazards and operator fatigue.

| Feature | Description |
|---------|-------------|
| **Hazard Zones** | Define exclusion and hazard areas on map |
| **Zone Violations** | Track equipment entering hazard zones |
| **Fatigue Scoring** | Calculate operator fatigue risk (0-100) |
| **Rest Recommendations** | Automatic rest break suggestions |

---

### 🔌 Integration Hub

Connect to external systems.

| System | Connection Type | Features |
|--------|-----------------|----------|
| **SCADA** | OPC-UA | Tag reading, historian queries |
| **SAP** | RFC | Cost rates, work order sync |
| **Oracle EBS** | REST | Invoice posting, production records |

---

### 🤖 Machine Learning Services

Predictive analytics for equipment and operations.

| Model | Purpose | Output |
|-------|---------|--------|
| **Failure Predictor** | Predict equipment failures | Risk score 0-100 |
| **Grade Predictor** | Predict ore grade from drilling | Grade % |
| **Route Optimizer** | Find optimal haul routes | Shortest path |

---

### 📊 Query Builder

Create ad-hoc reports without SQL knowledge.

| Feature | Description |
|---------|-------------|
| **Table Selection** | Choose from available data tables |
| **Column Picker** | Select fields to include |
| **Filters** | Add conditions (equals, greater than, etc.) |
| **Aggregations** | Sum, average, count, min, max |
| **Export** | Download as CSV or chart |

**How to Use:**
1. Go to Reports > Query Builder
2. Select a table from the dropdown
3. Choose columns to display
4. Add filters if needed
5. Click "Run Query"
6. Export results as needed

**Frontend Component:** `QueryBuilder`

---

### 🎥 3D Visualization

Advanced 3D surface visualization and comparison.

| Feature | Description |
|---------|-------------|
| **Surface Timeline** | Play back surface changes over time |
| **Version Comparison** | Compare two surfaces side-by-side |
| **Cut/Fill Volumes** | Calculate volume differences |
| **Excavation Progress** | Track cumulative excavation chart |
| **3D Measurements** | Point, distance, area measurements |
| **LOD Settings** | Adjust render quality for performance |

**Frontend Components:**
- `SurfaceTimelinePlayer` - Timeline scrubber for playback
- `SurfaceComparisonOverlay` - Cut/fill comparison
- `ExcavationProgressChart` - Cumulative volume chart
- `MeasurementToolbar3D` - Measurement tools
- `LODSettingsPanel` - Render quality settings

---

## Detailed Setup Guide

### Option 1: Basic Development Setup

This is the simplest setup for development and testing.

```bash
# Terminal 1: Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

### Option 2: Docker Setup

For consistent environments, use Docker:

```bash
# Build and run both services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

**docker-compose.yml** is included in the project.

### Option 3: Production Setup

For production deployment:

```bash
# Backend
cd backend
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Frontend (build static files)
cd frontend
npm run build
# Serve the 'dist' folder with your web server (nginx, etc.)
```

---

## Usage Guide

### Starting the Application

| Component | Command | URL |
|-----------|---------|-----|
| Backend API | `uvicorn app.main:app --reload --port 8000` | http://localhost:8000 |
| Frontend UI | `npm run dev` | http://localhost:5173 |
| API Docs | (auto-generated) | http://localhost:8000/docs |

### Navigating the Interface

1. **Dashboard** - Overview of key metrics
2. **3D Viewer** - Interactive mine visualization
3. **Scheduling** - Gantt charts and production plans
4. **Fleet** - Equipment tracking and maintenance
5. **Drill & Blast** - Pattern design
6. **Operations** - Material and shift management
7. **Monitoring** - Geotech and environmental
8. **Reports** - Query builder and dashboards

### Common Workflows

#### Creating a Schedule

1. Go to Scheduling > New Schedule
2. Select the calendar period
3. Choose resources to include
4. Run "Fast Pass" for quick schedule
5. Review and adjust as needed
6. Publish when ready

#### Tracking Equipment

1. Go to Fleet > Map View
2. See all equipment locations in real-time
3. Click an equipment icon for details
4. View haul cycles and utilization

#### Designing a Blast Pattern

1. Go to Drill & Blast > Pattern Designer
2. Set pattern parameters (burden, spacing)
3. Place holes on the grid
4. Set delay sequence
5. Run fragmentation prediction

#### Monitoring Slopes

1. Go to Monitoring > Slope Stability
2. View prism status cards
3. Check alert history
4. Export data for analysis

---

## API Reference

### Health Check

```bash
GET /
# Returns: {"status": "MineOpt Pro Server Running", "version": "2.0.0-Enterprise"}
```

### Fleet Endpoints

```bash
# Get all equipment
GET /fleet/equipment

# Get equipment GPS readings
GET /fleet/equipment/{equipment_id}/gps

# Record GPS reading
POST /fleet/equipment/{equipment_id}/gps
Body: {"latitude": -26.2, "longitude": 28.0, "heading": 90, "speed_kmh": 25}

# Get haul cycle KPIs
GET /fleet/equipment/{equipment_id}/haul-cycle-kpis
```

### Drill & Blast Endpoints

```bash
# Create blast pattern
POST /drill-blast/patterns
Body: {"site_id": "...", "pattern_name": "Pattern 1", "burden": 4.0, "spacing": 5.0}

# Get fragmentation prediction
GET /drill-blast/patterns/{pattern_id}/fragmentation
```

### Operations Endpoints

```bash
# Create load ticket
POST /operations/tickets
Body: {"truck_fleet_number": "TR01", "origin_name": "Pit A", "tonnes": 120}

# Get current shift
GET /operations/sites/{site_id}/current-shift
```

### Monitoring Endpoints

```bash
# Record prism reading
POST /monitoring/prisms/readings
Body: {"prism_id": "...", "x": 1000.0, "y": 2000.0, "z": 100.0}

# Get slope alerts
GET /monitoring/sites/{site_id}/slope-alerts
```

### Surface History Endpoints

```bash
# List surface versions
GET /surfaces/{surface_id}/history

# Compare surfaces
POST /surfaces/compare
Body: {"base_version_id": "...", "compare_version_id": "..."}

# Get excavation progress
GET /surfaces/sites/{site_id}/progress
```

### Full API Documentation

Access the interactive API docs at: **http://localhost:8000/docs**

---

## Project Structure

```
Open-Cast_Mine_Production_Optimization_Dashboard/
│
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── domain/               # Database models
│   │   │   ├── models_core.py
│   │   │   ├── models_fleet.py
│   │   │   ├── models_drill_blast.py
│   │   │   ├── models_material_shift.py
│   │   │   ├── models_geotech_safety.py
│   │   │   └── models_surface_history.py
│   │   │
│   │   ├── services/             # Business logic
│   │   │   ├── fleet_service.py
│   │   │   ├── drill_blast_service.py
│   │   │   ├── material_shift_service.py
│   │   │   ├── geotech_safety_service.py
│   │   │   ├── integration_hub.py
│   │   │   ├── ml_service.py
│   │   │   ├── query_builder_service.py
│   │   │   └── surface_history_service.py
│   │   │
│   │   ├── routers/              # API endpoints
│   │   │   ├── fleet_router.py
│   │   │   ├── drill_blast_router.py
│   │   │   ├── operations_router.py
│   │   │   ├── monitoring_router.py
│   │   │   └── surface_history_router.py
│   │   │
│   │   ├── database.py           # Database connection
│   │   └── main.py               # Application entry point
│   │
│   ├── tests/                    # Test files
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── fleet/            # Fleet management UI
│   │   │   │   ├── FleetMapOverlay.jsx
│   │   │   │   ├── EquipmentDetailCard.jsx
│   │   │   │   ├── HaulCycleDashboard.jsx
│   │   │   │   ├── MaintenanceCalendar.jsx
│   │   │   │   └── EquipmentHealthDashboard.jsx
│   │   │   │
│   │   │   ├── drill-blast/      # Drill & blast UI
│   │   │   │   └── BlastPatternDesigner.jsx
│   │   │   │
│   │   │   ├── operations/       # Operations UI
│   │   │   │   └── ShiftHandoverForm.jsx
│   │   │   │
│   │   │   ├── material/         # Material tracking UI
│   │   │   │   └── MaterialFlowSankey.jsx
│   │   │   │
│   │   │   ├── geotech/          # Geotechnical UI
│   │   │   │   └── SlopeMonitoringPanel.jsx
│   │   │   │
│   │   │   ├── environmental/    # Environmental UI
│   │   │   │   └── DustMonitoringDashboard.jsx
│   │   │   │
│   │   │   ├── reporting/        # Reporting UI
│   │   │   │   └── QueryBuilder.jsx
│   │   │   │
│   │   │   └── viewer3d/         # 3D visualization UI
│   │   │       ├── SurfaceTimelinePlayer.jsx
│   │   │       ├── SurfaceComparisonOverlay.jsx
│   │   │       ├── ExcavationProgressChart.jsx
│   │   │       ├── MeasurementToolbar3D.jsx
│   │   │       └── LODSettingsPanel.jsx
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   └── package.json              # JavaScript dependencies
│
└── README.md                     # This file
```

---

## Troubleshooting

### Backend Issues

#### "Module not found" Error

```bash
# Make sure venv is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### "Port 8000 already in use"

```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

#### Database Connection Error

```bash
# The database is created automatically on first run
# If issues persist, delete mineopt.db and restart
del mineopt.db  # Windows
rm mineopt.db   # Mac/Linux
```

### Frontend Issues

#### "npm install" Fails

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and try again
rmdir /s /q node_modules  # Windows
rm -rf node_modules       # Mac/Linux

npm install
```

#### "Cannot connect to backend"

1. Check backend is running on port 8000
2. Check browser console for CORS errors
3. Verify `http://localhost:8000` is accessible

#### Page Shows Blank

```bash
# Check for JavaScript errors in browser console (F12)
# Restart the dev server
npm run dev
```

### Common Error Messages

| Error | Solution |
|-------|----------|
| `ENOENT: no such file or directory` | Run `npm install` in the frontend folder |
| `ModuleNotFoundError` | Activate venv and run `pip install -r requirements.txt` |
| `Connection refused` | Make sure backend server is running |
| `CORS error` | Backend and frontend ports must be 8000 and 5173 |

---

## Configuration

### Environment Variables

Create a `.env` file in the backend folder:

```bash
# Database (SQLite is default, PostgreSQL for production)
DATABASE_URL=sqlite:///./mineopt.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/mineopt

# Server
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here

# CORS (allowed frontend origins)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Changing the Database

By default, MineOpt Pro uses SQLite (file-based, good for development).

For production, use PostgreSQL:

1. Install PostgreSQL
2. Create a database: `createdb mineopt`
3. Update `DATABASE_URL` in `.env`
4. Restart the backend

---

## Testing

### Running Backend Tests

```bash
cd backend
pytest

# With verbose output
pytest -v

# Specific test file
pytest tests/test_services.py

# With coverage report
pytest --cov=app --cov-report=html
```

### Running Frontend Tests

```bash
cd frontend
npm test
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `pytest` and `npm test`
5. Commit: `git commit -m 'feat: add my feature'`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

---

## Need Help?

- **API Documentation**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas

---

<div align="center">

**MineOpt Pro** - Optimizing Mine Production, One Shift at a Time

Built with ❤️ for the mining industry

</div>
