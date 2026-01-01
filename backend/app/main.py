from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import config_router, schedule_router, calendar_router, optimization_router, reporting_router, stockpile_router, analytics_router

app = FastAPI(title="MineOpt Pro Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router.router)
app.include_router(schedule_router.router)
app.include_router(calendar_router.router)
app.include_router(optimization_router.router)
app.include_router(reporting_router.router)
app.include_router(stockpile_router.router)
app.include_router(analytics_router.router)



@app.get("/")
def health_check():
    return {"status": "MineOpt Pro Server Running", "version": "2.0.0-Enterprise"}
