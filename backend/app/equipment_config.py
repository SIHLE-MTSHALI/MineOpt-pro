from dataclasses import dataclass
from typing import Dict, List

@dataclass
class LoaderConfig:
    type_name: str
    bucket_capacity: float  # in cubic meters
    cycle_time: float      # in seconds
    maintenance_interval: int  # in hours
    fuel_consumption: float    # L/hour

@dataclass
class TruckConfig:
    type_name: str
    capacity: float        # in tons
    empty_weight: float    # in tons
    max_speed_loaded: float    # km/h
    max_speed_empty: float     # km/h
    fuel_consumption_loaded: float  # L/km
    fuel_consumption_empty: float   # L/km
    maintenance_interval: int      # in hours

# Define loader configurations
LOADER_TYPES: Dict[str, LoaderConfig] = {
    'small_excavator': LoaderConfig(
        type_name='CAT 336',
        bucket_capacity=2.5,
        cycle_time=25,
        maintenance_interval=250,
        fuel_consumption=28
    ),
    'medium_excavator': LoaderConfig(
        type_name='CAT 349',
        bucket_capacity=3.5,
        cycle_time=28,
        maintenance_interval=250,
        fuel_consumption=35
    ),
    'large_excavator': LoaderConfig(
        type_name='CAT 395',
        bucket_capacity=6.0,
        cycle_time=32,
        maintenance_interval=250,
        fuel_consumption=45
    ),
    'excavator_870': LoaderConfig(
        type_name='CAT 870',
        bucket_capacity=7.5,
        cycle_time=35,
        maintenance_interval=300,
        fuel_consumption=52
    ),
    'excavator_2600': LoaderConfig(
        type_name='CAT 2600',
        bucket_capacity=15.0,
        cycle_time=40,
        maintenance_interval=350,
        fuel_consumption=85
    ),
    'face_shovel_2500': LoaderConfig(
        type_name='CAT 2500',
        bucket_capacity=13.0,
        cycle_time=38,
        maintenance_interval=300,
        fuel_consumption=75
    ),
    'face_shovel_2600': LoaderConfig(
        type_name='CAT 2600',
        bucket_capacity=16.0,
        cycle_time=42,
        maintenance_interval=350,
        fuel_consumption=90
    ),
    'face_shovel_3600': LoaderConfig(
        type_name='CAT 3600',
        bucket_capacity=20.0,
        cycle_time=45,
        maintenance_interval=400,
        fuel_consumption=110
    ),
    'wheel_loader_small': LoaderConfig(
        type_name='CAT 966',
        bucket_capacity=4.0,
        cycle_time=45,
        maintenance_interval=200,
        fuel_consumption=25
    ),
    'wheel_loader_large': LoaderConfig(
        type_name='CAT 992',
        bucket_capacity=12.0,
        cycle_time=55,
        maintenance_interval=200,
        fuel_consumption=55
    ),
    'wheel_loader_993': LoaderConfig(
        type_name='CAT 993',
        bucket_capacity=14.5,
        cycle_time=58,
        maintenance_interval=250,
        fuel_consumption=65
    ),
    'wheel_loader_994': LoaderConfig(
        type_name='CAT 994',
        bucket_capacity=19.0,
        cycle_time=62,
        maintenance_interval=300,
        fuel_consumption=85
    )
}

# Define truck configurations
TRUCK_TYPES: Dict[str, TruckConfig] = {
    'articulated_small': TruckConfig(
        type_name='Bell B30E',
        capacity=28,
        empty_weight=22.7,
        max_speed_loaded=40,
        max_speed_empty=50,
        fuel_consumption_loaded=0.85,
        fuel_consumption_empty=0.55,
        maintenance_interval=250
    ),
    'articulated_medium': TruckConfig(
        type_name='Bell B45E',
        capacity=41,
        empty_weight=32.5,
        max_speed_loaded=35,
        max_speed_empty=45,
        fuel_consumption_loaded=1.0,
        fuel_consumption_empty=0.65,
        maintenance_interval=250
    ),
    'rigid_medium': TruckConfig(
        type_name='CAT 777E',
        capacity=100,
        empty_weight=64,
        max_speed_loaded=30,
        max_speed_empty=40,
        fuel_consumption_loaded=1.4,
        fuel_consumption_empty=0.9,
        maintenance_interval=300
    ),
    'rigid_large': TruckConfig(
        type_name='CAT 785D',
        capacity=140,
        empty_weight=87,
        max_speed_loaded=25,
        max_speed_empty=35,
        fuel_consumption_loaded=1.8,
        fuel_consumption_empty=1.1,
        maintenance_interval=300
    ),
    'rigid_789C': TruckConfig(
        type_name='CAT 789C',
        capacity=177,
        empty_weight=98,
        max_speed_loaded=23,
        max_speed_empty=33,
        fuel_consumption_loaded=2.0,
        fuel_consumption_empty=1.3,
        maintenance_interval=350
    ),
    'rigid_789D': TruckConfig(
        type_name='CAT 789D',
        capacity=181,
        empty_weight=99,
        max_speed_loaded=23,
        max_speed_empty=33,
        fuel_consumption_loaded=2.1,
        fuel_consumption_empty=1.35,
        maintenance_interval=350
    ),
    'rigid_793C': TruckConfig(
        type_name='CAT 793C',
        capacity=218,
        empty_weight=123,
        max_speed_loaded=21,
        max_speed_empty=31,
        fuel_consumption_loaded=2.4,
        fuel_consumption_empty=1.6,
        maintenance_interval=400
    ),
    'rigid_793D': TruckConfig(
        type_name='CAT 793D',
        capacity=227,
        empty_weight=125,
        max_speed_loaded=21,
        max_speed_empty=31,
        fuel_consumption_loaded=2.5,
        fuel_consumption_empty=1.65,
        maintenance_interval=400
    )
}

# Environmental factors affecting equipment performance
class EnvironmentalFactors:
    @staticmethod
    def get_road_condition_factor(condition: str) -> float:
        """Return speed reduction factor based on road condition"""
        factors = {
            'excellent': 1.0,
            'good': 0.9,
            'fair': 0.75,
            'poor': 0.6,
            'very_poor': 0.4
        }
        return factors.get(condition, 0.75)
    
    @staticmethod
    def get_weather_factor(condition: str) -> float:
        """Return speed reduction factor based on weather condition"""
        factors = {
            'clear': 1.0,
            'light_rain': 0.9,
            'heavy_rain': 0.7,
            'fog': 0.6,
            'storm': 0.4
        }
        return factors.get(condition, 1.0)
    
    @staticmethod
    def get_gradient_factor(gradient_percent: float) -> float:
        """Return speed reduction factor based on road gradient"""
        if gradient_percent <= 2:
            return 1.0
        elif gradient_percent <= 5:
            return 0.85
        elif gradient_percent <= 8:
            return 0.7
        elif gradient_percent <= 10:
            return 0.5
        else:
            return 0.4  # Steep grades above 10%