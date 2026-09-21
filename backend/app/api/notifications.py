from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Notification
from app.schemas import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    email: str | None = None,
    unread: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if email:
        stmt = stmt.where(Notification.recipient_email == email.strip().lower())
    if unread is not None:
        stmt = stmt.where(Notification.is_read.is_not(unread))
    return db.scalars(stmt).all()


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Notification, str(notification_id))
    if item is None:
        raise HTTPException(404, "Notification not found")
    item.is_read = True
    db.commit()
    return item
