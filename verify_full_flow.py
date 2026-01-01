import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_verification():
    print("=== MineOpt Pro Enterprise Verification ===")
    
    # 1. Initialize Site (Seed Data)
    print("\n[1] Seeding Demo Data...")
    try:
        res = requests.post(f"{BASE_URL}/config/seed-demo-data?site_id=Site-A")
        res.raise_for_status()
        data = res.json()
        print(f"    Success: Created Site '{data['site']['name']}'")
        site_id = data['site']['site_id']
        version_id = data['version']['version_id']
        print(f"    Site ID: {site_id}")
        print(f"    Schedule Version ID: {version_id}")
    except Exception as e:
        print(f"    FAILED: {e}")
        return

    # 2. Verify Flow Network
    print("\n[2] Verifying Flow Network (Stockpiles)...")
    try:
        res = requests.get(f"{BASE_URL}/config/network-nodes?site_id={site_id}")
        nodes = res.json()
        stockpiles = [n for n in nodes if n['node_type'] == 'Stockpile']
        print(f"    Found {len(nodes)} nodes, {len(stockpiles)} stockpiles.")
        if len(stockpiles) > 0:
            print(f"    Sample: {stockpiles[0]['name']}")
        else:
            print("    WARNING: No stockpiles found.")
    except Exception as e:
        print(f"    FAILED: {e}")

    # 3. Verify Resources
    print("\n[3] Verifying Resources...")
    try:
        res = requests.get(f"{BASE_URL}/config/resources?site_id={site_id}")
        resources = res.json()
        excavators = [r for r in resources if r['resource_type'] == 'Excavator']
        print(f"    Found {len(resources)} resources, {len(excavators)} excavators.")
    except Exception as e:
        print(f"    FAILED: {e}")

    # 4. Run Optimization (Auto-Schedule)
    print("\n[4] Running Optimization (Auto-Schedule)...")
    try:
        payload = {"site_id": site_id, "schedule_version_id": version_id}
        start = time.time()
        res = requests.post(f"{BASE_URL}/optimization/run", json=payload)
        res.raise_for_status()
        result = res.json()
        duration = time.time() - start
        print(f"    Success: {result['message']}")
        print(f"    Tasks Created: {result.get('tasks_count', 'N/A')}")
        print(f"    Time Taken: {duration:.2f}s")
    except Exception as e:
        print(f"    FAILED: {e}")
        if res.content:
            print(f"    Error Content: {res.content}")

    # 5. Verify Schedule Tasks
    print("\n[5] Verifying Schedule Output...")
    try:
        res = requests.get(f"{BASE_URL}/schedule/versions/{version_id}/tasks")
        tasks = res.json()
        print(f"    Retrieved {len(tasks)} verified tasks from DB.")
        if len(tasks) > 0:
            print(f"    Sample Task: {tasks[0]['planned_quantity']}t on {tasks[0]['period_id']}")
    except Exception as e:
        print(f"    FAILED: {e}")

    # 6. Verify Reporting Dashboard
    print("\n[6] generating Dashboard Report...")
    try:
        res = requests.get(f"{BASE_URL}/reporting/dashboard/{version_id}")
        report = res.json()
        print(f"    Total Tons: {report['total_tons']}")
        print(f"    Coal Tons: {report['coal_tons']}")
        print(f"    Waste Tons: {report['waste_tons']}")
        print(f"    Stripping Ratio: {report['stripping_ratio']}")
        print(f"    Chart Data Points: {len(report['chart_data'])}")
    except Exception as e:
        print(f"    FAILED: {e}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    run_verification()
