"""ORM mapping of supabase/migrations/0001_init.sql (the SQL files own the schema)."""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.db import Base

_DIM = get_settings().EMBEDDING_DIM


def _id() -> Mapped[str]:
    return mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )


def _num() -> Mapped[float]:
    return mapped_column(Numeric(asdecimal=False))


def _created() -> Mapped[datetime]:
    return mapped_column(server_default=func.now())


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = _id()
    client_name: Mapped[str]
    contact_email: Mapped[str]
    product_requirement: Mapped[str]
    category: Mapped[str]
    quantity: Mapped[float] = _num()
    unit: Mapped[str]
    budget: Mapped[float] = _num()
    location: Mapped[str]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    needed_within_days: Mapped[int]
    notes: Mapped[str | None]
    embedding = mapped_column(Vector(_DIM), nullable=True, deferred=True)
    status: Mapped[str] = mapped_column(server_default="open")
    created_at: Mapped[datetime] = _created()

    matches: Mapped[list["Match"]] = relationship(
        back_populates="requirement", order_by="Match.score.desc()", viewonly=True
    )

    @property
    def product(self) -> str:
        return self.product_requirement


class Offering(Base):
    __tablename__ = "offerings"

    id: Mapped[str] = _id()
    supplier_name: Mapped[str]
    contact_email: Mapped[str]
    product_offered: Mapped[str]
    category: Mapped[str]
    available_quantity: Mapped[float] = _num()
    unit: Mapped[str]
    unit_price: Mapped[float] = _num()
    pricing_notes: Mapped[str | None]
    location: Mapped[str]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    lead_time_days: Mapped[int]
    delivery_scope: Mapped[str]
    notes: Mapped[str | None]
    embedding = mapped_column(Vector(_DIM), nullable=True, deferred=True)
    status: Mapped[str] = mapped_column(server_default="active")
    created_at: Mapped[datetime] = _created()

    matches: Mapped[list["Match"]] = relationship(
        back_populates="offering", order_by="Match.score.desc()", viewonly=True
    )

    @property
    def product(self) -> str:
        return self.product_offered


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = _id()
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"))
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id", ondelete="CASCADE"))
    score: Mapped[float] = mapped_column(Numeric(5, 2, asdecimal=False))
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        ENUM("new", "notified", "accepted", "rejected", name="match_status", create_type=False),
        server_default="new",
    )
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _created()

    requirement: Mapped[Requirement] = relationship(back_populates="matches", lazy="joined")
    offering: Mapped[Offering] = relationship(back_populates="matches", lazy="joined")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = _id()
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    recipient_role: Mapped[str]
    recipient_email: Mapped[str]
    message: Mapped[str]
    is_read: Mapped[bool] = mapped_column(server_default="false")
    created_at: Mapped[datetime] = _created()


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id: Mapped[str] = _id()
    to_email: Mapped[str]
    subject: Mapped[str]
    body: Mapped[str]
    created_at: Mapped[datetime] = _created()
    sent_at: Mapped[datetime | None]


class GeocodeCache(Base):
    __tablename__ = "geocode_cache"

    query: Mapped[str] = mapped_column(primary_key=True)
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    created_at: Mapped[datetime] = _created()


class ModelState(Base):
    __tablename__ = "model_state"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = _created()
