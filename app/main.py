"""
ApnaPG — Trust-Based Student Housing Platform
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# ── Application instance ────────────────────────────────────────
app = FastAPI(
    title="ApnaPG API",
    description=(
        "Backend API for ApnaPG — a broker-free, trust-based student "
        "housing platform connecting verified property owners with "
        "student tenants."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (open for development — tighten in production) ────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """Basic liveness probe."""
    return {"status": "healthy", "service": "apnapg-api", "version": "1.0.0"}


# ── API Routers ─────────────────────────────────────────────────
from app.api import users, properties, connections, reviews, documents

app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(properties.router,  prefix="/api/properties",  tags=["Properties"])
app.include_router(connections.router, prefix="/api/connections", tags=["Connections"])
app.include_router(reviews.router,     prefix="/api/reviews",     tags=["Reviews"])
app.include_router(documents.router,   prefix="/api/documents",   tags=["Documents"])

