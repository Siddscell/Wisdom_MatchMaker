from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Match, Offering, Requirement

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    by_status = dict(db.execute(select(Match.status, func.count()).group_by(Match.status)).all())
    average = db.scalar(select(func.avg(Match.score)))
    return {
        "total_requirements": db.scalar(select(func.count()).select_from(Requirement)),
        "total_offerings": db.scalar(select(func.count()).select_from(Offering)),
        "total_matches": sum(by_status.values()),
        "average_score": round(float(average), 2) if average is not None else None,
        "accepted_count": by_status.get("accepted", 0),
        "matches_by_status": {
            s: by_status.get(s, 0) for s in ("new", "notified", "accepted", "rejected")
        },
    }
