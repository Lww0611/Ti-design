from fastapi import APIRouter
# ✅ 显式从 api.v1 导入，防止名称冲突
from api.v1.auth import router as auth_router
from api.v1.predictions import router as predictions_router
from api.v1.datasets import router as datasets_router
from api.v1.tasks import router as tasks_router
from api.v1.model_manager import model_manager_router as model_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(predictions_router)
api_router.include_router(datasets_router)
api_router.include_router(tasks_router)
api_router.include_router(model_router)