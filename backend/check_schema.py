"""
Script to check database schema against SQLAlchemy models.
Identifies missing columns in the database.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mineopt_pro.db")

print(f"Database: {DB_PATH}")
if not os.path.exists(DB_PATH):
    print("ERROR: Database file not found!")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"\nTables in database ({len(tables)}):")
for t in sorted(tables):
    print(f"  - {t}")

# Check specific tables that are causing errors
print("\n" + "="*60)
print("Checking tables with known issues:")
print("="*60)

# Check resources table
print("\n[resources] table columns:")
cursor.execute("PRAGMA table_info(resources)")
cols = cursor.fetchall()
col_names = [c[1] for c in cols]
print(f"  Columns: {col_names}")

# Expected columns from model
expected_resource_cols = [
    'resource_id', 'site_id', 'name', 'resource_type', 'capacity_type',
    'base_rate', 'base_rate_units', 'can_reduce_rate_for_blend',
    'min_rate_factor', 'max_rate_factor', 'cost_per_hour', 'cost_per_tonne',
    'emissions_factor', 'supported_activities', 'created_at'
]
missing_resource = set(expected_resource_cols) - set(col_names)
if missing_resource:
    print(f"  MISSING: {missing_resource}")

# Check material_types table
print("\n[material_types] table columns:")
cursor.execute("PRAGMA table_info(material_types)")
cols = cursor.fetchall()
col_names = [c[1] for c in cols]
print(f"  Columns: {col_names}")

expected_material_cols = [
    'material_type_id', 'site_id', 'name', 'category', 'default_density',
    'moisture_basis_for_quantity', 'reporting_group', 'created_at'
]
missing_material = set(expected_material_cols) - set(col_names)
if missing_material:
    print(f"  MISSING: {missing_material}")

# Check all tables for created_at consistency
print("\n" + "="*60)
print("Tables missing 'created_at' column (when expected):")
print("="*60)

tables_needing_created_at = [
    'sites', 'users', 'roles', 'calendars', 'periods', 'activities',
    'activity_areas', 'resources', 'material_types', 'quality_fields',
    'flow_networks', 'flow_nodes', 'flow_arcs', 'stockpile_configs',
    'wash_plant_configs', 'schedule_versions', 'parcels'
]

for table in tables_needing_created_at:
    if table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cursor.fetchall()]
        if 'created_at' not in cols:
            print(f"  {table} - MISSING created_at")

conn.close()
print("\nSchema check complete.")
