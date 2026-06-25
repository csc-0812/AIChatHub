from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .models import LoginRequest, LoginResponse, User, UserRole, RegisterRequest, CaptchaResponse
from .services import auth_service
from shared.utils.auth_utils import decode_token
from shared.utils.redis_client import redis_client
import random
import uuid
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 注册频率限制配置
REGISTER_LIMIT_WINDOW = 60      # 时间窗口（秒）
REGISTER_LIMIT_MAX = 3           # 窗口内最大注册次数
# 验证码配置
CAPTCHA_TTL = 300                # 验证码有效期（秒），5分钟
CAPTCHA_LENGTH = 4               # 验证码长度


def _get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _generate_captcha_code() -> str:
    """生成随机验证码（数字+大写字母，排除易混淆字符）"""
    chars = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
    return "".join(random.choices(chars, k=CAPTCHA_LENGTH))


@router.get("/captcha", response_model=CaptchaResponse)
async def get_captcha():
    """获取登录/注册验证码"""
    captcha_id = str(uuid.uuid4())
    captcha_text = _generate_captcha_code()
    # 存入 Redis，设置过期时间
    redis_client.set(f"captcha:{captcha_id}", captcha_text, expire=CAPTCHA_TTL)
    return CaptchaResponse(
        captcha_id=captcha_id,
        captcha_text=captcha_text
    )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """用户登录"""
    try:
        access_token, role = auth_service.login(login_data.username, login_data.password)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            username=login_data.username,
            role=role
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=dict)
async def register(user: RegisterRequest, request: Request):
    """用户注册（需验证码，注册后需管理员启用）"""
    # 1. 注册频率限制
    client_ip = _get_client_ip(request)
    rate_key = f"register_limit:{client_ip}"
    count = redis_client.incr(rate_key, expire=REGISTER_LIMIT_WINDOW)
    if count > REGISTER_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"注册频率过高，请{REGISTER_LIMIT_WINDOW}秒后再试"
        )

    # 2. 验证码校验
    stored_captcha = redis_client.get(f"captcha:{user.captcha_id}")
    if stored_captcha is None:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if stored_captcha.upper() != user.captcha_text.strip().upper():
        raise HTTPException(status_code=400, detail="验证码错误")
    # 验证通过后删除验证码，防止重复使用
    redis_client.delete(f"captcha:{user.captcha_id}")

    # 3. 检查用户是否已存在
    existing_user = auth_service.get_user(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 4. 强制设置为普通用户角色，防止通过注册接口提升权限
    new_user = User(
        username=user.username,
        password=user.password,
        email=user.email,
        full_name=user.full_name,
        disabled=True,          # 新注册用户初始为禁用状态
        role=UserRole.USER
    )

    # 5. 创建新用户
    created_user = auth_service.create_user(new_user)
    return {
        "username": created_user.username,
        "email": created_user.email,
        "full_name": created_user.full_name,
        "role": created_user.role.value,
        "disabled": True,
        "message": "注册成功！您的账户已创建，请等待管理员启用后登录使用。"
    }


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    role_str: str = payload.get("role", "user")
    session_id: str = payload.get("session_id")
    if username is None:
        raise credentials_exception

    user = auth_service.get_user(username)
    if user is None:
        raise credentials_exception

    # 检查用户是否被禁用
    if user.disabled:
        raise HTTPException(
            status_code=403,
            detail="用户已被禁用，请联系管理员"
        )

    # 验证会话是否有效（检查是否被挤出）
    if not session_id:
        # 没有session_id的token是旧版token，要求重新登录
        raise HTTPException(
            status_code=401,
            detail="登录已过期，请重新登录"
        )
    if not auth_service.validate_session(username, session_id):
        raise HTTPException(
            status_code=401,
            detail="账号已在其他地方登录"
        )

    # 更新用户角色（从token中获取最新角色）
    user.role = UserRole(role_str)

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not auth_service.is_admin(current_user.username):
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """获取当前超级管理员用户"""
    if not auth_service.is_super_admin(current_user.username):
        raise HTTPException(
            status_code=403,
            detail="需要超级管理员权限"
        )
    return current_user


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "disabled": current_user.disabled,
        "role": current_user.role.value
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户退出登录"""
    auth_service.logout(current_user.username)
    return {"message": "退出登录成功"}
