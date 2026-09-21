"""Requirements and offerings share one router shape: create, list with filters, detail."""

from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Offering, Requirement
from app.schemas import (
    MatchOut,
    OfferingDetail,
    OfferingIn,
    OfferingOut,
    RequirementDetail,
    RequirementIn,
    RequirementOut,
)
from app.services.matching import match_offering, match_requirement


def _router(
    prefix: str,
    model: type[Requirement] | type[Offering],
    schema_in: type[BaseModel],
    schema_out: type[BaseModel],
    schema_detail: type[BaseModel],
    run_matching: Callable[[str], None],
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[model.__tablename__])
    label = model.__name__

    @router.post("", status_code=201, response_model=schema_out)
    def create(payload: schema_in, tasks: BackgroundTasks, db: Session = Depends(get_db)):
        item = model(**payload.model_dump())
        db.add(item)
        db.commit()
        tasks.add_task(run_matching, item.id)  # runs after the response is sent
        return item

    @router.get("", response_model=list[schema_out])
    def list_items(
        email: str | None = None,
        category: str | None = None,
        status: str | None = None,
        db: Session = Depends(get_db),
    ):
        stmt = select(model).order_by(model.created_at.desc())
        if email:
            stmt = stmt.where(model.contact_email == email.strip().lower())
        if category:
            stmt = stmt.where(model.category == category)
        if status:
            stmt = stmt.where(model.status == status)
        return db.scalars(stmt).all()

    @router.get("/{item_id}", response_model=schema_detail)
    def detail(item_id: UUID, db: Session = Depends(get_db)):
        item = db.get(model, str(item_id))
        if item is None:
            raise HTTPException(404, f"{label} not found")
        return schema_detail(
            **schema_out.model_validate(item).model_dump(),
            matches=[MatchOut.of(m) for m in item.matches],
        )

    return router


requirements = _router(
    "/api/requirements",
    Requirement,
    RequirementIn,
    RequirementOut,
    RequirementDetail,
    match_requirement,
)
offerings = _router(
    "/api/offerings", Offering, OfferingIn, OfferingOut, OfferingDetail, match_offering
)
