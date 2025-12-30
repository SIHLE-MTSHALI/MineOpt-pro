from sqlalchemy.orm import Session
from ..domain import models_site, models_config, models_resources, models_flow, models_scheduling
import uuid
from datetime import datetime
def seed_test_data(db: Session):
    # 1. Create Site
    site = models_site.Site(name="Demo Mine Site", time_zone="UTC")
    db.add(site)
    db.flush()

    # 2. Config (Materials)
    mat_coal = models_config.MaterialType(site_id=site.site_id, name="Thermal Coal", category="ROM", default_density=1.4)
    mat_waste = models_config.MaterialType(site_id=site.site_id, name="Waste", category="Waste", default_density=2.2)
    db.add_all([mat_coal, mat_waste])
    db.flush()

    # 3. Resources
    r_ex1 = models_resources.Resource(site_id=site.site_id, name="EX-01 (Liebherr 9800)", resource_type="Excavator", base_rate=3000, base_rate_units="t/h")
    r_ex2 = models_resources.Resource(site_id=site.site_id, name="EX-02 (CAT 6060)", resource_type="Excavator", base_rate=2500, base_rate_units="t/h")
    r_trk1 = models_resources.Resource(site_id=site.site_id, name="Fleet CAT 793 (x5)", resource_type="TruckFleet", base_rate=0, base_rate_units="t/h")
    db.add_all([r_ex1, r_ex2, r_trk1])
    db.flush()

    # 4. Activities & Areas (The Block Model)
    act_mine = models_resources.Activity(site_id=site.site_id, name="Mining", display_color="#3b82f6") # Blue
    db.add(act_mine)
    db.flush()

    areas = []
    # Create a 5x5 grid of blocks
    for x in range(5):
        for y in range(5):
            is_coal = (x + y) % 2 == 0
            area = models_resources.ActivityArea(
                site_id=site.site_id,
                activity_id=act_mine.activity_id,
                name=f"Block-{x}-{y}",
                geometry={"position": [x*50, 0, y*50], "size": [45, 10, 45]},
                priority=100 - (x+y),
                slice_states=[{"index": 0, "status": "Available", "quantity": 5000, "material": "Coal" if is_coal else "Waste"}]
            )
            areas.append(area)
    db.add_all(areas)

    # 5. Flow Network (Simple)
    net = models_flow.FlowNetwork(site_id=site.site_id, name="Main Haulage")
    db.add(net)
    db.flush()
    
    n_pit = models_flow.FlowNode(network_id=net.network_id, node_type="Source", name="Pit Exit")
    n_rom = models_flow.FlowNode(network_id=net.network_id, node_type="Stockpile", name="ROM Pad")
    n_dump = models_flow.FlowNode(network_id=net.network_id, node_type="Dump", name="Waste Dump")
    db.add_all([n_pit, n_rom, n_dump])
    db.flush()

    # 6. Schedule (Draft)
    sched = models_scheduling.ScheduleVersion(site_id=site.site_id, name="Q1 Base Schedule", status="Draft")
    db.add(sched)
    db.flush()

    # 7. Calendar
    from ..services import calendar_service
    cal = calendar_service.generate_standard_roster(db, site.site_id, datetime.utcnow())
    periods = cal.periods # List of period objects
    
    # Add Test Tasks
    t1 = models_scheduling.Task(
        schedule_version_id=sched.version_id,
        resource_id=r_ex1.resource_id,
        activity_id=act_mine.activity_id,
        period_id=periods[0].period_id, # First Shift
        activity_area_id=areas[0].area_id, 
        planned_quantity=2000
    )
    t2 = models_scheduling.Task(
        schedule_version_id=sched.version_id,
        resource_id=r_ex1.resource_id,
        activity_id=act_mine.activity_id,
        period_id=periods[1].period_id, # Second Shift
        activity_area_id=areas[1].area_id, 
        planned_quantity=2000
    )
    db.add_all([t1, t2])
    
    db.commit()
    return site.site_id
