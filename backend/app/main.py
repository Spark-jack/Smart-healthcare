from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
import app.models # registers models with Base metadata
from app.api import auth, survey, predictions, triage, doctor, admin, notifications
from app.services.notification_service import notification_service

def _run_scheduled_reminders():
    db = SessionLocal()
    try:
        notification_service.send_appointment_reminders(db)
    except Exception as e:
        print(f"[Scheduler Error] Error running reminders: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist on startup
    Base.metadata.create_all(bind=engine)
    
    scheduler = None
    if settings.ENABLE_SCHEDULER:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(_run_scheduled_reminders, "interval", minutes=15, id="appointment_reminders", replace_existing=True)
            scheduler.start()
            print("[Scheduler] APScheduler background reminder worker started (interval: 15 min).")
        except Exception as e:
            print(f"[Scheduler Warning] Failed to start APScheduler: {e}")
            
    yield
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] APScheduler shut down cleanly.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Full-stack Clinical Healthcare Ecosystem with Explainable AI & Urgency Triage",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to settings.CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(survey.router, prefix=settings.API_V1_STR)
app.include_router(predictions.router, prefix=settings.API_V1_STR)
app.include_router(triage.router, prefix=settings.API_V1_STR)
app.include_router(doctor.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
