"""Requirements and offerings share one router shape.

Public: list and detail (no contacts, budgets or prices).
Owner (logged in, right role): create, /mine, edit, open/close.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ROLE_TABLE, User, current_user, optional_user
from app.db import get_db
from app.models import Offering, Requirement
from app.schemas import (
    ListingStatusIn,
    MatchOut,
    OfferingDetail,
    OfferingIn,
    OfferingOut,
    OfferingPublic,
    RequirementDetail,
    RequirementIn,
    RequirementOut,
    RequirementPublic,
)
from app.services.matching import match_offering, match_requirement


def _router(
    model: type[Requirement] | type[Offering],
    schema_in: type[BaseModel],
    schema_public: type[BaseModel],
    schema_owner: type[BaseModel],
    schema_detail: type[BaseModel],
    statuses: tuple[str, str],  # (active, inactive)
    run_matching: Callable[[str], None],
) -> APIRouter:
    table = model.__tablename__
    router = APIRouter(prefix=f"/api/{table}", tags=[table])
    label = model.__name__
    text_fields = {"product_requirement", "product_offered", "notes"}

    def owned(db: Session, item_id: UUID, user: User):
        item = db.get(model, str(item_id))
        if item is None:
            raise HTTPException(404, f"{label} not found")
        if item.contact_email != user.email:
            raise HTTPException(403, f"This {label.lower()} belongs to another account.")
        return item

    @router.post("", status_code=201, response_model=schema_owner)
    def create(
        payload: schema_in,
        tasks: BackgroundTasks,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        if ROLE_TABLE.get(user.role) != table:
            needed = next(role for role, t in ROLE_TABLE.items() if t == table)
            raise HTTPException(403, f"Only {needed} accounts can post {table}.")
        item = model(**payload.model_dump(), contact_email=user.email)
        db.add(item)
        db.commit()
        tasks.add_task(run_matching, item.id)  # runs after the response is sent
        return item

    @router.get("", response_model=list[schema_public])
    def list_public(
        category: str | None = None, status: str | None = None, db: Session = Depends(get_db)
    ):
        stmt = select(model).order_by(model.created_at.desc())
        if category:
            stmt = stmt.where(model.category == category)
        if status:
            stmt = stmt.where(model.status == status)
        return db.scalars(stmt).all()

    @router.get("/mine", response_model=list[schema_owner])
    def list_mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
        stmt = select(model).where(model.contact_email == user.email)
        return db.scalars(stmt.order_by(model.created_at.desc())).all()

    @router.get("/{item_id}", response_model=schema_detail)
    def detail(
        item_id: UUID,
        viewer: User | None = Depends(optional_user),
        db: Session = Depends(get_db),
    ):
        item = db.get(model, str(item_id))
        if item is None:
            raise HTTPException(404, f"{label} not found")
        return schema_detail(
            **schema_public.model_validate(item).model_dump(),
            matches=[MatchOut.of(m, viewer) for m in item.matches],
        )

    @router.put("/{item_id}", response_model=schema_owner)
    def update(
        item_id: UUID,
        payload: schema_in,
        tasks: BackgroundTasks,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        item = owned(db, item_id, user)
        changes = {k: v for k, v in payload.model_dump().items() if getattr(item, k) != v}
        for key, value in changes.items():
            setattr(item, key, value)
        if text_fields & changes.keys():
            item.embedding = item.clip_text_embedding = None  # re-embedded by the run below
        if "image_url" in changes:
            item.image_embedding = None
        if "location" in changes:
            item.latitude = item.longitude = None  # re-geocoded
        db.commit()
        if changes and item.status == statuses[0]:
            tasks.add_task(run_matching, item.id)
        return item

    @router.patch("/{item_id}/status", response_model=schema_owner)
    def set_status(
        item_id: UUID,
        body: ListingStatusIn,
        tasks: BackgroundTasks,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        if body.status not in statuses:
            raise HTTPException(422, f"Status must be one of: {', '.join(statuses)}")
        item = owned(db, item_id, user)
        reopened = item.status != statuses[0] and body.status == statuses[0]
        item.status = body.status
        db.commit()
        if reopened:
            tasks.add_task(run_matching, item.id)
        return item

    return router


requirements = _router(
    Requirement,
    RequirementIn,
    RequirementPublic,
    RequirementOut,
    RequirementDetail,
    ("open", "closed"),
    match_requirement,
)
offerings = _router(
    Offering,
    OfferingIn,
    OfferingPublic,
    OfferingOut,
    OfferingDetail,
    ("active", "inactive"),
    match_offering,
)
