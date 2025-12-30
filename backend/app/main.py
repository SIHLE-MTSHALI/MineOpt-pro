from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from .models import SimulationConfig, SimulationState, OptimizationParams
from .simulation import MineSimulation
from .optimization import MineOptimizer

app = FastAPI(title="Mine Optimization API")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Simulation Instance
simulation_instance: MineSimulation | None = None
simulation_running = False

@app.post("/simulation/init")
async def init_simulation(config: SimulationConfig):
    global simulation_instance
    simulation_instance = MineSimulation(
        num_trucks=config.num_trucks,
        num_shovels=config.num_shovels,
        max_trucks_per_shovel=config.max_trucks_per_shovel
    )
    return {
        "message": "Simulation initialized", 
        "config": config,
        "initial_state": simulation_instance.get_state().dict()
    }

@app.post("/simulation/start")
async def start_simulation():
    global simulation_running
    if not simulation_instance:
        return {"error": "Simulation not initialized"}
    simulation_running = True
    return {
        "status": "started",
        "state": simulation_instance.get_state().dict()
    }

@app.post("/simulation/stop")
async def stop_simulation():
    global simulation_running
    simulation_running = False
    return {"status": "stopped"}

@app.websocket("/simulation/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if simulation_running and simulation_instance:
                # Run a step
                await simulation_instance.run_step(duration=0.1) # 6 minutes sim time
                
                # Get state
                state = simulation_instance.get_state()
                
                # Send to client
                await websocket.send_json(state.dict())
                
                # Limit frame rate
                await asyncio.sleep(0.1) # 10 updates per second max
            else:
                await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in websocket: {e}")
        await websocket.close()

@app.post("/optimization/run")
async def run_optimization(params: OptimizationParams):
    # This is a blocking operation, ideally should be a background task
    optimizer = MineOptimizer(
        num_trucks=10, # Default for now, should come from params or current config
        num_shovels=3
    )
    # NOTE: You probably need to refactor MineOptimizer to not depend on simpy.Environment in __init__ if it conflicts
    # Or just instantiate it fresh
    results = optimizer.optimize(
        population_size=params.population_size,
        generations=params.generations
    )
    
    # Clean up results for JSON response (simpy objects not serializable)
    clean_results = {
        "best_fitness": results['best_fitness'],
        # "best_solution": results['best_solution'], # Might be a list
        "logbook": results['logbook']
    }
    return clean_results
