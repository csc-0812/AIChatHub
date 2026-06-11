from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import hashlib
import uuid
from shared.utils.config_loader import config_loader


def _get_auth_config() -> dict:
    """获取认证配置"""
    return config_loader.get("backend.auth", {})


def _get_secret_key() -> str:
    return _get_auth_config().get("secret_key", "your-secret-key-change-this-in-production")


def _get_algorithm() -> str:
    return _get_auth_config().get("algorithm", "HS256")


def _get_token_expire_minutes() -> int:
    return _get_auth_config().get("access_token_expire_minutes", 30)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    hashed = hashlib.sha256(plain_password.encode()).hexdigest()
    return hashed == hashed_password


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=_get_token_expire_minutes())
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=_get_algorithm())
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[_get_algorithm()])
        return payload
    except JWTError:
        return None


def generate_session_id() -> str:
    """生成唯一会话ID"""
    return str(uuid.uuid4())
