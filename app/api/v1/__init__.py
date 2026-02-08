"""API v1 router aggregation."""

from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

# Sub-routers will be registered here as they are implemented:
# from app.api.v1.routes.auth import router as auth_router
# from app.api.v1.routes.todos import router as todos_router
# from app.api.v1.routes.sections import router as sections_router
# from app.api.v1.routes.labels import router as labels_router
#
# v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
# v1_router.include_router(todos_router, prefix="/todos", tags=["todos"])
# v1_router.include_router(sections_router, tags=["sections"])
# v1_router.include_router(labels_router, prefix="/labels", tags=["labels"])
