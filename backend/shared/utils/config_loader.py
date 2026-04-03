"""
配置文件加载器
支持从YAML文件加载配置，并支持环境变量覆盖
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigLoader:
    """配置加载器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 首先检查环境变量
        config_path = os.getenv("CONFIG_PATH")
        if config_path:
            return Path(config_path)
        
        # 默认路径：项目根目录下的config/config.yaml
        # 从当前文件位置推算项目根目录
        # backend/shared/utils/config_loader.py -> backend -> Demo
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        return project_root / "config" / "config.yaml"
    
    def _load_config(self):
        """加载配置文件"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        # OpenAI配置环境变量
        if os.getenv("OPENAI_API_KEY"):
            self._config["llm"]["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_BASE_URL"):
            self._config["llm"]["openai"]["base_url"] = os.getenv("OPENAI_BASE_URL")
        if os.getenv("OPENAI_MODEL"):
            self._config["llm"]["openai"]["model"] = os.getenv("OPENAI_MODEL")
        
        # 数据库配置环境变量
        if os.getenv("REDIS_HOST"):
            self._config["backend"]["database"]["host"] = os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            self._config["backend"]["database"]["port"] = int(os.getenv("REDIS_PORT"))
        if os.getenv("REDIS_PASSWORD"):
            self._config["backend"]["database"]["password"] = os.getenv("REDIS_PASSWORD")
        
        # JWT配置环境变量
        if os.getenv("JWT_SECRET_KEY"):
            self._config["backend"]["auth"]["secret_key"] = os.getenv("JWT_SECRET_KEY")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔，如 "llm.openai.model"
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self._config.get("llm", {})
    
    def get_backend_config(self) -> Dict[str, Any]:
        """获取后端配置"""
        return self._config.get("backend", {})
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """获取前端配置"""
        return self._config.get("frontend", {})
    
    def get_docker_config(self) -> Dict[str, Any]:
        """获取Docker配置"""
        return self._config.get("docker", {})
    
    def reload(self):
        """重新加载配置"""
        self._load_config()


# 创建全局配置加载器实例
config_loader = ConfigLoader()
