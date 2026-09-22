"""Development helpers. Every route returns 404 when ENV=production."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import EmailOutbox
from app.schemas import OutboxOut
from app.seed.seed_data import seed
from app.services.matching import rematch_all


def _dev_only() -> None:
    if get_settings().ENV == "production":
        raise HTTPException(404, "Not found")


router = APIRouter(prefix="/api/dev", tags=["dev"], dependencies=[Depends(_dev_only)])


@router.post("/seed")
def seed_data(tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict:
    created = seed(db)
    tasks.add_task(rematch_all)
    return {**created, "message": "Sample data loaded; matching is running in the background."}


@router.post("/rematch", status_code=202)
def rematch(tasks: BackgroundTasks) -> dict:
    tasks.add_task(rematch_all)
    return {"message": "Recomputing all matches in the background."}


@router.get("/outbox", response_model=list[OutboxOut])
def outbox(db: Session = Depends(get_db)):
    return db.scalars(select(EmailOutbox).order_by(EmailOutbox.created_at.desc()).limit(200)).all()
