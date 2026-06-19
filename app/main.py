from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import os

from app.api.v1.routers import (
    auth_router,
    role_router,
    states_router,
    user_router,
    terminal_router,
    courier_router,
    vehicle_routers,
    hub_shift_router,
    order_router,
    mission_router,
    route_router,
    avatar_router,
    utils_router,
    scan_router,
    billing_router,
    stripe_webhook_router,
)
from app.config.settings import settings
from app.config.dependencies import engine
from app.adapters.database.models import Base
from pathlib import Path
from fastapi.responses import FileResponse


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Database connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    swagger_ui_parameters={"docExpansion": "none"},
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# Use settings or explicit path
uploads_dir = Path("/app/uploads")  # ← Explicit path

uploads_dir.mkdir(parents=True, exist_ok=True)

print(f"Static dir: {STATIC_DIR}")
print(f"Uploads dir: {uploads_dir}")
print("_+_+_+_+_+_+_+_")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
templates = Jinja2Templates(directory="app/static")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/login",
                    "scopes": {
                        "read": "Read data",
                        "write": "Write data",
                        "admin": "Admin access",
                    },
                }
            },
        }
    }

    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "api.driver-mobile-app.ecolosplus.se",
    ],
)

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(avatar_router.router)
app.include_router(role_router.router)
app.include_router(courier_router.router)
app.include_router(vehicle_routers.router)
app.include_router(terminal_router.router)
app.include_router(hub_shift_router.router)
app.include_router(order_router.router)
app.include_router(scan_router.router)
app.include_router(mission_router.router)
app.include_router(route_router.router)
app.include_router(states_router.router)
app.include_router(billing_router.router)
app.include_router(stripe_webhook_router.router)
app.include_router(utils_router.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "APP_VERSION": os.getenv("APP_VERSION", "unknown"),
            "login_endpoint": "/api/v1/auth/login",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
