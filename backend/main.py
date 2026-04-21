from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api import router as api_router
from skills import load_skills_from_directory

# 初始化技能加载
skills_dir = Path(__file__).parent / "skills" / "skills_dir"
load_skills_from_directory(str(skills_dir))

app = FastAPI(
    title="AI Chat Hub",
    description="Backend API for AI Chat Hub project",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router)

# 配置静态文件服务（用于访问上传的文件）
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {"message": "Welcome to Demo API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

