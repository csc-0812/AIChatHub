from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import hashlib
import uuid

# 配置
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 使用SHA-256哈希密码
    hashed = hashlib.sha256(plain_password.encode()).hexdigest()
    return hashed == hashed_password

def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    # 使用SHA-256哈希密码
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_session_id() -> str:
    """生成唯一会话ID"""
    return str(uuid.uuid4())