from fastapi import APIRouter
from .v1 import router as v1_router

router = APIRouter(prefix="/api")

# 注册版本路由
router.include_router(v1_router)
