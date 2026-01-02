# MineOpt Pro - Enterprise Production Optimization Platform

**MineOpt Pro** is a state-of-the-art open-cast mining execution system designed to bridge the gap between long-term planning and short-term operational reality. It integrates **3D Spatial Visualization**, **Automated Scheduling**, and **Real-time Analytics** into a single, cohesive web interface.

---

## 🚀 Getting Started

Follow these instructions to set up the full Enterprise system on your local machine.

### Prerequisites
*   **Python 3.9+** (for the Backend API)
*   **Node.js 16+** & **npm** (for the Frontend UI)

### 1. Backend Setup (The Engine)
The backend powers the database, optimization algorithms, and 3D geometry engine.

```bash
cd backend
# Create a virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Run the Server
python -m uvicorn app.main:app --reload
```
*The API will start at `http://localhost:8000`.*

### 2. Frontend Setup (The Interface)
The frontend provides the modern, glass-morphism user interface.

```bash
cd frontend

# Install Dependencies
npm install

# Start the Development Server
npm run dev
```
*The App will open at `http://localhost:5173`.*

---

## 🔐 Authentication & Access

### Login
Upon launching the application, you will be presented with the **Enterprise Login Screen**.
*   **Default Admin Credentials**:
    *   Username: `admin`
    *   Password: `admin`

### Creating a New Account
If you wish to create a separate planner account:
1.  Click **"Don't have an account? Sign Up"** on the login screen.
2.  Enter your desired username, password, and email.
3.  Click "Create Account". You will be redirected to login with your new credentials.

---

## 🎮 Features & Usage Guide

### 1. Initializing the Project
When you first log in, the system may be empty. To explore the features, you should load the **Enterprise Demo Dataset**.

1.  Look for the **"Initialize Demo Data"** button in the top header.
2.  Click it to seed the database with:
    *   A 3x3 **Block Model** (Coal & Waste).
    *   A **Resource Fleet** (Excavator & Trucks).
    *   **Stockpiles** and Wash Plant configurations.
3.  The page will reload, and you will see the 3D Pit Visualization.

### 2. 3D Spatial Planner (The "Map")
The **Spatial Tab** is your primary view of the mine geometry.
*   **Navigation**:
    *   **Rotate**: Left Click + Drag.
    *   **Pan**: Right Click + Drag.
    *   **Zoom**: Mouse Wheel.
*   **Block Interaction**: Click on any block to see its properties in the Right Panel (Material, Tonnage, Grade).
*   **Stockpiles**: View dynamic cones representing ROM and Product stocks. Hover to see current inventory levels.

### 3. Scenario Management (Versioning)
MineOpt Pro supports "What-If" analysis through **Scenarios**.
*   **Switching Scenarios**: Use the Dropdown in the top header to switch between different mining plans (e.g., "Initial Draft", "High Production Case").
*   **Forking / Copying**:
    1.  Click the **"Fork / Copy"** button next to the dropdown.
    2.  Enter a name for the new scenario (e.g., "Plan B - Excavator Down").
    3.  The system creates a **Deep Copy** of the current schedule. You can now modify this copy without affecting the original plan.

### 4. Scheduling & Optimization
There are two ways to build a mining schedule:

#### A. Manual Scheduling
1.  Select a Block in the **3D View**.
2.  In the Properties Panel, click **"+ Add to Schedule"**.
3.  The system assigns the block to the first available period for the default Excavator.

#### B. Auto-Scheduling (The Optimizer)
The **Optimization Engine** uses a greedy heuristic to automatically generate a feasible mining sequence.
1.  Ensure you have selected the correct Scenario.
2.  Click the **"⚡ Auto-Schedule"** button in the header.
3.  The algorithm processes the **Topological Constraints** (mining top-down) and **Resource Capacities**.
4.  The schedule is populated instantly.

### 5. Gantt Chart
Switch to the **Gantt Tab** to see the timeline of operations.
*   **Y-Axis**: Mining Resources (Excavators).
*   **X-Axis**: Time Periods (Shifts).
*   **Bars**: Represent mining tasks. The length and color indicate duration and material type.

### 6. Reports & Analytics
Switch to the **Dashboard Tab** for high-level business intelligence.
*   **Production Stats**: Total Tons, Coal Tons, Waste Tons.
*   **Stripping Ratio**: Real-time calculation of Waste/Coal ratio.
*   **Shift Performance**: Bar charts visualizing production output per shift.

---

## 🛠️ System Architecture

*   **Backend**: Python, FastAPI, SQLAlchemy (SQLite).
*   **Frontend**: React, Vite, TailwindCSS (Dark Mode), Three.js (3D).
*   **Security**: JWT (JSON Web Tokens) with Stateless Authentication.

---
*MineOpt Pro v2.0.0-Enterprise*
