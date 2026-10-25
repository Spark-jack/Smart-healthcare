from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationOut, UnreadCountOut, NotificationPageOut

router = APIRouter(prefix="/notifications", tags=["Notifications & Clinical Alerts"])

@router.get("", response_model=NotificationPageOut)
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Returns paginated notifications for current user, sorted unread-first then newest-first.
    """
    base_query = db.query(Notification).filter(Notification.user_id == current_user.id)
    total = base_query.count()
    unread_count = base_query.filter(Notification.is_read == False).count()

    items = (
        base_query.order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NotificationPageOut(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size
    )

@router.get("/unread-count", response_model=UnreadCountOut)
def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

@router.post("/read-all", response_model=UnreadCountOut)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"unread_count": 0}
