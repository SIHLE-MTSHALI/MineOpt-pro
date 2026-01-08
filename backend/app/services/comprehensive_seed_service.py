"""
Comprehensive Demo Data Seeding Service

Generates realistic demo data for MineOpt Pro including:
- 3 Coal Mining Sites
- 50+ Equipment pieces per site
- 90 days (3 months) of operational data
- GPS readings, haul cycles, shifts, blast patterns
- Geotechnical and environmental monitoring data
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import uuid
import math

# Import all domain models
from ..domain import (
    models_core, models_calendar, models_resource, models_flow, 
    models_scheduling, models_fleet, models_drill_blast,
    models_material_shift, models_geotech_safety
)

# Configuration
START_DATE = datetime.now() - timedelta(days=90)  # 3 months ago
END_DATE = datetime.now()
DAYS_OF_DATA = 90

# ============================================================================
# Site Configurations
# ============================================================================
COAL_SITES = [
    {
        "name": "Blackwater Open Cut Mine",
        "timezone": "Australia/Brisbane",
        "crs_epsg": 28354,
        "crs_name": "GDA94 / MGA zone 54",
        "coal_type": "Metallurgical Coal",
        "annual_capacity_mt": 12.5,
        "location": {"lat": -23.5833, "lon": 148.8833}
    },
    {
        "name": "Hunter Valley Operations",
        "timezone": "Australia/Sydney", 
        "crs_epsg": 28356,
        "crs_name": "GDA94 / MGA zone 56",
        "coal_type": "Thermal Coal",
        "annual_capacity_mt": 18.0,
        "location": {"lat": -32.3500, "lon": 151.1667}
    },
    {
        "name": "Mpumalanga Colliery",
        "timezone": "Africa/Johannesburg",
        "crs_epsg": 32735,
        "crs_name": "WGS 84 / UTM zone 35S",
        "coal_type": "Thermal Coal",
        "annual_capacity_mt": 8.5,
        "location": {"lat": -26.0833, "lon": 29.2500}
    }
]

# Equipment templates per site
EQUIPMENT_TEMPLATES = {
    "haul_truck": [
        {"model": "CAT 789D", "payload": 181, "base_rate": 220},
        {"model": "CAT 793F", "payload": 227, "base_rate": 280},
        {"model": "Komatsu 930E-5", "payload": 290, "base_rate": 320},
        {"model": "Liebherr T 284", "payload": 363, "base_rate": 400},
    ],
    "excavator": [
        {"model": "Hitachi EX3600-7", "bucket": 22, "base_rate": 3500},
        {"model": "Liebherr R 9800", "bucket": 42, "base_rate": 5000},
        {"model": "CAT 6060", "bucket": 34, "base_rate": 4200},
        {"model": "Komatsu PC8000-11", "bucket": 42, "base_rate": 5200},
    ],
    "dozer": [
        {"model": "CAT D10T2", "blade_width": 4.3, "base_rate": 800},
        {"model": "CAT D11T", "blade_width": 5.6, "base_rate": 1200},
        {"model": "Komatsu D475A-8", "blade_width": 5.4, "base_rate": 1100},
    ],
    "drill_rig": [
        {"model": "Atlas Copco DM45", "hole_diameter": 270, "max_depth": 60},
        {"model": "Sandvik DR410i", "hole_diameter": 311, "max_depth": 65},
        {"model": "Epiroc PV-271", "hole_diameter": 270, "max_depth": 55},
    ],
    "grader": [
        {"model": "CAT 16M3", "blade_width": 4.9, "base_rate": 150},
        {"model": "Komatsu GD825A-2", "blade_width": 4.3, "base_rate": 140},
    ],
    "water_cart": [
        {"model": "CAT 777G WC", "capacity_l": 75000, "base_rate": 100},
        {"model": "CAT 785D WC", "capacity_l": 100000, "base_rate": 120},
    ],
    "front_end_loader": [
        {"model": "CAT 994K", "bucket": 19, "base_rate": 2800},
        {"model": "Komatsu WA1200-6", "bucket": 20, "base_rate": 3000},
    ],
    "light_vehicle": [
        {"model": "Toyota Landcruiser 79", "purpose": "Supervision", "base_rate": 0},
        {"model": "Ford Ranger", "purpose": "Technical", "base_rate": 0},
    ]
}

# Fleet count per site type
FLEET_COUNTS = {
    "large": {  # >15 Mt/year
        "haul_truck": 25,
        "excavator": 4,
        "dozer": 5,
        "drill_rig": 3,
        "grader": 2,
        "water_cart": 4,
        "front_end_loader": 2,
        "light_vehicle": 8
    },
    "medium": {  # 8-15 Mt/year
        "haul_truck": 15,
        "excavator": 3,
        "dozer": 4,
        "drill_rig": 2,
        "grader": 2,
        "water_cart": 3,
        "front_end_loader": 1,
        "light_vehicle": 6
    },
    "small": {  # <8 Mt/year
        "haul_truck": 10,
        "excavator": 2,
        "dozer": 3,
        "drill_rig": 2,
        "grader": 1,
        "water_cart": 2,
        "front_end_loader": 1,
        "light_vehicle": 4
    }
}


def get_fleet_size(annual_mt):
    """Determine fleet size category based on annual capacity."""
    if annual_mt >= 15:
        return "large"
    elif annual_mt >= 8:
        return "medium"
    return "small"


def generate_fleet_number(eq_type, idx, site_abbr):
    """Generate fleet number like HT-01, EX-02."""
    prefixes = {
        "haul_truck": "HT",
        "excavator": "EX",
        "dozer": "DZ",
        "drill_rig": "DR",
        "grader": "GR",
        "water_cart": "WC",
        "front_end_loader": "LDR",
        "light_vehicle": "LV"
    }
    return f"{site_abbr}-{prefixes.get(eq_type, 'XX')}{idx+1:02d}"


def random_position_in_pit(base_lat, base_lon, radius_km=2):
    """Generate random position within pit area."""
    # Approx degrees for km at equator
    lat_offset = random.uniform(-radius_km, radius_km) / 111
    lon_offset = random.uniform(-radius_km, radius_km) / 111
    return {
        "latitude": base_lat + lat_offset,
        "longitude": base_lon + lon_offset,
        "elevation": random.uniform(-50, 20)  # Below and above ground level
    }


# ============================================================================
# Main Seeding Functions
# ============================================================================

def seed_sites(db: Session):
    """Create 3 coal mining sites."""
    sites = []
    for config in COAL_SITES:
        site = models_core.Site(
            name=config["name"],
            time_zone=config["timezone"],
            unit_system="Metric",
            crs_epsg=config["crs_epsg"],
            crs_name=config["crs_name"],
            default_quality_basis_preferences={
                "CV": "ARB", 
                "Ash": "ADB",
                "coal_type": config["coal_type"]
            }
        )
        db.add(site)
        sites.append((site, config))
    
    db.flush()
    return sites


def seed_materials_and_qualities(db: Session, site):
    """Create coal-specific materials and quality fields."""
    # Materials
    mat_coal_rom = models_resource.MaterialType(
        site_id=site.site_id,
        name="ROM Coal",
        category="ROM",
        reporting_group="Coal"
    )
    mat_coal_product = models_resource.MaterialType(
        site_id=site.site_id,
        name="Product Coal",
        category="Product",
        reporting_group="Coal"
    )
    mat_waste = models_resource.MaterialType(
        site_id=site.site_id,
        name="Overburden",
        category="Waste",
        reporting_group="Waste"
    )
    mat_interburden = models_resource.MaterialType(
        site_id=site.site_id,
        name="Interburden",
        category="Waste",
        reporting_group="Waste"
    )
    db.add_all([mat_coal_rom, mat_coal_product, mat_waste, mat_interburden])
    
    # Quality fields
    qualities = [
        models_resource.QualityField(
            site_id=site.site_id, name="CV_ARB", units="MJ/kg", basis="ARB",
            aggregation_rule="WeightedAverage", constraint_direction_default="Min"
        ),
        models_resource.QualityField(
            site_id=site.site_id, name="Ash_ADB", units="%", basis="ADB",
            aggregation_rule="WeightedAverage", constraint_direction_default="Max"
        ),
        models_resource.QualityField(
            site_id=site.site_id, name="Moisture_AR", units="%", basis="AR",
            aggregation_rule="WeightedAverage", constraint_direction_default="Max"
        ),
        models_resource.QualityField(
            site_id=site.site_id, name="Sulphur_ADB", units="%", basis="ADB",
            aggregation_rule="WeightedAverage", constraint_direction_default="Max"
        ),
        models_resource.QualityField(
            site_id=site.site_id, name="Volatile_ADB", units="%", basis="ADB",
            aggregation_rule="WeightedAverage", constraint_direction_default=None
        ),
    ]
    db.add_all(qualities)
    db.flush()
    
    return {"rom": mat_coal_rom, "product": mat_coal_product, "waste": mat_waste}


def seed_calendar(db: Session, site):
    """Create 90 days of shift periods (6 shifts per day = Day/Night for 3 crews)."""
    cal = models_calendar.Calendar(
        site_id=site.site_id,
        name="Production Calendar",
        period_granularity_type="Shift"
    )
    db.add(cal)
    db.flush()
    
    periods = []
    start_dt = START_DATE.replace(hour=6, minute=0, second=0, microsecond=0)
    
    crews = ["A", "B", "C"]
    for day_offset in range(DAYS_OF_DATA):
        for shift_num in range(2):  # Day and Night
            is_day = shift_num == 0
            crew_idx = (day_offset + shift_num) % 3
            p_start = start_dt + timedelta(days=day_offset, hours=12 * shift_num)
            p_end = p_start + timedelta(hours=12)
            
            period = models_calendar.Period(
                calendar_id=cal.calendar_id,
                name=f"{'Day' if is_day else 'Night'} Shift - Crew {crews[crew_idx]}",
                start_datetime=p_start,
                end_datetime=p_end,
                duration_hours=12.0,
                group_shift="Day" if is_day else "Night",
                group_day=p_start.strftime("%Y-%m-%d")
            )
            periods.append(period)
    
    db.add_all(periods)
    db.flush()
    return cal, periods


def seed_equipment(db: Session, site, site_config):
    """Create equipment fleet for a site."""
    fleet_size = get_fleet_size(site_config["annual_capacity_mt"])
    counts = FLEET_COUNTS[fleet_size]
    site_abbr = "".join([w[0] for w in site_config["name"].split()[:2]]).upper()
    
    equipment_list = []
    
    for eq_type, count in counts.items():
        templates = EQUIPMENT_TEMPLATES.get(eq_type, [])
        for i in range(count):
            template = random.choice(templates)
            fleet_num = generate_fleet_number(eq_type, i, site_abbr)
            
            # Random commission date (1-10 years ago)
            years_old = random.randint(1, 10)
            commission_date = datetime.now() - timedelta(days=365 * years_old)
            
            # Random status with realistic distribution
            status_weights = {
                "operating": 0.70,
                "standby": 0.15,
                "maintenance": 0.10,
                "breakdown": 0.03,
                "refueling": 0.02
            }
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]
            
            eq = models_fleet.Equipment(
                site_id=site.site_id,
                fleet_number=fleet_num,
                equipment_type=eq_type,
                make=template["model"].split()[0],
                model=template["model"],
                status=status,
                commissioned_date=commission_date,
                engine_hours=random.randint(5000, 50000),
                current_operator_id=None
            )
            equipment_list.append(eq)
    
    db.add_all(equipment_list)
    db.flush()
    return equipment_list


def seed_gps_readings(db: Session, equipment_list, site_config, sample_rate_minutes=30):
    """Generate GPS readings for equipment over 3 months."""
    readings = []
    base_lat = site_config["location"]["lat"]
    base_lon = site_config["location"]["lon"]
    
    # Only generate for mobile equipment
    mobile_types = ["haul_truck", "excavator", "dozer", "water_cart", "grader", "light_vehicle"]
    mobile_equipment = [e for e in equipment_list if e.equipment_type in mobile_types]
    
    # Generate readings at reduced frequency for performance
    # Every 30 minutes for haul trucks, every hour for others
    current_time = START_DATE
    reading_count = 0
    max_readings_per_equipment = 1000  # Limit to avoid massive data
    
    for eq in mobile_equipment:
        eq_readings = 0
        current_time = START_DATE
        pos = random_position_in_pit(base_lat, base_lon)
        heading = random.uniform(0, 360)
        
        interval_minutes = 30 if eq.equipment_type == "haul_truck" else 60
        
        while current_time <= END_DATE and eq_readings < max_readings_per_equipment:
            # Simulate movement
            if random.random() < 0.8:  # 80% chance equipment moves
                # Small random movement
                pos["latitude"] += random.uniform(-0.001, 0.001)
                pos["longitude"] += random.uniform(-0.001, 0.001)
                pos["elevation"] += random.uniform(-2, 2)
                heading = (heading + random.uniform(-30, 30)) % 360
            
            speed = 0 if eq.equipment_type == "excavator" else random.uniform(0, 40)
            
            reading = models_fleet.GPSReading(
                equipment_id=eq.equipment_id,
                timestamp=current_time,
                latitude=pos["latitude"],
                longitude=pos["longitude"],
                elevation=pos["elevation"],
                heading=heading,
                speed_kmh=speed,
                satellites=random.randint(8, 14),
                hdop=random.uniform(0.8, 2.0)
            )
            readings.append(reading)
            eq_readings += 1
            reading_count += 1
            
            current_time += timedelta(minutes=interval_minutes)
        
        # Reset for next equipment
        current_time = START_DATE
    
    # Batch insert for performance
    if readings:
        db.bulk_save_objects(readings)
        db.flush()
    
    return reading_count


def seed_haul_cycles(db: Session, equipment_list, site, materials, periods):
    """Generate haul cycle data for trucks."""
    trucks = [e for e in equipment_list if e.equipment_type == "haul_truck"]
    cycles = []
    
    for period in periods[:180]:  # First 90 days × 2 shifts
        shift_start = period.start_datetime
        
        for truck in trucks:
            # 8-15 cycles per truck per shift
            num_cycles = random.randint(8, 15)
            
            for cycle_num in range(num_cycles):
                cycle_start = shift_start + timedelta(minutes=random.randint(0, 600))
                
                # Realistic cycle times
                queue_time = random.uniform(1, 8)
                load_time = random.uniform(3, 6)
                haul_time = random.uniform(8, 20)
                dump_time = random.uniform(2, 4)
                return_time = haul_time * 0.8  # Return faster (empty)
                
                total_cycle = queue_time + load_time + haul_time + dump_time + return_time
                cycle_end = cycle_start + timedelta(minutes=total_cycle)
                
                # Random payload (90-105% of rated capacity)
                payload = truck.model.split()[-1] if hasattr(truck, 'model') else 200
                try:
                    rated_payload = int(''.join(filter(str.isdigit, str(payload)))) or 200
                except:
                    rated_payload = 200
                actual_payload = rated_payload * random.uniform(0.90, 1.05)
                
                # Material type (70% waste, 30% coal)
                is_coal = random.random() < 0.30
                
                cycle = models_fleet.HaulCycle(
                    equipment_id=truck.equipment_id,
                    cycle_start=cycle_start,
                    cycle_end=cycle_end,
                    source_location=f"Pit {random.randint(1, 3)}",
                    destination_location="ROM Pad" if is_coal else f"Dump {random.randint(1, 4)}",
                    material_type="ROM Coal" if is_coal else "Overburden",
                    payload_tonnes=round(actual_payload, 1),
                    queue_time_minutes=round(queue_time, 1),
                    load_time_minutes=round(load_time, 1),
                    haul_time_minutes=round(haul_time, 1),
                    dump_time_minutes=round(dump_time, 1),
                    return_time_minutes=round(return_time, 1),
                    distance_km=round(haul_time * 0.5, 1)  # ~30 km/h average
                )
                cycles.append(cycle)
    
    # Batch insert
    if cycles:
        db.bulk_save_objects(cycles)
        db.flush()
    
    return len(cycles)


def seed_blast_patterns(db: Session, site, site_config):
    """Generate blast patterns with drill holes and events."""
    patterns = []
    holes = []
    events = []
    
    num_patterns = 20 if site_config["annual_capacity_mt"] >= 12 else 12
    
    for i in range(num_patterns):
        # Pattern created at random time in past 3 months
        created_at = START_DATE + timedelta(days=random.randint(0, DAYS_OF_DATA - 10))
        
        # Status progression based on age
        days_old = (END_DATE - created_at).days
        if days_old > 21:
            status = "blasted"
        elif days_old > 14:
            status = "charged"
        elif days_old > 7:
            status = "drilled"
        else:
            status = "designed"
        
        pattern = models_drill_blast.BlastPattern(
            site_id=site.site_id,
            pattern_name=f"BP-{created_at.strftime('%Y%m%d')}-{i+1:03d}",
            bench_level=random.choice(["2850RL", "2840RL", "2830RL", "2820RL"]),
            status=status,
            designed_by="Chief Drill & Blast Engineer",
            designed_date=created_at,
            burden_m=random.uniform(4.5, 6.0),
            spacing_m=random.uniform(5.0, 7.0),
            hole_diameter_mm=random.choice([270, 311]),
            expected_fragmentation_p80=random.uniform(0.3, 0.6),
            explosive_type=random.choice(["ANFO", "Emulsion", "Heavy ANFO"]),
            total_explosives_kg=random.randint(5000, 25000),
            total_volume_bcm=random.randint(50000, 200000)
        )
        patterns.append(pattern)
    
    db.add_all(patterns)
    db.flush()
    
    # Generate holes for each pattern
    for pattern in patterns:
        num_holes = random.randint(60, 180)
        for h in range(num_holes):
            row = h // 15
            col = h % 15
            
            hole = models_drill_blast.DrillHole(
                pattern_id=pattern.pattern_id,
                hole_number=f"H{h+1:03d}",
                easting=1000 + col * pattern.spacing_m,
                northing=2000 + row * pattern.burden_m,
                collar_rl=float(pattern.bench_level.replace("RL", "")) if "RL" in pattern.bench_level else 2850,
                designed_depth=random.uniform(12, 18),
                actual_depth=random.uniform(11.5, 18.5) if pattern.status != "designed" else None,
                hole_status="drilled" if pattern.status in ["drilled", "charged", "blasted"] else "designed",
                water_depth=random.uniform(0, 3) if random.random() < 0.3 else None
            )
            holes.append(hole)
        
        # Create blast event if pattern was blasted
        if pattern.status == "blasted":
            blast_date = pattern.designed_date + timedelta(days=random.randint(14, 21))
            event = models_drill_blast.BlastEvent(
                pattern_id=pattern.pattern_id,
                blast_datetime=blast_date,
                blast_engineer="Senior Blast Engineer",
                weather_conditions=random.choice(["Clear", "Overcast", "Light Wind", "Windy"]),
                actual_fragmentation_p80=pattern.expected_fragmentation_p80 * random.uniform(0.9, 1.2),
                vibration_ppv=random.uniform(2, 15),
                overpressure_db=random.uniform(115, 135),
                notes="Blast completed as planned" if random.random() > 0.1 else "Minor deviation from plan"
            )
            events.append(event)
    
    db.bulk_save_objects(holes)
    db.bulk_save_objects(events)
    db.flush()
    
    return len(patterns), len(holes), len(events)


def seed_shifts_and_tickets(db: Session, site, periods, materials):
    """Generate shift records with load tickets."""
    shifts = []
    tickets = []
    
    for idx, period in enumerate(periods):
        # Use correct Shift model fields
        shift = models_material_shift.Shift(
            site_id=site.site_id,
            shift_name=period.name.split(" - ")[0] if " - " in period.name else "Day",
            shift_date=period.start_datetime,
            shift_number=(idx % 2) + 1,
            scheduled_start=period.start_datetime,
            scheduled_end=period.end_datetime,
            actual_start=period.start_datetime if period.end_datetime < datetime.now() else None,
            actual_end=period.end_datetime if period.end_datetime < datetime.now() else None,
            supervisor_name=random.choice([
                "John Smith", "Sarah Johnson", "Mike Brown", 
                "Emily Davis", "James Wilson", "Lisa Anderson"
            ]),
            crew_count=random.randint(25, 40),
            status="completed" if period.end_datetime < datetime.now() else "active"
        )
        shifts.append(shift)
    
    db.add_all(shifts)
    db.flush()
    
    # Generate load tickets for each shift
    for shift in shifts:
        if shift.scheduled_end > datetime.now():
            continue  # Skip future shifts
            
        num_tickets = random.randint(80, 150)
        
        for t in range(num_tickets):
            ticket_time = shift.scheduled_start + timedelta(
                minutes=random.randint(0, 11 * 60)
            )
            
            # 70% waste, 30% coal
            is_coal = random.random() < 0.30
            quantity = random.uniform(180, 280)
            
            # Use correct LoadTicket fields from models_material_shift
            ticket = models_material_shift.LoadTicket(
                site_id=site.site_id,
                shift_id=shift.shift_id,
                truck_fleet_number=f"HT{random.randint(1, 20):02d}",
                origin_type="dig_block",
                origin_name=f"Pit {random.randint(1, 3)} - Bench {random.randint(1, 5)}",
                destination_type="stockpile" if is_coal else "dump",
                destination_name="ROM Pad" if is_coal else f"Waste Dump {random.randint(1, 3)}",
                material_type=models_material_shift.MaterialType.ORE_HIGH_GRADE if is_coal else models_material_shift.MaterialType.OVERBURDEN,
                tonnes=round(quantity, 1),
                loaded_at=ticket_time,
                operator_name=f"Operator {random.randint(1, 30)}",
                is_valid=True
            )
            tickets.append(ticket)
    
    db.bulk_save_objects(tickets)
    db.flush()
    
    return len(shifts), len(tickets)


def seed_geotechnical_data(db: Session, site, site_config):
    """Generate slope monitoring prisms and readings."""
    prisms = []
    readings = []
    
    base_lat = site_config["location"]["lat"]
    base_lon = site_config["location"]["lon"]
    
    # 12-15 prisms per site
    num_prisms = random.randint(12, 15)
    
    for i in range(num_prisms):
        prism = models_geotech_safety.SlopeMonitoringPrism(
            site_id=site.site_id,
            prism_name=f"PRS-{i+1:03d}",
            location_easting=random.uniform(1000, 2000),
            location_northing=random.uniform(2000, 3000),
            location_rl=random.uniform(2800, 2900),
            install_date=START_DATE - timedelta(days=random.randint(30, 365)),
            status="active",
            monitoring_frequency="daily",
            alert_threshold_mm=25.0,
            critical_threshold_mm=50.0
        )
        prisms.append(prism)
    
    db.add_all(prisms)
    db.flush()
    
    # Generate daily readings for each prism
    for prism in prisms:
        cumulative_displacement = 0
        base_x, base_y, base_z = 0, 0, 0
        
        for day in range(DAYS_OF_DATA):
            reading_time = START_DATE + timedelta(days=day, hours=random.randint(6, 18))
            
            # Small random movement with occasional larger moves
            if random.random() < 0.05:  # 5% chance of larger movement
                dx = random.uniform(-3, 3)
                dy = random.uniform(-3, 3)
                dz = random.uniform(-2, 1)
            else:
                dx = random.uniform(-0.5, 0.5)
                dy = random.uniform(-0.5, 0.5)
                dz = random.uniform(-0.3, 0.1)
            
            base_x += dx
            base_y += dy
            base_z += dz
            cumulative_displacement = math.sqrt(base_x**2 + base_y**2 + base_z**2)
            
            reading = models_geotech_safety.PrismReading(
                prism_id=prism.prism_id,
                timestamp=reading_time,
                easting=prism.location_easting + base_x/1000,  # Convert mm to m
                northing=prism.location_northing + base_y/1000,
                rl=prism.location_rl + base_z/1000,
                delta_x_mm=dx,
                delta_y_mm=dy,
                delta_z_mm=dz,
                cumulative_displacement_mm=round(cumulative_displacement, 1),
                velocity_mm_per_day=round(math.sqrt(dx**2 + dy**2 + dz**2), 2)
            )
            readings.append(reading)
    
    db.bulk_save_objects(readings)
    db.flush()
    
    return len(prisms), len(readings)


def seed_environmental_data(db: Session, site, site_config):
    """Generate dust monitoring and environmental data."""
    monitors = []
    readings = []
    
    # 4 dust monitors per site
    monitor_locations = ["North Boundary", "South Pit Edge", "ROM Pad", "Main Haul Road"]
    
    for i, location in enumerate(monitor_locations):
        monitor = models_geotech_safety.DustMonitor(
            site_id=site.site_id,
            monitor_name=f"DM-{i+1:02d}",
            location_description=location,
            latitude=site_config["location"]["lat"] + random.uniform(-0.01, 0.01),
            longitude=site_config["location"]["lon"] + random.uniform(-0.01, 0.01),
            install_date=START_DATE - timedelta(days=180),
            status="active",
            pm10_limit=150,  # µg/m³
            pm25_limit=25
        )
        monitors.append(monitor)
    
    db.add_all(monitors)
    db.flush()
    
    # Generate hourly readings for each monitor
    for monitor in monitors:
        current_time = START_DATE
        
        while current_time <= END_DATE:
            # Dust levels vary by time of day and weather
            hour = current_time.hour
            
            # Higher during day operations
            if 6 <= hour <= 18:
                base_pm10 = random.uniform(40, 100)
                base_pm25 = random.uniform(10, 25)
            else:
                base_pm10 = random.uniform(15, 40)
                base_pm25 = random.uniform(5, 12)
            
            # Occasional spikes (blasting, dry windy conditions)
            if random.random() < 0.03:
                base_pm10 *= random.uniform(1.5, 3.0)
                base_pm25 *= random.uniform(1.3, 2.0)
            
            reading = models_geotech_safety.DustReading(
                monitor_id=monitor.monitor_id,
                measured_at=current_time,
                pm10=round(base_pm10, 1),
                pm25=round(base_pm25, 1),
                temperature_c=random.uniform(15, 35),
                humidity_percent=random.uniform(30, 80),
                wind_speed_ms=random.uniform(0, 15),
                wind_direction=random.uniform(0, 360)
            )
            readings.append(reading)
            
            current_time += timedelta(hours=1)
    
    db.bulk_save_objects(readings)
    db.flush()
    
    return len(monitors), len(readings)


def seed_flow_network(db: Session, site, materials):
    """Create flow network with stockpiles and plant."""
    network = models_flow.FlowNetwork(
        site_id=site.site_id,
        name="Main Production Network"
    )
    db.add(network)
    db.flush()
    
    # Nodes
    nodes = [
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="Source",
            name="Active Pit",
            location_geometry={"position": [0, 0, 0]}
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="Stockpile",
            name="ROM Pad A",
            location_geometry={"position": [500, 0, 50]},
            capacity_tonnes=80000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="Stockpile",
            name="ROM Pad B",
            location_geometry={"position": [600, 100, 50]},
            capacity_tonnes=60000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="WashPlant",
            name="CHPP",
            location_geometry={"position": [800, 50, 60]},
            capacity_tonnes_per_hour=2500
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="Stockpile",
            name="Product Stockpile",
            location_geometry={"position": [1000, 0, 70]},
            capacity_tonnes=120000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="Dump",
            name="Waste Dump North",
            location_geometry={"position": [-200, 300, -30]}
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            site_id=site.site_id,
            node_type="Dump",
            name="Waste Dump South",
            location_geometry={"position": [-200, -300, -30]}
        ),
    ]
    
    db.add_all(nodes)
    db.flush()
    
    return network, nodes


def seed_schedule_and_tasks(db: Session, site, periods, areas):
    """Create schedule version with tasks."""
    schedule = models_scheduling.ScheduleVersion(
        site_id=site.site_id,
        name="Q1 2026 Production Plan",
        status="Published"
    )
    db.add(schedule)
    db.flush()
    
    # Create tasks for each area-period combination
    tasks = []
    for area in areas[:9]:  # First 9 blocks
        for period in periods[:30]:  # First 30 periods (15 days)
            task = models_scheduling.Task(
                schedule_version_id=schedule.version_id,
                activity_area_id=area.area_id,
                period_id=period.period_id,
                planned_quantity=random.uniform(5000, 15000),
                rate_factor_applied=random.uniform(0.85, 1.0)
            )
            tasks.append(task)
    
    db.bulk_save_objects(tasks)
    db.flush()
    
    return schedule


def seed_activity_areas(db: Session, site, activity):
    """Create mining blocks as activity areas."""
    areas = []
    
    # 16 blocks (4x4 grid)
    for x in range(4):
        for y in range(4):
            is_coal = (x + y) % 2 == 0
            
            slice_state = [{
                "index": 0,
                "status": "Available",
                "quantity": random.randint(50000, 200000),
                "material_type": "ROM Coal" if is_coal else "Overburden",
                "qualities": {
                    "CV_ARB": round(random.uniform(22, 26), 1) if is_coal else 0,
                    "Ash_ADB": round(random.uniform(10, 16), 1) if is_coal else 80,
                    "Moisture_AR": round(random.uniform(8, 12), 1) if is_coal else 0
                }
            }]
            
            area = models_resource.ActivityArea(
                site_id=site.site_id,
                activity_id=activity.activity_id,
                name=f"Block-{chr(65 + x)}{y + 1}",
                geometry={"position": [x * 80, 0, y * 80], "size": [70, 15, 70]},
                slice_states=slice_state,
                priority=random.randint(1, 10),
                bench_level=f"{2850 - y * 10}RL"
            )
            areas.append(area)
    
    db.add_all(areas)
    db.flush()
    
    return areas


def seed_all(db: Session):
    """Main function to seed all comprehensive demo data."""
    print("Starting comprehensive demo data seeding...")
    results = {
        "sites": [],
        "equipment_count": 0,
        "gps_readings": 0,
        "haul_cycles": 0,
        "blast_patterns": 0,
        "shifts": 0,
        "load_tickets": 0,
        "prism_readings": 0,
        "dust_readings": 0
    }
    
    # Seed each site
    sites = seed_sites(db)
    
    for site, config in sites:
        print(f"Seeding data for: {config['name']}")
        
        # Core configuration
        materials = seed_materials_and_qualities(db, site)
        calendar, periods = seed_calendar(db, site)
        
        # Activity for mining
        activity = models_resource.Activity(
            site_id=site.site_id,
            name="Mining",
            display_color="#3b82f6"
        )
        db.add(activity)
        db.flush()
        
        # Activity areas (blocks)
        areas = seed_activity_areas(db, site, activity)
        
        # Flow network
        network, nodes = seed_flow_network(db, site, materials)
        
        # Equipment
        equipment = seed_equipment(db, site, config)
        results["equipment_count"] += len(equipment)
        
        # GPS Readings
        gps_count = seed_gps_readings(db, equipment, config)
        results["gps_readings"] += gps_count
        
        # Haul Cycles
        cycle_count = seed_haul_cycles(db, equipment, site, materials, periods)
        results["haul_cycles"] += cycle_count
        
        # Blast Patterns
        patterns, holes, events = seed_blast_patterns(db, site, config)
        results["blast_patterns"] += patterns
        
        # Shifts and Tickets
        shift_count, ticket_count = seed_shifts_and_tickets(db, site, periods, materials)
        results["shifts"] += shift_count
        results["load_tickets"] += ticket_count
        
        # Geotechnical
        prisms, prism_readings = seed_geotechnical_data(db, site, config)
        results["prism_readings"] += prism_readings
        
        # Environmental
        monitors, dust_readings = seed_environmental_data(db, site, config)
        results["dust_readings"] += dust_readings
        
        # Schedule
        schedule = seed_schedule_and_tasks(db, site, periods, areas)
        
        results["sites"].append({
            "site_id": site.site_id,
            "name": config["name"]
        })
        
        db.flush()
    
    db.commit()
    print("Comprehensive demo data seeding complete!")
    
    return results
