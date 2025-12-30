import numpy as np
import pandas as pd
from deap import base, creator, tools, algorithms
import random
import pickle
import simpy
from .simulation import MineSimulation

class MineOptimizer:
    def __init__(self, num_trucks=10, num_shovels=3, max_trucks_per_shovel=4):
        self.num_trucks = num_trucks
        self.num_shovels = num_shovels
        self.max_trucks_per_shovel = max_trucks_per_shovel
        self.fuel_price = 25.0  # ZAR/L
        self.idle_cost_per_min = 35.0  # ZAR/min
        
        # Setup DEAP
        # Check if classes already exist to avoid warnings/errors on re-instantiation
        if not hasattr(creator, "FitnessMin"):
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMin)
        
        self.toolbox = base.Toolbox()
        self.setup_ga()
    
    def setup_ga(self):
        # Attribute generator: random shovel assignment
        self.toolbox.register("attr_shovel", random.randint, 1, self.num_shovels)
        
        # Structure initializers
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, 
                            self.toolbox.attr_shovel, n=self.num_trucks)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Genetic operators
        self.toolbox.register("evaluate", self.evaluate_solution)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt, low=1, up=self.num_shovels, indpb=0.2)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def evaluate_solution(self, individual):
        """Evaluate a solution using simulation results."""
        # Create a temporary simulation for evaluation
        # Note: In a real high-perf scenario, we wouldn't re-init the whole sim object every eval,
        # but for this scale it's fine.
        env = simpy.Environment() # Not actually used in new Simulation __init__ but kept if we need it
        
        # We need a headless mode for simulation that runs fast and doesn't do async sleeps
        # For now, we manually patch the simulation or create a lightweight version.
        # Let's instantiate the class but not run the async loop.
        
        sim = MineSimulation(self.num_trucks, self.num_shovels, self.max_trucks_per_shovel)
        
        # Apply Assignments
        # individual is a list of shovel IDs for each truck
        shovel_counts = {i: 0 for i in range(1, self.num_shovels + 1)}
        
        for i, shovel_id in enumerate(individual):
            if shovel_id not in shovel_counts: shovel_counts[shovel_id] = 0
            shovel_counts[shovel_id] += 1
            if shovel_counts[shovel_id] > self.max_trucks_per_shovel:
                return (float('inf'),)
            
            # Update dataframe directly
            sim.trucks_df.at[i, 'assigned_shovel'] = shovel_id

        # Run Simulation Headless (mocking the async loop for speed)
        # Since the new simulation.py uses async heavily for the real-time aspect,
        # we might need a dedicated `run_fast()` method in simulation.py for optimization.
        # For this refactor, I will calculate clear metrics based on distances and queues analytically or use a simplified event loop.
        
        # SIMPLE HEURISTIC COST FUNCTION FOR NOW (to avoid freezing the API with 100 generations of async sims)
        # Cost = Distance * Fuel + QueuePenalty
        
        total_cost = 0
        
        for i, truck in sim.trucks_df.iterrows():
            assigned_shovel = truck['assigned_shovel']
            shovel = sim.shovels_df[sim.shovels_df['shovel_id'] == assigned_shovel].iloc[0]
            
            # Location objects are dicts in the df
            dist = np.sqrt((truck['current_location']['latitude'] - shovel['location']['latitude'])**2 + 
                           (truck['current_location']['longitude'] - shovel['location']['longitude'])**2)
            
            # Simple cost model
            fuel_cost = dist * truck['fuel_consumption_empty'] * self.fuel_price
            
            # Queue penalty: simple heuristic (more trucks assigned to same shovel = more likely queue)
            queue_penalty = (shovel_counts[assigned_shovel] ** 2) * 50 # Exponential penalty for overcrowding
            
            total_cost += fuel_cost + queue_penalty
            
        return (total_cost,)
    
    def optimize(self, population_size=50, generations=100):
        """Run genetic algorithm optimization."""
        pop = self.toolbox.population(n=population_size)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Run evolution
        pop, logbook = algorithms.eaSimple(pop, self.toolbox, cxpb=0.7, mutpb=0.2,
                                         ngen=generations, stats=stats, halloffame=hof,
                                         verbose=True)
        
        return {
            'best_solution': list(hof[0]),
            'best_fitness': hof[0].fitness.values[0],
            'logbook': logbook
        }
