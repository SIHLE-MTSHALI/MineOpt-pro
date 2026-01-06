# MineOpt Pro - User Guide

## Overview

MineOpt Pro is an enterprise-grade coal mine production scheduling and optimization system. This guide provides comprehensive instructions for using the platform's key features.

---

## Getting Started

### Accessing the System

1. Navigate to the MineOpt Pro URL provided by your administrator
2. Click **"Get Started"** on the landing page
3. Enter your email and password to log in
4. For first-time users, click **"Register"** to create an account

### Dashboard Overview

After logging in, you'll see the **Site Dashboard** with:

- **KPI Cards**: Planned tonnes, actual vs plan variance, quality compliance, active resources
- **Active Schedule Summary**: Current schedule status and optimization details
- **Quick Actions**: Run Fast Pass, Create Scenario, View Reports, Site Settings
- **Alerts**: Recent notifications and warnings
- **Stockpile Status**: Current stockpile levels with progress bars

---

## Scheduling Module

### Gantt Chart Interaction

The Gantt chart provides a visual timeline of scheduled tasks:

| Action | How To |
|--------|--------|
| Move task | Drag and drop to new time slot |
| Split task | Right-click → "Split Task" → Set percentage and target period |
| Change resource | Right-click → "Change Resource" → Select new resource |
| View explanation | Right-click → "View Explanation" |
| Edit rate factor | Click on task's inline rate input |

### Context Menu Options

Right-click any task to access:
- ✏️ **Edit Task**: Modify task properties
- ✂️ **Split Task**: Divide task across periods
- 📋 **Duplicate**: Create a copy of the task
- 🔄 **Change Resource**: Reassign to different equipment
- 📊 **View Explanation**: See optimization decisions
- 🗑️ **Delete Task**: Remove from schedule

### Diagnostics Panel

Access scheduling diagnostics to understand optimization decisions:

1. Open the **Diagnostics Panel** from the toolbar
2. View sections:
   - **Infeasibilities**: Constraint violations
   - **Blocked Routes**: Unavailable transport paths
   - **Binding Constraints**: Active limitations
   - **Decision Explanations**: Why specific choices were made

---

## Quality Management

### Simulation Panel

Run Monte Carlo simulations to understand quality uncertainty:

1. Open the **Simulation Panel**
2. Select iteration count (100 - 10,000)
3. Click **Run Simulation**
4. Review results:
   - **Confidence Bands**: P5/P50/P95 ranges
   - **Compliance Probability**: Likelihood of meeting specs
   - **Risk Score**: Overall quality risk assessment

### Product Specifications

Define quality targets for different products:

1. Navigate to **Product Specifications**
2. Click **"New Product"**
3. Enter:
   - Product name and code
   - Quality field min/max values (CV, Ash, Moisture, etc.)
4. Add demand periods with target and committed tonnes

---

## Integration Features

### External ID Mapping

Map external system IDs to MineOpt entities:

1. Go to **Integration → External ID Mappings**
2. Select entity type tab (Parcels, Resources, Locations, Products)
3. Actions:
   - **Add Mapping**: Click "Add Mapping" button
   - **Import CSV**: Upload file with `external_id`, `internal_id`, `description` columns
   - **Export**: Download current mappings as CSV
   - **Search**: Filter by external ID, internal ID, or description

### BI Extract Publishing

Schedule data exports for business intelligence:

1. Go to **Integration → BI Extract Publisher**
2. Click **"New Extract"**
3. Configure:
   - Name and data type
   - Schedule (hourly, daily, weekly, or custom cron)
   - Output format (JSON/CSV)
   - Destination path
4. Click **"Run Now"** for immediate export

---

## Reporting

### Scheduled Reports

Set up automated email reports:

1. Navigate to **Reports → Schedules**
2. Create new schedule with:
   - Report type (daily production, weekly summary, quality analysis)
   - Cron schedule
   - Recipient emails
3. Enable/disable as needed

### Report Packs

Generate bundled PDF reports:

1. Go to **Reports → Generate Pack**
2. Select report types to include
3. Set date range
4. Click **Generate**
5. Download the combined PDF

---

## Collaboration

### Presence Indicators

See who else is working on the schedule:
- **Green dot**: User is active
- **Yellow dot**: User is idle
- **Pencil icon**: User is editing

### Change Log

Track all modifications:
1. Open the **Change Log** panel
2. View chronological list of changes
3. Filter by user, date, or entity type

---

## Geometry Editing

### Vertex Editing Mode

Modify mining area boundaries:

1. Select an area on the map
2. Enable **Vertex Edit Mode**
3. Drag vertices to adjust boundaries
4. Use **Undo/Redo** buttons for corrections
5. Click **Save** to commit changes

### Polygon Tools

| Tool | Function |
|------|----------|
| Split | Divide polygon into multiple areas |
| Merge | Combine adjacent polygons |
| Add Vertex | Insert new point on edge |
| Delete Vertex | Remove selected point |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Z` | Undo last action |
| `Ctrl + Y` | Redo |
| `Ctrl + S` | Save current changes |
| `Escape` | Cancel current operation |
| `Delete` | Remove selected item |

---

## Troubleshooting

### Common Issues

**Schedule won't optimize**
- Check for infeasibilities in Diagnostics Panel
- Verify all required data is configured
- Ensure equipment availability is set

**Quality values seem wrong**
- Review lab import status for pending results
- Check external ID mappings are correct
- Verify parcel quality vectors are updated

**BI Export failed**
- Verify destination path is writable
- Check network connectivity for API endpoints
- Review error logs in export history

### Getting Help

Contact your system administrator or refer to:
- API Documentation: `/docs/API_DOCUMENTATION.md`
- Developer Guide: `/docs/DEVELOPER_GUIDE.md`
- In-app help: Click the **?** icon in the header

---

*MineOpt Pro v2.0.0-Enterprise*
