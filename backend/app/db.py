from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


# prepare_threshold=None: server-side prepared statements break behind transaction poolers.
engine = create_engine(
    get_settings().DATABASE_URL, pool_pre_ping=True, connect_args={"prepare_threshold": None}
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db
