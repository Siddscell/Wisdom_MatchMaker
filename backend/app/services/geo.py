import logging
import threading
import time

import httpx
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import GeocodeCache

log = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_INDIA = "68,37,98,6"  # lon/lat box; preferred, not a restriction

_lock = threading.Lock()
_last_call = 0.0


def haversine_sql(lat1, lon1, lat2, lon2):
    """Great-circle distance in km as a SQL expression. Args may mix columns and floats."""
    a = func.power(func.sin(func.radians(lat2 - lat1) / 2), 2) + func.cos(
        func.radians(lat1)
    ) * func.cos(func.radians(lat2)) * func.power(func.sin(func.radians(lon2 - lon1) / 2), 2)
    return 2 * EARTH_RADIUS_KM * func.asin(func.least(1.0, func.sqrt(a)))


def geocode(db: Session, place: str) -> tuple[float, float] | None:
    """Place name -> (lat, lon) via Nominatim, cached in geocode_cache (misses cached too)."""
    if get_settings().GEOCODER == "none":
        return None
    key = place.strip().lower()
    hit = db.get(GeocodeCache, key)
    if hit is None:
        try:
            lat, lon = _nominatim(place)
        except (httpx.HTTPError, ValueError, KeyError):
            log.warning("Geocoding failed for %r; will retry next time", place, exc_info=True)
            return None  # transient failure: do not cache
        db.execute(
            insert(GeocodeCache)
            .values(query=key, latitude=lat, longitude=lon)
            .on_conflict_do_nothing()
        )
        hit = GeocodeCache(latitude=lat, longitude=lon)
    return None if hit.latitude is None else (hit.latitude, hit.longitude)


def _nominatim(place: str) -> tuple[float | None, float | None]:
    global _last_call
    # Note: process-wide lock to honour Nominatim's 1 request/second policy;
    # switch to a paid/self-hosted geocoder if volume grows.
    with _lock:
        time.sleep(max(0.0, 1.0 - (time.monotonic() - _last_call)))
        try:
            response = httpx.get(
                NOMINATIM_URL,
                params={"q": place, "format": "json", "limit": 1, "viewbox": _INDIA, "bounded": 0},
                headers={"User-Agent": "supplier-client-matchmaking/0.1"},
                timeout=10,
            )
        finally:
            _last_call = time.monotonic()
    response.raise_for_status()
    results = response.json()
    if not results:
        return None, None
    return float(results[0]["lat"]), float(results[0]["lon"])
