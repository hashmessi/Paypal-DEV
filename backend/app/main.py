"""FastAPI Application entry point for PromiseLoop backend."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.checkout import router as checkout_router
from app.api.console import router as console_router
from app.api.demo import router as demo_router
from app.api.discovery import router as discovery_router
from app.api.fulfillment import router as fulfillment_router
from app.api.gate import router as gate_router
from app.api.intent import router as intent_router
from app.api.ledger import router as ledger_router
from app.api.payments import router as payments_router
from app.api.receipts import router as receipts_router
from app.api.replay import router as replay_router
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("promiseloop")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PromiseLoop database tables...")
    init_db()
    logger.info("PromiseLoop backend initialized successfully.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Promise-Gated Payments for Agentic Commerce — Financial Backbone & State Machine",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# Include Routers with both direct and /api prefixes for client compatibility
for prefix in ("", "/api"):
    app.include_router(checkout_router, prefix=prefix)
    app.include_router(payments_router, prefix=prefix)
    app.include_router(ledger_router, prefix=prefix)
    app.include_router(webhooks_router, prefix=prefix)
    app.include_router(demo_router, prefix=prefix)
    app.include_router(intent_router, prefix=prefix)
    app.include_router(discovery_router, prefix=prefix)
    app.include_router(receipts_router, prefix=prefix)
    app.include_router(fulfillment_router, prefix=prefix)
    app.include_router(gate_router, prefix=prefix)
    app.include_router(replay_router, prefix=prefix)
    app.include_router(console_router, prefix=prefix)

