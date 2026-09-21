"""One-time download of the embedding model: python -m app.scripts.download_model"""

from app.config import get_settings
from app.services.embedding import embed

if __name__ == "__main__":
    vector = embed("mild steel tube")
    print(f"{get_settings().EMBEDDING_MODEL} ready ({len(vector)} dims).")
