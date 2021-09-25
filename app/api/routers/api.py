from fastapi import APIRouter

from app.api.routers import status,data_import,report

# Collect all routers here
router = APIRouter(prefix='/scalable-capital-reporting-service')

router.include_router(status.router)
router.include_router(data_import.router)
router.include_router(report.router)