from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import User, current_user, optional_user
from app.db import get_db
from app.models import Match
from app.schemas import MatchOut, MatchStatusIn, is_party
from app.services.ml import retrain

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
def list_matches(
    requirement_id: UUID | None = None,
    offering_id: UUID | None = None,
    status: str | None = None,
    min_score: float | None = None,
    limit: int = Query(500, ge=1, le=2000),
    viewer: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    stmt = select(Match).order_by(Match.score.desc(), Match.created_at.desc()).limit(limit)
    if requirement_id:
        stmt = stmt.where(Match.requirement_id == str(requirement_id))
    if offering_id:
        stmt = stmt.where(Match.offering_id == str(offering_id))
    if status:
        stmt = stmt.where(Match.status == status)
    if min_score is not None:
        stmt = stmt.where(Match.score >= min_score)
    return [MatchOut.of(m, viewer) for m in db.scalars(stmt).unique()]


@router.patch("/{match_id}/status", response_model=MatchOut)
def update_status(
    match_id: UUID,
    body: MatchStatusIn,
    tasks: BackgroundTasks,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    match = db.get(Match, str(match_id), with_for_update={"of": Match})
    if match is None:
        raise HTTPException(404, "Match not found")
    if not is_party(match, user):
        raise HTTPException(403, "Only the client or supplier of this match can decide on it.")
    if match.status not in ("new", "notified"):
        raise HTTPException(409, f"Match is already {match.status}")
    match.status, match.updated_at = body.status, func.now()
    db.commit()
    db.refresh(match)
    tasks.add_task(retrain)  # every decision is a training label for the ranker
    return MatchOut.of(match, user)
