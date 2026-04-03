from fastapi import APIRouter

# 导入业务模块路由
from modules.auth.routers import router as auth_router
from modules.chat.routers import router as chat_router
from modules.admin.routers import router as admin_router
from modules.models_config.routers import router as models_config_router

# 创建 API 路由器
api_router = APIRouter(prefix="/v1")

# 注册业务模块路由
api_router.include_router(auth_router, tags=["认证管理"])
api_router.include_router(chat_router, tags=["聊天"])
api_router.include_router(admin_router, tags=["管理员"])
api_router.include_router(models_config_router, tags=["模型配置"])

# 导出路由器
router = api_router
