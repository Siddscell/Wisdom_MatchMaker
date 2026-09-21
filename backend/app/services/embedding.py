import threading

import numpy as np

from app.config import get_settings

_model = None
_lock = threading.Lock()


def get_model():
    """Load the local ONNX model once (downloads on first use, then cached on disk)."""
    global _model
    with _lock:
        if _model is None:
            from fastembed import TextEmbedding

            _model = TextEmbedding(get_settings().EMBEDDING_MODEL)
    return _model


def model_loaded() -> bool:
    return _model is not None


def record_text(product: str, notes: str | None) -> str:
    # Category is left out on purpose: it is a hard filter, and a shared suffix on both
    # sides inflates similarity between unrelated products (see docs/DECISIONS.md).
    return f"{product} | {notes}" if notes else product


def embed(text: str) -> list[float]:
    vector = next(iter(get_model().embed([text])))
    if len(vector) != get_settings().EMBEDDING_DIM:
        raise RuntimeError(
            f"Model returned {len(vector)} dims but EMBEDDING_DIM={get_settings().EMBEDDING_DIM}"
        )
    return (vector / np.linalg.norm(vector)).tolist()
