"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import v1_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.schemas.response import ApiResponse

app = FastAPI(
    title="The Todo Way",
    description="Backend API for The Todo Way productivity app",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convert AppException into a standard ApiResponse error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(data=None, error=exc.detail).model_dump(),
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(v1_router)

# ---------------------------------------------------------------------------
# Mangum handler for AWS Lambda
# ---------------------------------------------------------------------------
handler = None
if settings.environment != "local":
    from mangum import Mangum

    handler = Mangum(app)
