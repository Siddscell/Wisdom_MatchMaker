from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.auth import User
from app.constants import CATEGORIES, DELIVERY_SCOPES, UNIT_FAMILIES
from app.models import Match


def _one_of(options) -> AfterValidator:
    allowed = list(options)

    def check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"must be one of: {', '.join(allowed)}")
        return value

    return AfterValidator(check)


Name = Annotated[str, Field(min_length=2, max_length=200)]
Description = Annotated[str, Field(min_length=2, max_length=2000)]
Notes = Annotated[str | None, Field(max_length=2000), AfterValidator(lambda v: v or None)]
Positive = Annotated[float, Field(gt=0, le=1e12)]
Category = Annotated[str, _one_of(CATEGORIES)]
Unit = Annotated[str, _one_of(UNIT_FAMILIES)]
Scope = Annotated[str, _one_of(DELIVERY_SCOPES)]


class _In(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class RequirementIn(_In):
    client_name: Name
    product_requirement: Description
    category: Category
    quantity: Positive
    unit: Unit
    budget: Positive  # total budget for the full quantity
    location: Name
    needed_within_days: int = Field(gt=0, le=3650)
    notes: Notes = None


class OfferingIn(_In):
    supplier_name: Name
    product_offered: Description
    category: Category
    available_quantity: Positive
    unit: Unit
    unit_price: Positive
    pricing_notes: Notes = None
    location: Name
    lead_time_days: int = Field(ge=0, le=3650)
    delivery_scope: Scope
    notes: Notes = None


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MatchOut(_Out):
    id: str
    requirement_id: str
    offering_id: str
    score: float
    status: str
    created_at: datetime
    updated_at: datetime
    requirement_product: str
    client_name: str
    offering_product: str
    supplier_name: str
    # Contact details only for the two parties, and only once the match is accepted.
    client_email: str | None
    supplier_email: str | None

    @classmethod
    def of(cls, m: Match, viewer: User | None = None) -> "MatchOut":
        r, o = m.requirement, m.offering
        share = m.status == "accepted" and viewer is not None and is_party(m, viewer)
        return cls(
            id=m.id,
            requirement_id=m.requirement_id,
            offering_id=m.offering_id,
            score=m.score,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
            requirement_product=r.product_requirement,
            client_name=r.client_name,
            offering_product=o.product_offered,
            supplier_name=o.supplier_name,
            client_email=r.contact_email if share else None,
            supplier_email=o.contact_email if share else None,
        )


def is_party(m: Match, user: User) -> bool:
    # A listing belongs to the account whose verified email created it.
    return user.email in (m.requirement.contact_email, m.offering.contact_email)


class RequirementPublic(_Out):
    """What anyone may see: no contact email, no budget."""

    id: str
    client_name: str
    product_requirement: str
    category: str
    quantity: float
    unit: str
    location: str
    latitude: float | None
    longitude: float | None
    needed_within_days: int
    notes: str | None
    status: str
    created_at: datetime


class RequirementOut(RequirementPublic):
    """The owner's full view."""

    contact_email: str
    budget: float


class OfferingPublic(_Out):
    """What anyone may see: no contact email, no prices."""

    id: str
    supplier_name: str
    product_offered: str
    category: str
    available_quantity: float
    unit: str
    location: str
    latitude: float | None
    longitude: float | None
    lead_time_days: int
    delivery_scope: str
    notes: str | None
    status: str
    created_at: datetime


class OfferingOut(OfferingPublic):
    """The owner's full view."""

    contact_email: str
    unit_price: float
    pricing_notes: str | None


class RequirementDetail(RequirementPublic):
    matches: list[MatchOut]


class OfferingDetail(OfferingPublic):
    matches: list[MatchOut]


class ListingStatusIn(BaseModel):
    status: Literal["open", "closed", "active", "inactive"]


class MatchStatusIn(BaseModel):
    status: Literal["accepted", "rejected"]


class NotificationOut(_Out):
    id: str
    match_id: str
    recipient_role: str
    recipient_email: str
    message: str
    is_read: bool
    created_at: datetime


class OutboxOut(_Out):
    id: str
    to_email: str
    subject: str
    body: str
    created_at: datetime
    sent_at: datetime | None
