from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every tunable lives here; each can be overridden by an env var of the same name."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    ENV: Literal["development", "production"] = "development"
    DATABASE_URL: str  # required: fail fast when missing
    CORS_ORIGINS: str = "http://localhost:5173"
    # Supabase Auth: the backend asks Supabase who a bearer token belongs to.
    SUPABASE_URL: str  # required, e.g. https://<project-ref>.supabase.co
    SUPABASE_ANON_KEY: str  # anon / publishable key (never service_role)

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384
    # Visual matching (CLIP). Photos and text share one space but on different scales, so each
    # comparison has its own calibration, measured on sample photos (docs/AI_MATCHING.md).
    CLIP_IMAGE_MODEL: str = "Qdrant/clip-ViT-B-32-vision"
    CLIP_TEXT_MODEL: str = "Qdrant/clip-ViT-B-32-text"
    VISUAL_IMAGE_FLOOR: float = 0.64  # photo <-> photo
    VISUAL_IMAGE_RANGE: float = 0.16
    VISUAL_TEXT_FLOOR: float = 0.23  # photo <-> text
    VISUAL_TEXT_RANGE: float = 0.09

    STRICT_CATEGORY: bool = True
    MIN_QTY_FRACTION: float = 0.25
    MAX_LEAD_FACTOR: float = 2.0
    MAX_BUDGET_FACTOR: float = 1.5
    RETRIEVE_K: int = 30
    MAX_MATCHES_PER_ITEM: int = 10
    MATCH_MIN_SCORE: float = 60
    NOTIFY_MIN_SCORE: float = 70
    # Calibration of cosine similarity into 0..1: semantic = (cos - FLOOR) / RANGE.
    # Tuned on labelled seed pairs for bge-small (see docs/AI_MATCHING.md); retune per model.
    # Learned ranker: weights move from the WEIGHT_* prior to learned values as labels
    # accumulate; at RANKER_PRIOR_STRENGTH labels, learned and prior count equally.
    RANKER_PRIOR_STRENGTH: int = 50
    SEMANTIC_FLOOR: float = 0.65
    SEMANTIC_RANGE: float = 0.28

    WEIGHT_SEMANTIC: float = 0.40
    WEIGHT_PRICE: float = 0.20
    WEIGHT_QUANTITY: float = 0.15
    WEIGHT_DELIVERY: float = 0.15
    WEIGHT_LOCATION: float = 0.10

    EMAIL_BACKEND: Literal["outbox", "smtp"] = "outbox"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    GEOCODER: Literal["nominatim", "none"] = "nominatim"

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_psycopg3(cls, url: str) -> str:
        # Supabase hands out postgresql:// URLs; SQLAlchemy would pick psycopg2 for those.
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url

    @model_validator(mode="after")
    def _check(self) -> "Settings":
        total = sum(self.weights.values())
        if abs(total - 1) > 1e-6:
            raise ValueError(f"WEIGHT_* settings must sum to 1.0 (they sum to {total:g})")
        if self.EMAIL_BACKEND == "smtp" and not (self.SMTP_HOST and self.SMTP_FROM):
            raise ValueError("EMAIL_BACKEND=smtp requires SMTP_HOST and SMTP_FROM")
        return self

    @property
    def weights(self) -> dict[str, float]:
        return {
            "semantic": self.WEIGHT_SEMANTIC,
            "price": self.WEIGHT_PRICE,
            "quantity": self.WEIGHT_QUANTITY,
            "delivery": self.WEIGHT_DELIVERY,
            "location": self.WEIGHT_LOCATION,
        }

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
