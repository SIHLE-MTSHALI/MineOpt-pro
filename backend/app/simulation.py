import simpy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional
from backend.app.equipment_config import EnvironmentalFactors
from backend.app.data_generator import generate_truck_data, generate_shovel_data
from backend.app.models import SimulationState, Truck, Shovel, Location, Block, QualitySpecs, Stockpile
from backend.app.scheduler import BlockScheduler

class MineSimulation:
    def __init__(self, num_trucks=10, num_shovels=3, max_trucks_per_shovel=4):
        self.env = simpy.Environment()
        self.num_trucks = num_trucks
        self.num_shovels = num_shovels
        self.max_trucks_per_shovel = max_trucks_per_shovel
        
        # Determine initial locations (Witbank area)
        self.witbank_center = {'lat': -25.8772, 'lon': 29.2302}
        
        # Initialize data
        self.trucks_df = generate_truck_data(num_trucks)
        self.shovels_df = generate_shovel_data(num_shovels)
        
        # SimPy resources
        self.shovels_res = {}
        # Witbank Geology: Multiple seams (mainly Seam 2 and Seam 4).
        # We assign different seams to different shovels.
        seams = ['Seam 1', 'Seam 2 Lower', 'Seam 2 Upper', 'Seam 4 Lower', 'Seam 4 Upper', 'Seam 5']
        
        for i, (idx, shovel) in enumerate(self.shovels_df.iterrows()):
            self.shovels_res[shovel['shovel_id']] = simpy.Resource(self.env, capacity=max_trucks_per_shovel)
            # Assign a random seam to this shovel
            self.shovels_df.at[idx, 'mining_seam'] = seams[i % len(seams)]
            
        self.logs = []
        self.current_weather = 'clear'
        self.total_production = 0.0
        self.total_fuel = 0.0
        
        # Shift Management
        self.current_shift_name = 'Morning'
        self.shift_start_time = self.env.now
        self.shift_duration = 8 # hours
        self.daily_production_target = 30000.0 # tonnes
        self.shift_target = self.daily_production_target / 3
        
        # Real-time state for API
        self.running = False
        self.state_lock = asyncio.Lock()
        
        # Environmental setup
        self.road_conditions = pd.DataFrame({
            'segment_id': range(1, num_shovels + 1),
            'condition': 1.0,
            'last_maintenance': 0
        })
        
        # Start background processes
        self.env.process(self.weather_update_process())
        self.env.process(self.shift_update_process())

        # --- Scheduler & Block Model Setup ---
        self.scheduler = BlockScheduler()
        self.stockpiles = {
            "ROM": Stockpile(
                stockpile_id="ROM", 
                current_tonnes=0, 
                current_quality=QualitySpecs(ash=0, sulfur=0, cv=0), 
                target_quality=QualitySpecs(ash=15.0, sulfur=0.8, cv=24.0),
                capacity=500000
            )
        }
        
        # Mock Block Model
        self._init_mock_blocks()
        
        # Start truck processes
        for truck_id in self.trucks_df['truck_id']:
            self.env.process(self.truck_process(truck_id))

    def _init_mock_blocks(self):
        """Generate a simple block model for testing"""
        # Lower Seam (High Quality)
        b1 = Block(block_id="B1", tonnes=10000, waste_tonnes=500, quality=QualitySpecs(ash=12, sulfur=0.6, cv=26), location=Location(latitude=-25.88, longitude=29.23), status='available')
        b2 = Block(block_id="B2", tonnes=10000, waste_tonnes=500, quality=QualitySpecs(ash=12.5, sulfur=0.6, cv=25.8), location=Location(latitude=-25.882, longitude=29.232), dependencies=['B1'])
        
        # Upper Seam (Lower Quality)
        b3 = Block(block_id="B3", tonnes=15000, waste_tonnes=2000, quality=QualitySpecs(ash=22, sulfur=1.2, cv=20), location=Location(latitude=-25.875, longitude=29.225), status='available')
        
        self.scheduler.add_block(b1)
        self.scheduler.add_block(b2)
        self.scheduler.add_block(b3)

    def get_state(self) -> SimulationState:
        """Convert current internal state to Pydantic model"""
        trucks_list = []
        for _, t in self.trucks_df.iterrows():
            trucks_list.append(Truck(
                truck_id=t['truck_id'],
                type_name=t['type_name'],
                capacity=t['capacity'],
                current_load=t['current_load'],
                load_type=t.get('load_type'),
                status=t['status'],
                current_location=Location(latitude=t['current_location']['latitude'], longitude=t['current_location']['longitude']),
                assigned_shovel=int(t['assigned_shovel']),
                speed=t.get('speed', 0.0),
                heading=0.0 # Placeholder
            ))
            
        shovels_list = []
        for _, s in self.shovels_df.iterrows():
            shovels_list.append(Shovel(
                shovel_id=s['shovel_id'],
                type_name=s['type_name'],
                location=Location(latitude=s['location']['latitude'], longitude=s['location']['longitude']),
                status=s['status'],
                current_queue=len(self.shovels_res[s['shovel_id']].queue),
                mining_seam=s.get('mining_seam', 'Seam 4')
            ))
            
        # Calculate shift progress
        elapsed = self.env.now - self.shift_start_time
        progress_pct = min(100.0, (elapsed / self.shift_duration) * 100)

        return SimulationState(
            timestamp=datetime.now(), # In a real sim, this would be env time mapping
            trucks=trucks_list,
            shovels=shovels_list,
            blocks=self.scheduler.get_all_blocks(),
            stockpiles=list(self.stockpiles.values()),
            total_production_tonnes=self.total_production,
            total_fuel_consumed=self.total_fuel,
            current_weather=self.current_weather,
            current_shift=self.current_shift_name,
            shift_progress_percent=progress_pct,
            shift_production_target=self.shift_target
        )

    async def run_step(self, duration=1):
        """Run the simulation for a small step (e.g., 1 second/minute)"""
        try:
            self.env.run(until=self.env.now + duration)
        except simpy.StopSimulation:
            pass

    # --- Simulation Logic (Configured for Witbank/Coal) ---

    def calculate_travel_time(self, start_point, end_point, truck):
        lat1, lon1 = start_point['latitude'], start_point['longitude']
        lat2, lon2 = end_point['latitude'], end_point['longitude']
        
        # Distance (Haversine approx for small distances)
        # 1 deg lat ~= 111km
        dist_km = np.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111.0
        
        # Effective Speed
        is_loaded = truck['current_load'] > 0
        base_speed = truck['max_speed_loaded'] if is_loaded else truck['max_speed_empty']
        
        # Factors
        weather_factor = EnvironmentalFactors.get_weather_factor(self.current_weather)
        # Random gradient for realism in Witbank (generally rolling hills, not steep mountains, but open pits have ramps)
        gradient = np.random.uniform(0, 8) # 0-8% gradients common in ramps
        grad_factor = EnvironmentalFactors.get_gradient_factor(gradient)
        
        effective_speed = base_speed * weather_factor * grad_factor
        
        if effective_speed < 1: effective_speed = 1 # Minimum speed
        
        hours = dist_km / effective_speed
        
        # Update fuel
        consumption_rate = truck['fuel_consumption_loaded'] if is_loaded else truck['fuel_consumption_empty']
        self.total_fuel += consumption_rate * hours 
        
        # Store speed for UI
        self.trucks_df.loc[self.trucks_df['truck_id'] == truck['truck_id'], 'speed'] = effective_speed
        
        return hours

    def weather_update_process(self):
        while True:
            yield self.env.timeout(4) # Change every 4 hours
            self.current_weather = np.random.choice(['clear', 'rain', 'storm'], p=[0.7, 0.2, 0.1])
            
    def shift_update_process(self):
        shifts = ['Morning', 'Afternoon', 'Night']
        idx = 0
        while True:
            yield self.env.timeout(self.shift_duration)
            idx = (idx + 1) % len(shifts)
            self.current_shift_name = shifts[idx]
            self.shift_start_time = self.env.now
            # Reset shift-based counters if needed, but here we track total production
            # In a real app we might reset 'shift_production'

    def truck_process(self, truck_id):
        while True:
            # 1. Get Truck Data
            truck_idx = self.trucks_df.index[self.trucks_df['truck_id'] == truck_id][0]
            truck = self.trucks_df.iloc[truck_idx]
            
            # --- DISPATCH LOGIC ---
            # Find a mineable block
            available_blocks = self.scheduler.get_available_blocks()
            
            if not available_blocks:
                # No blocks available -> IDLE
                self.trucks_df.at[truck_idx, 'status'] = 'idle'
                self.trucks_df.at[truck_idx, 'speed'] = 0.0
                yield self.env.timeout(1/60) # Wait 1 min
                continue

            # Simple Dispatch: Pick first available block
            # In a real system, we'd pick based on Shovel assignment and distance
            target_block = available_blocks[0]
            
            # Find shovel closest to block (or assigned)
            # For simplicity, we just use the truck's assigned shovel and move it to the block
            assigned_shovel_id = truck['assigned_shovel']
            shovel_row = self.shovels_df[self.shovels_df['shovel_id'] == assigned_shovel_id].iloc[0]
            
            # 2. Travel to Block (Source)
            self.trucks_df.at[truck_idx, 'status'] = 'hauling'
            # Update shovel location to block location (Simulating shovel moving to face)
            # In reality shovel moves slowly, but we assume it's there for this "Shift"
            self.shovels_df.at[self.shovels_df.index[self.shovels_df['shovel_id'] == assigned_shovel_id][0], 'current_block_id'] = target_block.block_id
            
            travel_time = self.calculate_travel_time(truck['current_location'], target_block.location, truck)
            yield self.env.timeout(travel_time)
            self.trucks_df.at[truck_idx, 'current_location'] = target_block.location
            
            # 3. Queue & Load
            self.trucks_df.at[truck_idx, 'status'] = 'queueing'
            with self.shovels_res[assigned_shovel_id].request() as req:
                yield req
                
                # 4. Loading
                self.trucks_df.at[truck_idx, 'status'] = 'loading'
                cycles = np.ceil(truck['capacity'] / shovel_row['bucket_capacity'])
                load_time_hours = (cycles * shovel_row['cycle_time']) / 3600.0
                yield self.env.timeout(load_time_hours)
                
                # MINE THE BLOCK via Scheduler
                mined_quality = self.scheduler.mine_block(target_block.block_id, truck['capacity'])
                
                if mined_quality:
                    self.trucks_df.at[truck_idx, 'current_load'] = truck['capacity']
                    self.trucks_df.at[truck_idx, 'load_type'] = f"Block {target_block.block_id}"
                    # Store quality in temporary column or object (simplified here)
                    # We will apply it at the dumping point
            
            # 5. Travel to Stockpile (ROM)
            rom_stockpile = self.stockpiles['ROM'] # Default Dump
            # Assume stockpile is at a fixed location relative to center
            dump_loc = {'latitude': self.witbank_center['lat'] + 0.02, 'longitude': self.witbank_center['lon'] + 0.02}
            
            self.trucks_df.at[truck_idx, 'status'] = 'hauling'
            travel_time = self.calculate_travel_time(truck['current_location'], dump_loc, truck)
            yield self.env.timeout(travel_time)
            self.trucks_df.at[truck_idx, 'current_location'] = dump_loc
            
            # 6. Dumping & Stockpile Update
            self.trucks_df.at[truck_idx, 'status'] = 'dumping'
            yield self.env.timeout(2/60)
            
            # Update Stockpile Stats (Weighted Average Blending)
            if truck['current_load'] > 0 and mined_quality:
                new_tonnes = rom_stockpile.current_tonnes + truck['capacity']
                
                # Calculate new quality (Weighted Avg)
                # (OldQ * OldT + NewQ * NewT) / TotalT
                old_ash = rom_stockpile.current_quality.ash
                new_ash = ((old_ash * rom_stockpile.current_tonnes) + (mined_quality.ash * truck['capacity'])) / new_tonnes
                
                rom_stockpile.current_quality.ash = new_ash
                rom_stockpile.current_tonnes = new_tonnes
            
            self.total_production += truck['capacity']
            self.trucks_df.at[truck_idx, 'current_load'] = 0
            self.trucks_df.at[truck_idx, 'load_type'] = None
