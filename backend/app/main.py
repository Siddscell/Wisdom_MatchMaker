import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.api import dashboard, dev, items, matches, notifications
from app.config import get_settings
from app.constants import CATEGORIES, DELIVERY_SCOPES, UNIT_FAMILIES
from app.db import SessionLocal
from app.services.embedding import get_model, model_loaded

log = logging.getLogger(__name__)
_CODES = {400: "bad_request", 404: "not_found", 405: "method_not_allowed", 409: "conflict"}


def _error(status: int, code: str, message: str, fields: dict | None = None) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "fields": fields or {}}}
    return JSONResponse(status_code=status, content=body)


def _warm_model() -> None:
    try:
        get_model()
    except Exception:
        log.exception("Embedding model failed to load; run: python -m app.scripts.download_model")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the model in the background so startup is instant; /health shows progress.
    threading.Thread(target=_warm_model, daemon=True).start()
    yield


def create_app() -> FastAPI:
    settings = get_settings()  # raises a clear error on missing/invalid settings
    app = FastAPI(title="Supplier-Client Matchmaking", lifespan=lifespan)

    # Added before CORS so it runs inside it: 500s keep their CORS headers and the
    # browser sees the error body instead of an opaque network failure.
    @app.middleware("http")
    async def unexpected_error(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            log.exception("Unhandled error on %s %s", request.method, request.url.path)
            return _error(500, "internal_error", "Something went wrong on the server.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        return _error(exc.status_code, _CODES.get(exc.status_code, "http_error"), str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = {}
        for err in exc.errors():
            loc = [str(part) for part in err["loc"]]
            field = ".".join(loc[1:]) or loc[0]  # drop the "body"/"query" prefix
            fields[field] = err["msg"].removeprefix("Value error, ")
        return _error(422, "validation_error", "Some fields are invalid.", fields)

    for module in (matches, notifications, dashboard, dev):
        app.include_router(module.router)
    app.include_router(items.requirements)
    app.include_router(items.offerings)

    @app.get("/health")
    def health():
        try:
            with SessionLocal() as db:
                db.execute(text("select 1"))
            db_status = "ok"
        except SQLAlchemyError:
            log.exception("Database health check failed")
            db_status = "error"
        body = {"status": db_status, "db": db_status, "model_loaded": model_loaded()}
        return JSONResponse(body, status_code=200 if db_status == "ok" else 503)

    @app.get("/api/meta")
    def meta():
        return {
            "categories": CATEGORIES,
            "units": list(UNIT_FAMILIES),
            "delivery_scopes": DELIVERY_SCOPES,
            "score_thresholds": {
                "match_min": settings.MATCH_MIN_SCORE,
                "notify_min": settings.NOTIFY_MIN_SCORE,
            },
            "dev_mode": settings.ENV != "production",
        }

    return app


app = create_app()
