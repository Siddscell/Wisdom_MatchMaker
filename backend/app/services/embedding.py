"""Local ONNX models, each loaded once per process (downloaded on first use, then cached).

- text model (bge-small): meaning of descriptions, the main semantic signal
- CLIP image + CLIP text: one shared space, so photos compare with photos and with text
"""

import io
import threading

import httpx
import numpy as np
from PIL import Image

from app.config import get_settings

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # same limit as the storage bucket
_models: dict[str, object] = {}
_lock = threading.Lock()


def _load(kind: str, name: str):
    with _lock:
        if name not in _models:
            import fastembed

            _models[name] = getattr(fastembed, kind)(name)
    return _models[name]


def get_model():
    return _load("TextEmbedding", get_settings().EMBEDDING_MODEL)


def model_loaded() -> bool:
    return get_settings().EMBEDDING_MODEL in _models


def record_text(product: str, notes: str | None) -> str:
    # Category is left out on purpose: it is a hard filter, and a shared suffix on both
    # sides inflates similarity between unrelated products (see docs/DECISIONS.md).
    return f"{product} | {notes}" if notes else product


def _unit(vector) -> list[float]:
    vector = np.asarray(vector, dtype=float)
    return (vector / np.linalg.norm(vector)).tolist()


def embed(text: str) -> list[float]:
    vector = next(iter(get_model().embed([text])))
    if len(vector) != get_settings().EMBEDDING_DIM:
        raise RuntimeError(
            f"Model returned {len(vector)} dims but EMBEDDING_DIM={get_settings().EMBEDDING_DIM}"
        )
    return _unit(vector)


def clip_text(text: str) -> list[float]:
    model = _load("TextEmbedding", get_settings().CLIP_TEXT_MODEL)
    return _unit(next(iter(model.embed([text]))))


def clip_image(url: str) -> list[float]:
    """Download a listing photo (our own storage bucket only) and embed it with CLIP."""
    response = httpx.get(url, timeout=15, follow_redirects=False)
    response.raise_for_status()
    if len(response.content) > MAX_IMAGE_BYTES:
        raise ValueError("Image is larger than 5 MB")
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    model = _load("ImageEmbedding", get_settings().CLIP_IMAGE_MODEL)
    return _unit(next(iter(model.embed([image]))))
