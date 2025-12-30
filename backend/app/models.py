from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float

class EquipmentConfig(BaseModel):
    type_name: str
    capacity: float
    maintenance_interval: int
    fuel_consumption: float

class Shift(BaseModel):
    name: Literal['Morning', 'Afternoon', 'Night']
    start_hour: int
    end_hour: int
    target_production: float

class CoalType(BaseModel):
    name: str # e.g. "Seam 4 Lower"
    density: float # e.g. 1.5 t/m3
    quality_grade: str # e.g. "Export", "Eskom"

class QualitySpecs(BaseModel):
    ash: float = 0.0 # Percentage
    sulfur: float = 0.0 # Percentage
    cv: float = 0.0 # Calorific Value (MJ/kg)
    moisture: float = 0.0 # Percentage

class Block(BaseModel):
    block_id: str
    tonnes: float
    waste_tonnes: float
    quality: QualitySpecs
    status: Literal['available', 'mining', 'mined', 'blocked'] = 'blocked'
    dependencies: List[str] = [] # IDs of blocks that must be mined first
    location: Location

class Stockpile(BaseModel):
    stockpile_id: str
    current_tonnes: float
    current_quality: QualitySpecs
    target_quality: QualitySpecs
    capacity: float


class Truck(BaseModel):
    truck_id: int
    type_name: str
    capacity: float
    current_load: float
    load_type: Optional[str] = None # e.g. "Seam 4 Coal"
    load_quality: Optional[QualitySpecs] = None
    status: Literal['idle', 'loading', 'hauling', 'dumping', 'unloading', 'queueing', 'maintenance']
    current_location: Location
    assigned_shovel: int
    speed: float = 0.0
    heading: float = 0.0

class Shovel(BaseModel):
    shovel_id: int
    type_name: str
    location: Location
    status: Literal['operational', 'maintenance']
    current_queue: int
    mining_seam: str = "Seam 4" # Default seam
    current_block_id: Optional[str] = None # The block currently being mined

class SimulationConfig(BaseModel):
    num_trucks: int = 10
    num_shovels: int = 3
    max_trucks_per_shovel: int = 4
    time_scale: float = 1.0  # 1.0 = real time, 10.0 = 10x speed

class SimulationState(BaseModel):
    timestamp: datetime
    trucks: List[Truck]
    shovels: List[Shovel]
    blocks: List[Block] # New: Track block status
    stockpiles: List[Stockpile] # New: Track stockpile status
    total_production_tonnes: float
    total_fuel_consumed: float
    current_weather: str
    current_shift: str = "Morning"
    shift_progress_percent: float = 0.0
    shift_production_target: float = 10000.0

class OptimizationParams(BaseModel):
    population_size: int = 50
    generations: int = 100
    w_production: float = 1.0
    w_fuel: float = 0.5
