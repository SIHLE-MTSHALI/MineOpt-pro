
from app.database import engine, Base
# Import all models to ensure they are registered
from app.domain import models_core
from app.domain import models_calendar
from app.domain import models_resource
from app.domain import models_parcel
from app.domain import models_flow
from app.domain import models_scheduling
from app.domain import models_quality
from app.domain import models_wash_table
from app.domain import models_schedule_results

print("Imported all models")

try:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
except Exception as e:
    print(f"Error creating tables: {e}")
    import traceback
    traceback.print_exc()
