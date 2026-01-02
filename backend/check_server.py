import sys
import os
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("Server Import Successful")
except Exception as e:
    import traceback
    traceback.print_exc()
