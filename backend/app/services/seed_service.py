from sqlalchemy.orm import Session
from ..domain import models_core, models_time, models_resource, models_flow
import datetime
import uuid

def seed_enterprise_data(db: Session):
    # 1. Site Configuration
    site = models_core.Site(
        name="Enterprise Coal Mine",
        unit_system="Metric",
        default_quality_basis_preferences={"CV": "ARB", "Ash": "ADB"}
    )
    db.add(site)
    db.flush() # get site_id

    # 2. Materials & Qualities
    # Materials
    mat_coal = models_resource.MaterialType(site_id=site.site_id, name="Thermal Coal", category="ROM", reporting_group="Coal")
    mat_waste = models_resource.MaterialType(site_id=site.site_id, name="Overburden", category="Waste", reporting_group="Waste")
    db.add_all([mat_coal, mat_waste])
    
    # Qualities
    q_cv = models_resource.QualityField(
        site_id=site.site_id, name="CV_ARB", units="MJ/kg", basis="ARB", 
        aggregation_rule="WeightedAverage", constraint_direction_default="Min"
    )
    q_ash = models_resource.QualityField(
        site_id=site.site_id, name="Ash_ADB", units="%", basis="ADB", 
        aggregation_rule="WeightedAverage", constraint_direction_default="Max"
    )
    db.add_all([q_cv, q_ash])
    db.flush()

    # 3. Calendar & Periods
    cal = models_time.Calendar(site_id=site.site_id, name="Production Calendar", period_granularity_type="Shift")
    db.add(cal)
    db.flush()

    # Generate 14 Shifts (1 Week)
    start_dt = datetime.datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    periods = []
    for i in range(14):
        is_day = i % 2 == 0
        p_start = start_dt + datetime.timedelta(hours=12*i)
        p_end = p_start + datetime.timedelta(hours=12)
        p_name = f"Shift {i+1} ({'Day' if is_day else 'Night'})"
        
        period = models_time.Period(
            calendar_id=cal.calendar_id,
            name=p_name,
            start_datetime=p_start, 
            end_datetime=p_end,
            duration_hours=12.0,
            group_shift="Day" if is_day else "Night",
            group_day=p_start.strftime("%Y-%m-%d")
        )
        periods.append(period)
    db.add_all(periods)
    db.flush()

    # 4. Resources
    # Excavator 1
    ex1 = models_resource.Resource(
        site_id=site.site_id, name="EX-200 (Hitachi 2500)", resource_type="Excavator",
        capacity_type="Throughput", base_rate=1500, base_rate_units="t/h",
        can_reduce_rate_for_blend=True
    )
    # Truck Fleet
    trucks = models_resource.Resource(
        site_id=site.site_id, name="CAT 789 Fleet", resource_type="TruckFleet",
        capacity_type="Volume", base_rate=0, base_rate_units="variable"
    )
    db.add_all([ex1, trucks])
    db.flush()

    # 5. Network & Flow
    net = models_flow.FlowNetwork(site_id=site.site_id, name="Main Pit Network")
    db.add(net)
    db.flush()

    # Nodes
    n_source = models_flow.FlowNode(network_id=net.network_id, node_type="Source", name="Active Pit")
    n_dump = models_flow.FlowNode(network_id=net.network_id, node_type="Dump", name="Waste Dump 1", location_geometry={"position": [-50, 0, -50]})
    n_rom = models_flow.FlowNode(network_id=net.network_id, node_type="Stockpile", name="ROM Pad A", location_geometry={"position": [150, 0, -50]})
    n_plant = models_flow.FlowNode(network_id=net.network_id, node_type="WashPlant", name="CHPP Module 1")
    
    db.add_all([n_source, n_dump, n_rom, n_plant])
    db.flush()

    # Stockpile Config
    sp_config = models_flow.StockpileConfig(
        node_id=n_rom.node_id, 
        inventory_method="WeightedAverage", 
        max_capacity_tonnes=50000,
        current_inventory_tonnes=12000,
        current_grade_vector={"CV_ARB": 21.5, "Ash_ADB": 14.2}
    )
    db.add(sp_config)

    # 6. Activities & Spatial Model (Block Model)
    act_mine = models_resource.Activity(site_id=site.site_id, name="Mining", display_color="#3b82f6")
    db.add(act_mine)
    db.flush()

    # Create 9 Blocks (3x3)
    areas = []
    for x in range(3):
        for y in range(3):
            is_coal = (x+y)%2 == 0
            mat_id = mat_coal.material_type_id if is_coal else mat_waste.material_type_id
            
            # Slice State (JSON)
            slice_state = [{
                "index": 0,
                "status": "Available",
                "quantity": 10000,
                "material_type_id": mat_id,
                "qualities": {"CV_ARB": 24.0 if is_coal else 0, "Ash_ADB": 12.0 if is_coal else 80}
            }]
            
            area = models_resource.ActivityArea(
                site_id=site.site_id,
                activity_id=act_mine.activity_id,
                name=f"Block-{x}-{y}",
                geometry={"position": [x*60, 0, y*60], "size": [50, 10, 50]},
                slice_states=slice_state,
                priority=10
            )
            areas.append(area)
    db.add_all(areas)
    
    db.commit()
    return site.site_id
