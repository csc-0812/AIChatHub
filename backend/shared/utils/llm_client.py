"""
大语言模型客户端封装
使用LangChain封装OpenAI模型
"""
from typing import Optional, List, Dict, Any, AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from .config_loader import config_loader
from .logger import llm_logger


class LLMClient:
    """大语言模型客户端"""

    def __init__(self):
        self.config = config_loader.get_llm_config()
        self._model = None
        self._current_model_config = None
        # 延迟初始化，不在构造函数中立即初始化模型

    def _get_model_config(self) -> Dict[str, Any]:
        """获取模型配置，优先使用管理员配置的启用模型"""
        try:
            # 尝试从 models_config_service 获取启用的模型
            from modules.models_config.services import models_config_service
            active_model = models_config_service.get_active_model()
            if active_model:
                return {
                    "model": active_model.model,
                    "model_provider": active_model.provider,
                    "api_key": active_model.api_key,
                    "base_url": active_model.base_url,
                    "temperature": active_model.temperature,
                    "max_tokens": active_model.max_tokens,
                    "timeout": self.config.get("request_timeout", 60),
                    "max_retries": self.config.get("max_retries", 3)
                }
        except Exception as e:
            llm_logger.warning(f"从models_config获取模型配置失败: {e}")

        # 回退到配置文件
        openai_config = self.config.get("openai", {})
        return {
            "model": openai_config.get("model", "gpt-3.5-turbo"),
            "model_provider": "openai",
            "api_key": openai_config.get("api_key"),
            "base_url": openai_config.get("base_url"),
            "temperature": openai_config.get("temperature", 0.7),
            "max_tokens": openai_config.get("max_tokens", 2048),
            "timeout": self.config.get("request_timeout", 60),
            "max_retries": self.config.get("max_retries", 3)
        }

    def _get_model_config_hash(self, config: Dict[str, Any]) -> str:
        """获取模型配置的哈希值，用于判断配置是否变化"""
        import hashlib
        config_str = f"{config.get('model')}:{config.get('model_provider')}:{config.get('base_url')}:{config.get('api_key')}:{config.get('temperature')}:{config.get('max_tokens')}"
        return hashlib.md5(config_str.encode()).hexdigest()

    def _ensure_model_initialized(self):
        """确保模型已初始化，如果配置变化则重新初始化"""
        latest_config = self._get_model_config()
        latest_config_hash = self._get_model_config_hash(latest_config)

        # 如果模型未初始化或配置发生变化，重新初始化
        if self._model is None or self._current_model_config != latest_config_hash:
            llm_logger.info(f"模型配置变化，重新初始化模型: {latest_config.get('model')}")
            self._initialize_model_with_config(latest_config)
            self._current_model_config = latest_config_hash

    def _initialize_model_with_config(self, model_config: Dict[str, Any]):
        """使用指定配置初始化模型"""
        # 打印当前使用的模型参数
        llm_logger.info("=" * 50)
        llm_logger.info("初始化大语言模型")
        llm_logger.info(f"  模型: {model_config.get('model')}")
        llm_logger.info(f"  提供商: {model_config.get('model_provider', 'openai')}")
        llm_logger.info(f"  Base URL: {model_config.get('base_url')}")
        llm_logger.info(f"  Temperature: {model_config.get('temperature', 0.7)}")
        llm_logger.info(f"  Max Tokens: {model_config.get('max_tokens', 2048)}")
        llm_logger.info(f"  Timeout: {model_config.get('timeout', 60)}s")
        llm_logger.info(f"  Max Retries: {model_config.get('max_retries', 3)}")
        llm_logger.info("=" * 50)

        self._model = init_chat_model(
            model=model_config["model"],
            model_provider=model_config.get("model_provider", "openai"),
            api_key=model_config.get("api_key"),
            base_url=model_config.get("base_url"),
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 2048),
            timeout=model_config.get("timeout", 60),
            max_retries=model_config.get("max_retries", 3)
        )

        # 设置详细日志
        self._model.set_verbose(True)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        同步聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user/system/assistant", "content": "消息内容"}]

        Returns:
            AI的回复内容
        """
        # 确保模型已初始化（检查配置是否有变化）
        self._ensure_model_initialized()

        if not self._model:
            raise RuntimeError("LLM未初始化")

        # 转换消息格式
        langchain_messages = self._convert_messages(messages)

        # 调用模型
        response = self._model.invoke(langchain_messages)

        return response.content

    async def achat(self, messages: List[Dict[str, str]]) -> str:
        """
        异步聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user/system/assistant", "content": "消息内容"}]

        Returns:
            AI的回复内容
        """
        # 确保模型已初始化（检查配置是否有变化）
        self._ensure_model_initialized()

        if not self._model:
            raise RuntimeError("LLM未初始化")

        # 转换消息格式
        langchain_messages = self._convert_messages(messages)

        # 异步调用模型
        response = await self._model.ainvoke(langchain_messages)

        return response.content

    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        流式聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user/system/assistant", "content": "消息内容"}]

        Yields:
            AI回复的每个token
        """
        # 确保模型已初始化（检查配置是否有变化）
        self._ensure_model_initialized()

        if not self._model:
            raise RuntimeError("LLM未初始化")

        # 转换消息格式
        langchain_messages = self._convert_messages(messages)

        # 流式调用模型
        async for chunk in self._model.astream(langchain_messages):
            if chunk.content:
                yield chunk.content

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Any]:
        """将标准消息格式转换为LangChain消息格式"""
        langchain_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        简单聊天接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词（可选）

        Returns:
            AI的回复内容
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages)


# 创建全局LLM客户端实例（延迟初始化，不立即调用初始化方法）
llm_client = LLMClient()
