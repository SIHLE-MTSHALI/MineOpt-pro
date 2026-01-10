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
    
    # Map string types to EquipmentType enum values
    type_map = {
        "haul_truck": models_fleet.EquipmentType.HAUL_TRUCK,
        "excavator": models_fleet.EquipmentType.EXCAVATOR,
        "dozer": models_fleet.EquipmentType.DOZER,
        "drill_rig": models_fleet.EquipmentType.DRILL_RIG,
        "grader": models_fleet.EquipmentType.GRADER,
        "water_cart": models_fleet.EquipmentType.WATER_CART,
        "front_end_loader": models_fleet.EquipmentType.FRONT_END_LOADER,
        "light_vehicle": models_fleet.EquipmentType.LIGHT_VEHICLE,
    }
    
    for eq_type, count in counts.items():
        templates = EQUIPMENT_TEMPLATES.get(eq_type, [])
        for i in range(count):
            template = random.choice(templates) if templates else {"model": "Generic Equipment"}
            fleet_num = generate_fleet_number(eq_type, i, site_abbr)
            
            # Random commission year (1-10 years ago)
            years_old = random.randint(1, 10)
            commission_year = datetime.now().year - years_old
            
            # Random status with realistic distribution
            status_weights = {
                models_fleet.EquipmentStatus.OPERATING: 0.70,
                models_fleet.EquipmentStatus.STANDBY: 0.15,
                models_fleet.EquipmentStatus.MAINTENANCE: 0.10,
                models_fleet.EquipmentStatus.BREAKDOWN: 0.03,
                models_fleet.EquipmentStatus.REFUELING: 0.02
            }
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]
            
            eq = models_fleet.Equipment(
                site_id=site.site_id,
                fleet_number=fleet_num,
                name=f"{template['model']} {fleet_num}",
                equipment_type=type_map.get(eq_type, models_fleet.EquipmentType.OTHER),
                manufacturer=template["model"].split()[0],
                model=template["model"],
                status=status,
                year=commission_year,
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
    
    # Only generate for mobile equipment (using enum values)
    mobile_types = [
        models_fleet.EquipmentType.HAUL_TRUCK,
        models_fleet.EquipmentType.EXCAVATOR,
        models_fleet.EquipmentType.DOZER,
        models_fleet.EquipmentType.WATER_CART,
        models_fleet.EquipmentType.GRADER,
        models_fleet.EquipmentType.LIGHT_VEHICLE
    ]
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
        
        interval_minutes = 30 if eq.equipment_type == models_fleet.EquipmentType.HAUL_TRUCK else 60
        
        while current_time <= END_DATE and eq_readings < max_readings_per_equipment:
            # Simulate movement
            if random.random() < 0.8:  # 80% chance equipment moves
                # Small random movement
                pos["latitude"] += random.uniform(-0.001, 0.001)
                pos["longitude"] += random.uniform(-0.001, 0.001)
                pos["elevation"] += random.uniform(-2, 2)
                heading = (heading + random.uniform(-30, 30)) % 360
            
            speed = 0 if eq.equipment_type == models_fleet.EquipmentType.EXCAVATOR else random.uniform(0, 40)
            
            reading = models_fleet.GPSReading(
                equipment_id=eq.equipment_id,
                timestamp=current_time,
                latitude=pos["latitude"],
                longitude=pos["longitude"],
                altitude=pos["elevation"],
                heading=heading,
                speed_kmh=speed,
                num_satellites=random.randint(8, 14),
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
    trucks = [e for e in equipment_list if e.equipment_type == models_fleet.EquipmentType.HAUL_TRUCK]
    cycles = []
    
    for period in periods[:180]:  # First 90 days × 2 shifts
        shift_start = period.start_datetime
        
        for truck in trucks:
            # 8-15 cycles per truck per shift
            num_cycles = random.randint(8, 15)
            
            for cycle_num in range(num_cycles):
                cycle_start = shift_start + timedelta(minutes=random.randint(0, 600))
                
                # Realistic cycle times (in seconds for model)
                queue_time_sec = random.uniform(60, 480)  # 1-8 min
                load_time_sec = random.uniform(180, 360)   # 3-6 min
                haul_time_sec = random.uniform(480, 1200)   # 8-20 min
                dump_time_sec = random.uniform(120, 240)    # 2-4 min
                return_time_sec = haul_time_sec * 0.8  # Return faster (empty)
                
                total_cycle_sec = queue_time_sec + load_time_sec + haul_time_sec + dump_time_sec + return_time_sec
                cycle_end = cycle_start + timedelta(seconds=total_cycle_sec)
                
                # Random payload (90-105% of rated capacity)
                payload = truck.model.split()[-1] if hasattr(truck, 'model') else 200
                try:
                    rated_payload = int(''.join(filter(str.isdigit, str(payload)))) or 200
                except:
                    rated_payload = 200
                actual_payload = rated_payload * random.uniform(0.90, 1.05)
                
                # Material type (70% waste, 30% coal)
                is_coal = random.random() < 0.30
                
                # Calculate distance (assuming ~30 km/h average speed)
                haul_distance = (haul_time_sec / 3600) * 30  # km
                return_distance = (return_time_sec / 3600) * 35  # km
                
                cycle = models_fleet.HaulCycle(
                    equipment_id=truck.equipment_id,
                    site_id=site.site_id,
                    cycle_start=cycle_start,
                    cycle_end=cycle_end,
                    source_name=f"Pit {random.randint(1, 3)}",
                    destination_name="ROM Pad" if is_coal else f"Dump {random.randint(1, 4)}",
                    material_type="ROM Coal" if is_coal else "Overburden",
                    payload_tonnes=round(actual_payload, 1),
                    queue_at_loader_sec=round(queue_time_sec, 1),
                    loading_sec=round(load_time_sec, 1),
                    travel_loaded_sec=round(haul_time_sec, 1),
                    queue_at_dump_sec=round(queue_time_sec * 0.3, 1),
                    dumping_sec=round(dump_time_sec, 1),
                    travel_empty_sec=round(return_time_sec, 1),
                    total_cycle_sec=round(total_cycle_sec, 1),
                    travel_loaded_km=round(haul_distance, 1),
                    travel_empty_km=round(return_distance, 1),
                    total_distance_km=round(haul_distance + return_distance, 1)
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
            status = "fired"
        elif days_old > 14:
            status = "loaded"
        elif days_old > 7:
            status = "drilled"
        else:
            status = "approved"
        
        # Pattern dimensions
        burden = random.uniform(4.5, 6.0)
        spacing = random.uniform(5.0, 7.0)
        num_rows = random.randint(4, 8)
        num_holes_per_row = random.randint(10, 20)
        hole_depth = random.uniform(12, 18)
        
        pattern = models_drill_blast.BlastPattern(
            site_id=site.site_id,
            bench_name=random.choice(["2850RL", "2840RL", "2830RL", "2820RL"]),
            block_name=f"Block-{created_at.strftime('%Y%m%d')}-{i+1:03d}",
            pattern_type="rectangular",
            status=status,
            designed_by="Chief Drill & Blast Engineer",
            designed_at=created_at,
            burden=burden,
            spacing=spacing,
            num_rows=num_rows,
            num_holes_per_row=num_holes_per_row,
            hole_diameter_mm=random.choice([270.0, 311.0]),
            hole_depth_m=hole_depth,
            subdrill_m=0.5,
            stemming_height_m=3.0,
            explosive_type=random.choice([
                models_drill_blast.ExplosiveType.ANFO,
                models_drill_blast.ExplosiveType.EMULSION,
                models_drill_blast.ExplosiveType.HEAVY_ANFO
            ]),
            powder_factor_kg_bcm=random.uniform(0.3, 0.6),
            orientation_degrees=random.uniform(0, 90),
            origin_x=1000.0,
            origin_y=2000.0,
            origin_z=float(random.choice([2850, 2840, 2830, 2820]))
        )
        patterns.append(pattern)
    
    db.add_all(patterns)
    db.flush()
    
    # Generate holes for each pattern
    for pattern in patterns:
        total_holes = pattern.num_rows * pattern.num_holes_per_row
        for h in range(total_holes):
            row = h // pattern.num_holes_per_row
            col = h % pattern.num_holes_per_row
            
            # Determine hole status based on pattern status
            if pattern.status == "fired":
                hole_status = models_drill_blast.DrillHoleStatus.DETONATED
            elif pattern.status == "loaded":
                hole_status = models_drill_blast.DrillHoleStatus.LOADED
            elif pattern.status == "drilled":
                hole_status = models_drill_blast.DrillHoleStatus.DRILLED
            else:
                hole_status = models_drill_blast.DrillHoleStatus.PLANNED
            
            hole = models_drill_blast.DrillHole(
                pattern_id=pattern.pattern_id,
                hole_number=h + 1,  # Integer, not string
                row_number=row + 1,
                hole_in_row=col + 1,
                design_x=pattern.origin_x + col * pattern.spacing,
                design_y=pattern.origin_y + row * pattern.burden,
                design_z=pattern.origin_z,
                design_depth_m=pattern.hole_depth_m,
                design_angle_degrees=90,  # Vertical
                design_diameter_mm=pattern.hole_diameter_mm,
                actual_depth_m=pattern.hole_depth_m * random.uniform(0.95, 1.05) if pattern.status != "approved" else None,
                status=hole_status,
                water_present=random.random() < 0.15,  # 15% chance of water
                charge_weight_kg=random.uniform(80, 150) if hole_status in [models_drill_blast.DrillHoleStatus.LOADED, models_drill_blast.DrillHoleStatus.DETONATED] else None
            )
            holes.append(hole)
        
        # Create blast event if pattern was fired
        if pattern.status == "fired":
            blast_date = pattern.designed_at + timedelta(days=random.randint(14, 21))
            event = models_drill_blast.BlastEvent(
                pattern_id=pattern.pattern_id,
                site_id=site.site_id,
                blast_number=f"BLAST-{blast_date.strftime('%Y%m%d')}-{i+1:03d}",
                blast_date=blast_date,
                scheduled_time=blast_date,
                actual_fire_time=blast_date + timedelta(minutes=random.randint(-10, 30)),
                total_holes=total_holes,
                total_explosive_kg=random.randint(5000, 25000),
                total_volume_bcm=random.randint(50000, 200000),
                powder_factor_kg_bcm=random.uniform(0.3, 0.6),
                wind_speed_kmh=random.uniform(5, 25),
                wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                max_ppv_mm_s=random.uniform(2, 15),
                max_overpressure_db=random.uniform(115, 135),
                avg_fragment_size_cm=random.uniform(20, 50),
                fragmentation_rating=random.choice(["good", "acceptable", "poor"]),
                shotfirer_name="Senior Blast Engineer",
                status="completed",
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
        # Generate position
        initial_x = random.uniform(1000, 2000)
        initial_y = random.uniform(2000, 3000)
        initial_z = random.uniform(2800, 2900)
        
        prism = models_geotech_safety.SlopeMonitoringPrism(
            site_id=site.site_id,
            prism_name=f"PRS-{i+1:03d}",
            location=f"Bench {int(initial_z // 10) * 10}",
            initial_x=initial_x,
            initial_y=initial_y,
            initial_z=initial_z,
            current_x=initial_x,
            current_y=initial_y,
            current_z=initial_z,
            installed_at=START_DATE - timedelta(days=random.randint(30, 365)),
            warning_threshold_mm=25.0,
            critical_threshold_mm=50.0,
            alert_status="normal",
            is_active=True
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
                measured_at=reading_time,
                x=prism.initial_x + base_x/1000,  # Convert mm to m
                y=prism.initial_y + base_y/1000,
                z=prism.initial_z + base_z/1000,
                delta_x=dx,
                delta_y=dy,
                delta_z=dz,
                total_displacement_mm=round(cumulative_displacement, 1),
                displacement_rate_mm_day=round(math.sqrt(dx**2 + dy**2 + dz**2), 2)
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
    wind_directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    
    for i, location in enumerate(monitor_locations):
        monitor = models_geotech_safety.DustMonitor(
            site_id=site.site_id,
            name=f"DM-{i+1:02d}",
            location=location,
            monitor_type="continuous",
            easting=random.uniform(1000, 2000),
            northing=random.uniform(2000, 3000),
            pm10_threshold_ug_m3=150,  # µg/m³
            pm25_threshold_ug_m3=25,
            is_active=True
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
                pm10_ug_m3=round(base_pm10, 1),
                pm25_ug_m3=round(base_pm25, 1),
                pm10_exceeded=base_pm10 > monitor.pm10_threshold_ug_m3,
                pm25_exceeded=base_pm25 > monitor.pm25_threshold_ug_m3,
                temperature_c=random.uniform(15, 35),
                humidity_percent=random.uniform(30, 80),
                wind_speed_kmh=random.uniform(0, 50),
                wind_direction=random.choice(wind_directions)
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
            node_type="Source",
            name="Active Pit",
            location_geometry={"position": [0, 0, 0]}
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            node_type="Stockpile",
            name="ROM Pad A",
            location_geometry={"position": [500, 0, 50]},
            capacity_tonnes=80000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            node_type="Stockpile",
            name="ROM Pad B",
            location_geometry={"position": [600, 100, 50]},
            capacity_tonnes=60000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            node_type="WashPlant",
            name="CHPP",
            location_geometry={"position": [800, 50, 60]},
            capacity_tonnes=50000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            node_type="Stockpile",
            name="Product Stockpile",
            location_geometry={"position": [1000, 0, 70]},
            capacity_tonnes=120000
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
            node_type="Dump",
            name="Waste Dump North",
            location_geometry={"position": [-200, 300, -30]}
        ),
        models_flow.FlowNode(
            network_id=network.network_id,
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
    import sys
    
    def log_progress(step, total, message):
        """Print progress with visual bar."""
        percent = int((step / total) * 100)
        bar_width = 30
        filled = int(bar_width * step / total)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\r[{bar}] {percent:3d}% | Step {step}/{total}: {message}", end="", flush=True)
        if step == total:
            print()  # Newline at end
    
    total_steps = 33  # 11 steps per site × 3 sites
    current_step = 0
    
    print("\n" + "="*60)
    print("🏗️  COMPREHENSIVE DEMO DATA SEEDING")
    print("="*60)
    print(f"📅 Generating {DAYS_OF_DATA} days of operational data...")
    print(f"🏭 Creating {len(COAL_SITES)} coal mining sites...")
    print("="*60 + "\n")
    
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
    
    for site_idx, (site, config) in enumerate(sites):
        print(f"\n📍 Site {site_idx + 1}/3: {config['name']}")
        print("-" * 50)
        
        # Step 1: Core configuration
        current_step += 1
        log_progress(current_step, total_steps, f"Materials & qualities")
        materials = seed_materials_and_qualities(db, site)
        
        # Step 2: Calendar
        current_step += 1
        log_progress(current_step, total_steps, f"Calendar ({DAYS_OF_DATA} days)")
        calendar, periods = seed_calendar(db, site)
        
        # Activity for mining
        activity = models_resource.Activity(
            site_id=site.site_id,
            name="Mining",
            display_color="#3b82f6"
        )
        db.add(activity)
        db.flush()
        
        # Step 3: Activity areas (blocks)
        current_step += 1
        log_progress(current_step, total_steps, f"Mining blocks (16 blocks)")
        areas = seed_activity_areas(db, site, activity)
        
        # Step 4: Flow network
        current_step += 1
        log_progress(current_step, total_steps, f"Flow network & nodes")
        network, nodes = seed_flow_network(db, site, materials)
        
        # Step 5: Equipment
        current_step += 1
        log_progress(current_step, total_steps, f"Equipment fleet")
        equipment = seed_equipment(db, site, config)
        results["equipment_count"] += len(equipment)
        print(f" → {len(equipment)} pieces")
        
        # Step 6: GPS Readings
        current_step += 1
        log_progress(current_step, total_steps, f"GPS readings")
        gps_count = seed_gps_readings(db, equipment, config)
        results["gps_readings"] += gps_count
        print(f" → {gps_count:,} readings")
        
        # Step 7: Haul Cycles
        current_step += 1
        log_progress(current_step, total_steps, f"Haul cycles")
        cycle_count = seed_haul_cycles(db, equipment, site, materials, periods)
        results["haul_cycles"] += cycle_count
        print(f" → {cycle_count:,} cycles")
        
        # Step 8: Blast Patterns
        current_step += 1
        log_progress(current_step, total_steps, f"Blast patterns & holes")
        patterns, holes, events = seed_blast_patterns(db, site, config)
        results["blast_patterns"] += patterns
        print(f" → {patterns} patterns, {holes:,} holes")
        
        # Step 9: Shifts and Tickets
        current_step += 1
        log_progress(current_step, total_steps, f"Shifts & load tickets")
        shift_count, ticket_count = seed_shifts_and_tickets(db, site, periods, materials)
        results["shifts"] += shift_count
        results["load_tickets"] += ticket_count
        print(f" → {shift_count} shifts, {ticket_count:,} tickets")
        
        # Step 10: Geotechnical
        current_step += 1
        log_progress(current_step, total_steps, f"Prism monitoring data")
        prisms, prism_readings = seed_geotechnical_data(db, site, config)
        results["prism_readings"] += prism_readings
        print(f" → {prisms} prisms, {prism_readings:,} readings")
        
        # Step 11: Environmental
        current_step += 1
        log_progress(current_step, total_steps, f"Environmental monitoring")
        monitors, dust_readings = seed_environmental_data(db, site, config)
        results["dust_readings"] += dust_readings
        print(f" → {monitors} monitors, {dust_readings:,} readings")
        
        # Schedule
        schedule = seed_schedule_and_tasks(db, site, periods, areas)
        
        results["sites"].append({
            "site_id": site.site_id,
            "name": config["name"]
        })
        
        db.flush()
        print(f"✅ {config['name']} complete!\n")
    
    db.commit()
    
    # Final summary
    print("\n" + "="*60)
    print("🎉 SEEDING COMPLETE!")
    print("="*60)
    print(f"   Sites created:      {len(results['sites'])}")
    print(f"   Equipment:          {results['equipment_count']:,}")
    print(f"   GPS readings:       {results['gps_readings']:,}")
    print(f"   Haul cycles:        {results['haul_cycles']:,}")
    print(f"   Blast patterns:     {results['blast_patterns']}")
    print(f"   Shifts:             {results['shifts']}")
    print(f"   Load tickets:       {results['load_tickets']:,}")
    print(f"   Prism readings:     {results['prism_readings']:,}")
    print(f"   Dust readings:      {results['dust_readings']:,}")
    print("="*60 + "\n")
    
    return results

