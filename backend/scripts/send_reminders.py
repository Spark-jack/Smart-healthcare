import os
import sys

# Append backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.services.notification_service import notification_service

def run_reminders():
    print("=" * 60)
    print("Running 24-Hour Appointment Reminder Job...")
    db = SessionLocal()
    try:
        sent_count = notification_service.send_appointment_reminders(db)
        print(f"[OK] Reminder job execution completed. Reminders sent: {sent_count}")
        return sent_count
    except Exception as e:
        print(f"[Error] Reminder job encountered an error: {e}", file=sys.stderr)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_reminders()
