from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api import router as api_router
from shared.utils.config_loader import config_loader

# 从配置文件读取应用信息
app_config = config_loader.get("app", {})
backend_config = config_loader.get("backend", {})

app = FastAPI(
    title=app_config.get("name", "AIChatHub API"),
    description="Backend API for Plan Integration Platform AI",
    version=app_config.get("version", "1.0.0"),
    debug=app_config.get("debug", False),
)

# 配置 CORS（从配置文件读取允许的来源）
# 注意：当 allow_credentials=True 时，allow_origins 不能使用 "*"
cors_origins = backend_config.get("cors_origins", ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
)

# 注册 API 路由
app.include_router(api_router)

# 配置静态文件服务（用于访问上传的文件）
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    return {"message": f"Welcome to {app_config.get('name', 'AIChatHub')} API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
