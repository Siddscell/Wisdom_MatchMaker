"""One-time download of the text and image models: python -m app.scripts.download_model"""

from app.config import get_settings
from app.services.embedding import _load, clip_text, embed

if __name__ == "__main__":
    s = get_settings()
    print(f"{s.EMBEDDING_MODEL} ready ({len(embed('mild steel tube'))} dims).")
    print(f"{s.CLIP_TEXT_MODEL} ready ({len(clip_text('mild steel tube'))} dims).")
    _load("ImageEmbedding", s.CLIP_IMAGE_MODEL)
    print(f"{s.CLIP_IMAGE_MODEL} ready.")
