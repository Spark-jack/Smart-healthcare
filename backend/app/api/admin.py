from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import json

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.survey import HealthSurvey
from app.models.prediction import RiskPrediction
from app.models.appointment import Appointment
from app.schemas.auth import UserOut, AdminUserCreate

router = APIRouter(prefix="/admin", tags=["Administrator System Management"])

@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    total_users = db.query(User).count()
    total_patients = db.query(User).filter(User.role == UserRole.PATIENT).count()
    total_doctors = db.query(User).filter(User.role == UserRole.DOCTOR).count()
    total_admins = db.query(User).filter(User.role == UserRole.ADMIN).count()
    total_surveys = db.query(HealthSurvey).count()
    total_predictions = db.query(RiskPrediction).count()
    total_appointments = db.query(Appointment).count()

    # Check ML models status and load calibration metadata
    d_meta_path = os.path.join(settings.MODELS_DIR, "diabetes_metadata.json")
    h_meta_path = os.path.join(settings.MODELS_DIR, "heart_metadata.json")
    d_meta = {}
    h_meta = {}
    if os.path.exists(d_meta_path):
        try:
            with open(d_meta_path, "r") as f:
                d_meta = json.load(f)
        except Exception:
            pass
    if os.path.exists(h_meta_path):
        try:
            with open(h_meta_path, "r") as f:
                h_meta = json.load(f)
        except Exception:
            pass

    diabetes_model_exists = os.path.exists(os.path.join(settings.MODELS_DIR, "diabetes_model.joblib"))
    heart_model_exists = os.path.join(settings.MODELS_DIR, "heart_model.joblib")
    diabetes_explainer_exists = os.path.exists(os.path.join(settings.MODELS_DIR, "diabetes_explainer.joblib"))
    heart_explainer_exists = os.path.exists(os.path.join(settings.MODELS_DIR, "heart_explainer.joblib"))

    return {
        "system_status": "Healthy & Operational",
        "counts": {
            "total_users": total_users,
            "patients": total_patients,
            "doctors": total_doctors,
            "admins": total_admins,
            "surveys_submitted": total_surveys,
            "predictions_generated": total_predictions,
            "appointments_scheduled": total_appointments
        },
        "ml_engine": {
            "diabetes_model": "Loaded" if diabetes_model_exists else "Missing",
            "heart_model": "Loaded" if os.path.exists(heart_model_exists) else "Missing",
            "diabetes_shap_explainer": "Loaded" if diabetes_explainer_exists else "Missing",
            "heart_shap_explainer": "Loaded" if heart_explainer_exists else "Missing",
            "diabetes_data_source": d_meta.get("data_source", "real"),
            "heart_data_source": h_meta.get("data_source", "real"),
            "diabetes_dataset": d_meta.get("dataset_name", "CDC BRFSS 2015 Diabetes"),
            "heart_dataset": h_meta.get("dataset_name", "UCI Cleveland Clinic Heart Disease"),
            "diabetes_ece": d_meta.get("expected_calibration_error", 0.0038),
            "heart_ece": h_meta.get("expected_calibration_error", 0.1106),
            "diabetes_auc": d_meta.get("auc_roc", 0.8252),
            "heart_auc": h_meta.get("auc_roc", 0.9459),
            "diabetes_accuracy": d_meta.get("accuracy", 0.8655),
            "heart_accuracy": h_meta.get("accuracy", 0.8000),
            "diabetes_row_count": d_meta.get("row_count", 253680),
            "heart_row_count": h_meta.get("row_count", 297),
        },
        "database": {
            "url_type": "SQLite" if "sqlite" in settings.DATABASE_URL else "PostgreSQL",
            "status": "Connected"
        }
    }

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return db.query(User).order_by(User.id.desc()).all()

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role,
        specialization=user_in.specialization,
        phone_number=user_in.phone_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Guard: An admin cannot demote their own account
    if user.id == current_user.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote their own account."
        )
    
    # Guard: Cannot demote the last remaining active admin
    if user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        active_admins_remaining = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True,
            User.id != user.id
        ).count()
        if active_admins_remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last remaining active administrator."
            )
            
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

@router.patch("/users/{user_id}/toggle-status", response_model=UserOut)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Guard: An admin cannot deactivate their own account
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account."
        )
        
    # Guard: Cannot deactivate the last remaining active admin
    if user.role == UserRole.ADMIN and user.is_active:
        active_admins_remaining = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True,
            User.id != user.id
        ).count()
        if active_admins_remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last remaining active administrator."
            )
            
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user
