"""
模型配置服务
提供多模型管理和切换功能
"""
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from shared.utils.redis_client import redis_client
from shared.utils.config_loader import config_loader
from shared.utils.logger import models_logger
from .models import LLMModelConfig


class ModelsConfigService:
    """模型配置服务"""
    
    def __init__(self):
        self.redis = redis_client
        self.models_key = "llm:models"
        self.active_model_key = "llm:active_model"
    
    def _get_models_from_redis(self) -> List[LLMModelConfig]:
        """从Redis获取所有模型配置"""
        try:
            models_data = self.redis.get(self.models_key)
            if not models_data:
                return []

            models_list = json.loads(models_data)
            return [LLMModelConfig(**model) for model in models_list]
        except Exception as e:
            models_logger.error(f"从Redis获取模型配置失败: {e}")
            # 数据损坏，清除Redis中的数据
            try:
                self.redis.delete(self.models_key)
                self.redis.delete(self.active_model_key)
                models_logger.info("已清除损坏的模型配置数据")
            except Exception as del_e:
                models_logger.error(f"清除损坏数据失败: {del_e}")
            return []
    
    def _save_models_to_redis(self, models: List[LLMModelConfig]):
        """保存模型配置到Redis"""
        models_list = [model.model_dump() for model in models]
        self.redis.set(
            self.models_key,
            json.dumps(models_list, default=str),
            expire=30 * 24 * 3600  # 30天过期
        )
    
    def _init_default_model_from_config(self) -> Optional[LLMModelConfig]:
        """从配置文件初始化默认模型"""
        try:
            llm_config = config_loader.get_llm_config()
            openai_config = llm_config.get("openai", {})
            
            if not openai_config.get("api_key"):
                return None
            
            model = LLMModelConfig(
                id=str(uuid.uuid4()),
                name="默认配置",
                provider="openai",
                model=openai_config.get("model", "gpt-3.5-turbo"),
                base_url=openai_config.get("base_url", "https://api.openai.com/v1"),
                api_key=openai_config.get("api_key", ""),
                temperature=openai_config.get("temperature", 0.7),
                max_tokens=openai_config.get("max_tokens", 2048),
                is_active=True,
                description="从配置文件加载的默认模型",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到Redis
            self._save_models_to_redis([model])
            self.redis.set(self.active_model_key, model.id, expire=30 * 24 * 3600)
            
            return model
        except Exception as e:
            models_logger.error(f"从配置文件初始化模型失败: {e}")
            return None
    
    def get_all_models(self) -> Dict[str, Any]:
        """获取所有模型配置"""
        models_logger.info("开始获取模型配置")
        models = self._get_models_from_redis()
        models_logger.info(f"从Redis获取到 {len(models)} 个模型")

        # 如果没有数据，尝试从配置文件初始化
        if not models:
            models_logger.info("Redis中没有模型，尝试从配置文件初始化")
            default_model = self._init_default_model_from_config()
            if default_model:
                models = [default_model]
                models_logger.info(f"从配置文件初始化成功: {default_model.name}")
            else:
                models_logger.warning("从配置文件初始化失败")

        # 获取当前启用的模型ID
        active_model_id = self.redis.get(self.active_model_key)
        models_logger.info(f"当前启用模型ID: {active_model_id}")

        # 转换为响应格式（隐藏API密钥）
        # 根据 active_model_id 动态设置 is_active 字段
        models_response = []
        for model in models:
            model_dict = model.model_dump()
            model_dict["api_key"] = "******" if model.api_key else ""
            # 动态计算 is_active，以 active_model_key 为准
            model_dict["is_active"] = (model.id == active_model_id)
            models_response.append(model_dict)

        return {
            "models": models_response,
            "active_model_id": active_model_id,
            "count": len(models)
        }
    
    def get_active_model(self) -> Optional[LLMModelConfig]:
        """获取当前启用的模型配置"""
        active_model_id = self.redis.get(self.active_model_key)
        if not active_model_id:
            return None
        
        models = self._get_models_from_redis()
        for model in models:
            if model.id == active_model_id:
                return model
        
        return None
    
    def create_model(self, model_data: Dict[str, Any]) -> LLMModelConfig:
        """创建新模型配置"""
        models = self._get_models_from_redis()

        # 清理数据，provider 固定为 openai
        clean_data = {
            "name": model_data.get("name"),
            "provider": "openai",  # 固定为 openai
            "model": model_data.get("model"),
            "base_url": model_data.get("base_url"),
            "api_key": model_data.get("api_key"),
            "temperature": model_data.get("temperature", 0.7),
            "max_tokens": model_data.get("max_tokens", 2048),
            "description": model_data.get("description")
        }
        
        # 创建新模型
        new_model = LLMModelConfig(
            id=str(uuid.uuid4()),
            **clean_data,
            is_active=False,  # 新模型默认不启用
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        models.append(new_model)
        self._save_models_to_redis(models)
        
        return new_model
    
    def update_model(self, model_id: str, update_data: Dict[str, Any]) -> Optional[LLMModelConfig]:
        """更新模型配置"""
        models = self._get_models_from_redis()
        
        for i, model in enumerate(models):
            if model.id == model_id:
                # 更新字段
                for key, value in update_data.items():
                    if value is not None and hasattr(model, key):
                        setattr(model, key, value)
                
                model.updated_at = datetime.now()
                models[i] = model
                self._save_models_to_redis(models)
                return model
        
        return None
    
    def delete_model(self, model_id: str) -> bool:
        """删除模型配置"""
        models = self._get_models_from_redis()
        
        # 查找要删除的模型
        model_to_delete = None
        for model in models:
            if model.id == model_id:
                model_to_delete = model
                break
        
        if not model_to_delete:
            return False
        
        # 如果删除的是当前启用的模型，需要清除启用状态
        active_model_id = self.redis.get(self.active_model_key)
        if active_model_id == model_id:
            self.redis.delete(self.active_model_key)
        
        # 删除模型
        models = [m for m in models if m.id != model_id]
        self._save_models_to_redis(models)
        
        return True
    
    def set_active_model(self, model_id: str) -> bool:
        """设置启用的模型"""
        models = self._get_models_from_redis()
        
        # 验证模型是否存在
        model_exists = any(m.id == model_id for m in models)
        if not model_exists:
            return False
        
        # 更新所有模型的启用状态
        for model in models:
            model.is_active = (model.id == model_id)
        
        self._save_models_to_redis(models)
        self.redis.set(self.active_model_key, model_id, expire=30 * 24 * 3600)
        
        return True
    
    def get_model_by_id(self, model_id: str) -> Optional[LLMModelConfig]:
        """根据ID获取模型配置"""
        models = self._get_models_from_redis()
        for model in models:
            if model.id == model_id:
                return model
        return None


# 创建服务实例
models_config_service = ModelsConfigService()
