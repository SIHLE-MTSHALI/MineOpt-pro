import sys
import os
# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.services import seed_service
from app.domain import models_core, models_time, models_resource, models_flow, models_scheduling

# Ensure tables exist
models_core.Base.metadata.create_all(bind=engine)
models_time.Base.metadata.create_all(bind=engine)
models_resource.Base.metadata.create_all(bind=engine)
models_flow.Base.metadata.create_all(bind=engine)
models_scheduling.Base.metadata.create_all(bind=engine)

def debug_seed():
    db = SessionLocal()
    try:
        print("Attempting to seed data...")
        # Clean flush
        # seed_service.seed_enterprise_data(db)
        
        # Copied logic from config_router
        result = seed_service.seed_enterprise_data(db)
        print(f"Success! Result: {result}")
        
    except Exception as e:
        import traceback
        print("CAUGHT EXCEPTION:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_seed()
