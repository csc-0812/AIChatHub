"""
模型配置服务
提供多模型管理和切换功能（支持同时启用多个模型）
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
    
    def _get_models_from_redis(self) -> List[LLMModelConfig]:
        """从Redis获取所有模型配置"""
        try:
            models_data = self.redis.get(self.models_key)
            if not models_data:
                return []

            models_list = json.loads(models_data)
            result = []
            needs_resave = False
            for model_data in models_list:
                try:
                    result.append(LLMModelConfig(**model_data))
                except Exception:
                    # 兼容旧格式：datetime 可能以空格分隔（str() 序列化），修复为 ISO 8601
                    fixed = self._fix_datetime_format(model_data)
                    if fixed:
                        try:
                            result.append(LLMModelConfig(**fixed))
                            needs_resave = True
                            models_logger.info(f"已修复模型 '{fixed.get('name', 'unknown')}' 的日期格式")
                        except Exception as parse_err:
                            models_logger.warning(f"解析单个模型配置失败（跳过）: {parse_err}, name={model_data.get('name', 'unknown')}")
                    else:
                        models_logger.warning(f"解析单个模型配置失败（跳过）: name={model_data.get('name', 'unknown')}")
            # 如果有修复的数据，重新保存
            if needs_resave:
                self._save_models_to_redis(result)
            return result
        except Exception as e:
            models_logger.error(f"从Redis获取模型配置失败: {e}")
            return []
    
    def _fix_datetime_format(self, model_data: dict) -> Optional[dict]:
        """修复旧版 datetime 格式（空格分隔 → ISO 8601 T 分隔）"""
        fixed = dict(model_data)
        needs_fix = False
        for key in ("created_at", "updated_at"):
            val = fixed.get(key)
            if isinstance(val, str) and " " in val and "T" not in val:
                # "2025-06-11 17:19:30.123456" → "2025-06-11T17:19:30.123456"
                fixed[key] = val.replace(" ", "T", 1)
                needs_fix = True
        return fixed if needs_fix else None
    
    def _save_models_to_redis(self, models: List[LLMModelConfig]):
        """保存模型配置到Redis（使用 mode='json' 确保 datetime 序列化为 ISO 8601 格式）"""
        models_list = [model.model_dump(mode='json') for model in models]
        self.redis.set(
            self.models_key,
            json.dumps(models_list),
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

        # 转换为响应格式（隐藏API密钥）
        # 每个模型的 is_active 字段即为其真实启用状态
        models_response = []
        for model in models:
            model_dict = model.model_dump()
            model_dict["api_key"] = "******" if model.api_key else ""
            models_response.append(model_dict)

        enabled_ids = [m.id for m in models if m.is_active]

        return {
            "models": models_response,
            "enabled_model_ids": enabled_ids,
            "count": len(models)
        }
    
    def get_active_model(self) -> Optional[LLMModelConfig]:
        """获取当前启用的模型配置（返回第一个启用的模型，用于默认聊天）"""
        models = self._get_models_from_redis()
        for model in models:
            if model.is_active:
                return model
        return None
    
    def get_enabled_models(self) -> List[LLMModelConfig]:
        """获取所有已启用的模型"""
        models = self._get_models_from_redis()
        return [m for m in models if m.is_active]
    
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
        model_exists = any(m.id == model_id for m in models)
        if not model_exists:
            return False
        
        # 删除模型
        models = [m for m in models if m.id != model_id]
        self._save_models_to_redis(models)
        
        return True
    
    def set_model_enabled(self, model_id: str, enabled: bool) -> bool:
        """
        设置模型的启用/禁用状态（支持同时启用多个模型）
        
        Args:
            model_id: 模型ID
            enabled: True=启用, False=禁用
            
        Returns:
            是否操作成功
        """
        models = self._get_models_from_redis()
        
        for model in models:
            if model.id == model_id:
                model.is_active = enabled
                model.updated_at = datetime.now()
                self._save_models_to_redis(models)
                return True
        
        return False
    
    def get_model_by_id(self, model_id: str) -> Optional[LLMModelConfig]:
        """根据ID获取模型配置"""
        models = self._get_models_from_redis()
        for model in models:
            if model.id == model_id:
                return model
        return None

    def get_models_for_selection(self) -> Dict[str, Any]:
        """获取已启用模型选择列表（不含敏感信息，所有用户可访问）"""
        models = self._get_models_from_redis()

        # 如果没有数据，尝试从配置文件初始化
        if not models:
            default_model = self._init_default_model_from_config()
            if default_model:
                models = [default_model]

        # 只返回已启用的模型
        selection = []
        for model in models:
            if not model.is_active:
                continue
            selection.append({
                "id": model.id,
                "name": model.name,
                "model": model.model,
                "is_active": model.is_active,
                "description": model.description
            })

        return {
            "models": selection,
            "count": len(selection)
        }


# 创建服务实例
models_config_service = ModelsConfigService()
