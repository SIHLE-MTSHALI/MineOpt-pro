import pandas as pd
import numpy as np
from faker import Faker
import json
from backend.app.equipment_config import LOADER_TYPES, TRUCK_TYPES, EnvironmentalFactors
import random

fake = Faker()

def generate_gps_coordinates():
    # Generating coordinates within the Witbank coal mining region
    # Centered around -25.8772° S, 29.2302° E (Witbank)
    base_lat = -25.8772
    base_lon = 29.2302
    
    lat = base_lat + np.random.uniform(-0.05, 0.05)
    lon = base_lon + np.random.uniform(-0.05, 0.05)
    return lat, lon

def generate_route_data(start_point, end_point):
    """Generate route characteristics including road conditions and gradients"""
    return {
        'distance': np.sqrt((end_point['latitude'] - start_point['latitude'])**2 + 
                           (end_point['longitude'] - start_point['longitude'])**2) * 111,  # km
        'road_condition': np.random.choice(['excellent', 'good', 'fair', 'poor', 'very_poor'],
                                         p=[0.1, 0.3, 0.3, 0.2, 0.1]),
        'average_gradient': np.random.uniform(0, 12),  # percent
        'weather_condition': np.random.choice(['clear', 'light_rain', 'heavy_rain', 'fog', 'storm'],
                                            p=[0.6, 0.2, 0.1, 0.05, 0.05])
    }

def generate_truck_data(num_trucks=10):
    trucks = []
    for i in range(num_trucks):
        lat, lon = generate_gps_coordinates()
        truck_type = random.choice(list(TRUCK_TYPES.values()))
        truck = {
            'truck_id': i + 1,
            'type_name': truck_type.type_name,
            'capacity': truck_type.capacity,
            'empty_weight': truck_type.empty_weight,
            'max_speed_loaded': truck_type.max_speed_loaded,
            'max_speed_empty': truck_type.max_speed_empty,
            'fuel_consumption_loaded': truck_type.fuel_consumption_loaded,
            'fuel_consumption_empty': truck_type.fuel_consumption_empty,
            'current_load': 0,
            'status': np.random.choice(['idle', 'loading', 'hauling', 'dumping']),
            'current_location': {
                'latitude': lat,
                'longitude': lon
            },
            'assigned_shovel': np.random.randint(1, 4),
            'maintenance_status': np.random.choice(['operational', 'maintenance_due', 'in_maintenance'], 
                                                 p=[0.8, 0.15, 0.05]),
            'maintenance_interval': truck_type.maintenance_interval
        }
        trucks.append(truck)
    return pd.DataFrame(trucks)

def generate_shovel_data(num_shovels=3):
    shovels = []
    for i in range(num_shovels):
        lat, lon = generate_gps_coordinates()
        loader_type = random.choice(list(LOADER_TYPES.values()))
        shovel = {
            'shovel_id': i + 1,
            'type_name': loader_type.type_name,
            'bucket_capacity': loader_type.bucket_capacity,
            'cycle_time': loader_type.cycle_time,
            'fuel_consumption': loader_type.fuel_consumption,
            'location': {
                'latitude': lat,
                'longitude': lon
            },
            'status': np.random.choice(['operational', 'maintenance'], p=[0.9, 0.1]),
            'current_queue': np.random.randint(0, 4),
            'maintenance_interval': loader_type.maintenance_interval
        }
        shovels.append(shovel)
    return pd.DataFrame(shovels)

def main():
    # Generate data
    trucks_df = generate_truck_data()
    shovels_df = generate_shovel_data()
    
    # Generate route data for each truck to its assigned shovel
    routes = []
    for _, truck in trucks_df.iterrows():
        shovel = shovels_df[shovels_df['shovel_id'] == truck['assigned_shovel']].iloc[0]
        route = generate_route_data(truck['current_location'], shovel['location'])
        route.update({
            'truck_id': truck['truck_id'],
            'shovel_id': shovel['shovel_id']
        })
        routes.append(route)
    
    routes_df = pd.DataFrame(routes)
    
    # Save to CSV files using absolute paths
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    trucks_df.to_csv(os.path.join(data_dir, 'trucks.csv'), index=False)
    shovels_df.to_csv(os.path.join(data_dir, 'shovels.csv'), index=False)
    routes_df.to_csv(os.path.join(data_dir, 'routes.csv'), index=False)
    
    print("Mock data generated successfully!")
    print(f"Generated {len(trucks_df)} trucks, {len(shovels_df)} shovels, and {len(routes_df)} routes")

if __name__ == "__main__":
    main()