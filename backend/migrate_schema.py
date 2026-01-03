"""
Database Schema Migration Script for MineOpt Pro

Fixes schema mismatch errors by adding missing columns to existing tables.
Run this script to fix:
- resources.min_rate_factor missing
- resources.max_rate_factor missing  
- material_types.created_at missing
- And any other column mismatches

Usage:
    python migrate_schema.py

After running, restart the uvicorn server.
"""

import sqlite3
import os
from datetime import datetime

# Database path - same logic as database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mineopt_pro.db")

print("=" * 60)
print("MineOpt Pro - Database Schema Migration")
print("=" * 60)
print(f"\nDatabase: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("\n❌ ERROR: Database file not found!")
    print("   The database will be created when you start the server.")
    print("   Run: uvicorn app.main:app --reload --port 8000")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def get_table_columns(table_name):
    """Get current column names for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]

def add_column_if_missing(table, column, datatype, default=None):
    """Add a column to table if it doesn't exist."""
    columns = get_table_columns(table)
    if column not in columns:
        default_clause = f" DEFAULT {default}" if default is not None else ""
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {datatype}{default_clause}"
        try:
            cursor.execute(sql)
            print(f"  ✓ Added: {table}.{column}")
            return True
        except Exception as e:
            print(f"  ✗ Error adding {table}.{column}: {e}")
            return False
    else:
        print(f"  ○ Exists: {table}.{column}")
        return False

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"\nFound {len(tables)} tables in database.")

# =============================================================================
# MIGRATIONS
# =============================================================================

print("\n" + "-" * 60)
print("Running schema migrations...")
print("-" * 60)

migrations_applied = 0

# --- resources table ---
print("\n[resources]")
if 'resources' in tables:
    if add_column_if_missing('resources', 'min_rate_factor', 'REAL', '0.0'):
        migrations_applied += 1
    if add_column_if_missing('resources', 'max_rate_factor', 'REAL', '1.0'):
        migrations_applied += 1
    if add_column_if_missing('resources', 'can_reduce_rate_for_blend', 'INTEGER', '0'):
        migrations_applied += 1
    if add_column_if_missing('resources', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- material_types table ---
print("\n[material_types]")
if 'material_types' in tables:
    if add_column_if_missing('material_types', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- activities table ---
print("\n[activities]")
if 'activities' in tables:
    if add_column_if_missing('activities', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- activity_areas table ---
print("\n[activity_areas]")
if 'activity_areas' in tables:
    if add_column_if_missing('activity_areas', 'lock_reason', 'TEXT', 'NULL'):
        migrations_applied += 1
    if add_column_if_missing('activity_areas', 'preferred_destination_node_id', 'TEXT', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- quality_fields table ---
print("\n[quality_fields]")
if 'quality_fields' in tables:
    if add_column_if_missing('quality_fields', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- flow_networks table ---
print("\n[flow_networks]")
if 'flow_networks' in tables:
    if add_column_if_missing('flow_networks', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- flow_nodes table ---
print("\n[flow_nodes]")
if 'flow_nodes' in tables:
    if add_column_if_missing('flow_nodes', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- flow_arcs table ---
print("\n[flow_arcs]")
if 'flow_arcs' in tables:
    if add_column_if_missing('flow_arcs', 'created_at', 'DATETIME', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# --- schedule_versions table ---
print("\n[schedule_versions]")
if 'schedule_versions' in tables:
    if add_column_if_missing('schedule_versions', 'run_request_id', 'TEXT', 'NULL'):
        migrations_applied += 1
else:
    print("  Table not found - will be created on server start")

# Commit changes
conn.commit()
conn.close()

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 60)
if migrations_applied > 0:
    print(f"✓ Migration complete! {migrations_applied} column(s) added.")
else:
    print("✓ No migrations needed - schema is up to date.")
print("=" * 60)

print("\nNext steps:")
print("  1. Restart the uvicorn server:")
print("     uvicorn app.main:app --reload --port 8000")
print("  2. Test the API at http://localhost:8000/docs")
print("  3. Seed demo data: POST /config/seed-demo-data")
