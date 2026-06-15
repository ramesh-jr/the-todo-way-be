"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.calendar import router as calendar_router
from app.api.v1.routes.data import router as data_router
from app.api.v1.routes.domains import router as domains_router
from app.api.v1.routes.items import router as items_router
from app.api.v1.routes.nudges import router as nudges_router
from app.api.v1.routes.onboarding import router as onboarding_router
from app.api.v1.routes.priorities import router as priorities_router
from app.api.v1.routes.push import router as push_router
from app.api.v1.routes.review import router as review_router
from app.api.v1.routes.routines import router as routines_router
from app.api.v1.routes.standards import router as standards_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
v1_router.include_router(items_router, prefix="/items", tags=["items"])
v1_router.include_router(domains_router, prefix="/domains", tags=["domains"])
v1_router.include_router(standards_router, prefix="/standards", tags=["standards"])
v1_router.include_router(priorities_router, prefix="/priorities", tags=["priorities"])
v1_router.include_router(routines_router, prefix="/routines", tags=["routines"])
v1_router.include_router(review_router, prefix="/review", tags=["review"])
v1_router.include_router(nudges_router, prefix="/nudges", tags=["nudges"])
v1_router.include_router(data_router, prefix="/data", tags=["data"])
v1_router.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
v1_router.include_router(push_router, prefix="/push", tags=["push"])
v1_router.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
