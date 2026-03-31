"""
PM Digital Employee - LLM Gateway
项目经理数字员工系统 - LLM统一网关

提供统一的LLM调用接口，支持多提供商、重试、限流、审计。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx

from app.ai.schemas import (
    ChatMessage,
    ChatRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsageRecord,
)
from app.core.config import settings
from app.core.exceptions import ErrorCode, LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMGateway:
    """
    LLM统一网关.

    提供统一的LLM调用接口，支持：
    - 多提供商（OpenAI、Azure、智谱、通义千问等）
    - 重试机制
    - 限流控制
    - Token统计
    - 审计日志
    """

    def __init__(self) -> None:
        """初始化LLM网关."""
        self._http_client: Optional[httpx.AsyncClient] = None
        self._provider_configs = self._load_provider_configs()
        self._usage_stats: Dict[str, List[LLMUsageRecord]] = {}

    def _load_provider_configs(self) -> Dict[LLMProvider, Dict[str, Any]]:
        """
        加载提供商配置.

        Returns:
            Dict: 提供商配置映射
        """
        return {
            LLMProvider.OPENAI: {
                "api_base": settings.llm.openai_api_base or "https://api.openai.com/v1",
                "api_key": settings.llm.openai_api_key,
                "default_model": settings.llm.openai_model,
            },
            LLMProvider.AZURE: {
                "api_base": settings.llm.azure_api_base,
                "api_key": settings.llm.azure_api_key,
                "api_version": settings.llm.azure_api_version,
                "default_model": settings.llm.azure_deployment,
            },
            LLMProvider.ZHIPU: {
                "api_base": "https://open.bigmodel.cn/api/paas/v3",
                "api_key": settings.llm.zhipu_api_key,
                "default_model": "glm-4",
            },
            LLMProvider.QWEN: {
                "api_base": "https://dashscope.aliyuncs.com/api/v1",
                "api_key": settings.llm.qwen_api_key,
                "default_model": "qwen-max",
            },
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.llm.timeout),
                follow_redirects=True,
            )
        return self._http_client

    async def close(self) -> None:
        """关闭客户端."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        provider: LLMProvider = LLMProvider.OPENAI,
        **kwargs,
    ) -> LLMResponse:
        """
        生成文本.

        Args:
            prompt: 用户Prompt
            model: 模型名称
            max_tokens: 最大输出Token
            temperature: 温度
            system_prompt: 系统Prompt
            conversation_history: 对话历史
            provider: 提供商
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成响应

        Raises:
            LLMError: 生成失败
        """
        start_time = time.time()

        # 构建消息列表
        messages = self._build_messages(
            prompt=prompt,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
        )

        # 构建请求
        request = LLMRequest(
            prompt=prompt,
            model=model or self._get_default_model(provider),
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            conversation_history=conversation_history or [],
            metadata=kwargs,
        )

        try:
            # 调用LLM API
            response = await self._call_llm_api(
                provider=provider,
                messages=messages,
                model=request.model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            # 计算延迟
            latency_ms = int((time.time() - start_time) * 1000)
            response.latency_ms = latency_ms

            # 记录使用日志
            self._log_usage(
                trace_id=kwargs.get("trace_id", ""),
                user_id=kwargs.get("user_id", ""),
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=latency_ms,
                skill_name=kwargs.get("skill_name"),
                success=True,
            )

            logger.info(
                "LLM generation completed",
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=latency_ms,
            )

            return response

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            self._log_usage(
                trace_id=kwargs.get("trace_id", ""),
                user_id=kwargs.get("user_id", ""),
                model=request.model,
                latency_ms=latency_ms,
                skill_name=kwargs.get("skill_name"),
                success=False,
                error_message=str(e),
            )

            logger.error(
                "LLM generation failed",
                model=request.model,
                error=str(e),
            )

            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"LLM生成失败: {str(e)}",
                model=request.model,
            )

    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        provider: LLMProvider = LLMProvider.OPENAI,
        **kwargs,
    ) -> LLMResponse:
        """
        聊天接口.

        Args:
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大输出Token
            temperature: 温度
            provider: 提供商
            **kwargs: 其他参数

        Returns:
            LLMResponse: 聊天响应
        """
        start_time = time.time()

        try:
            response = await self._call_llm_api(
                provider=provider,
                messages=[m.model_dump() for m in messages],
                model=model or self._get_default_model(provider),
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            response.latency_ms = int((time.time() - start_time) * 1000)

            return response

        except Exception as e:
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"聊天请求失败: {str(e)}",
            )

    async def _call_llm_api(
        self,
        provider: LLMProvider,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        retry_count: int = 0,
        **kwargs,
    ) -> LLMResponse:
        """
        调用LLM API.

        Args:
            provider: 提供商
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大Token
            temperature: 温度
            retry_count: 当前重试次数
            **kwargs: 其他参数

        Returns:
            LLMResponse: API响应
        """
        config = self._provider_configs.get(provider)
        if not config or not config.get("api_key"):
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"提供商 {provider} 未配置",
            )

        client = await self._get_client()

        try:
            if provider == LLMProvider.OPENAI:
                return await self._call_openai(
                    client, config, messages, model, max_tokens, temperature,
                )
            elif provider == LLMProvider.AZURE:
                return await self._call_azure(
                    client, config, messages, model, max_tokens, temperature,
                )
            elif provider == LLMProvider.ZHIPU:
                return await self._call_zhipu(
                    client, config, messages, model, max_tokens, temperature,
                )
            elif provider == LLMProvider.QWEN:
                return await self._call_qwen(
                    client, config, messages, model, max_tokens, temperature,
                )
            else:
                raise LLMError(
                    error_code=ErrorCode.LLM_ERROR,
                    message=f"不支持的提供商: {provider}",
                )

        except httpx.TimeoutException:
            if retry_count < settings.llm.retry_count:
                await asyncio.sleep(settings.llm.retry_delay * (retry_count + 1))
                return await self._call_llm_api(
                    provider, messages, model, max_tokens, temperature,
                    retry_count + 1, **kwargs,
                )
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message="LLM请求超时",
            )

        except httpx.RequestError as e:
            if retry_count < settings.llm.retry_count:
                await asyncio.sleep(settings.llm.retry_delay * (retry_count + 1))
                return await self._call_llm_api(
                    provider, messages, model, max_tokens, temperature,
                    retry_count + 1, **kwargs,
                )
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"LLM请求失败: {str(e)}",
            )

    async def _call_openai(
        self,
        client: httpx.AsyncClient,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """
        调用OpenAI API.

        Args:
            client: HTTP客户端
            config: 配置
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大Token
            temperature: 温度

        Returns:
            LLMResponse: 响应
        """
        url = f"{config['api_base']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await client.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code != 200:
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"OpenAI API错误: {data.get('error', {}).get('message', 'Unknown')}",
            )

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            request_id=data.get("id"),
        )

    async def _call_azure(
        self,
        client: httpx.AsyncClient,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """
        调用Azure OpenAI API.

        Args:
            client: HTTP客户端
            config: 配置
            messages: 消息列表
            model: 模型名称（部署名）
            max_tokens: 最大Token
            temperature: 温度

        Returns:
            LLMResponse: 响应
        """
        url = f"{config['api_base']}/openai/deployments/{model}/chat/completions"
        url += f"?api-version={config.get('api_version', '2024-02-15-preview')}"

        headers = {
            "api-key": config["api_key"],
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await client.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code != 200:
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"Azure API错误: {data.get('error', {}).get('message', 'Unknown')}",
            )

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def _call_zhipu(
        self,
        client: httpx.AsyncClient,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """
        调用智谱AI API.

        Args:
            client: HTTP客户端
            config: 配置
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大Token
            temperature: 温度

        Returns:
            LLMResponse: 响应
        """
        url = f"{config['api_base']}/model-api/{model}/inference"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await client.post(url, headers=headers, json=payload)
        data = response.json()

        if data.get("code") != 200:
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"智谱API错误: {data.get('msg', 'Unknown')}",
            )

        choice = data["data"]["choices"][0]
        usage = data["data"].get("usage", {})

        return LLMResponse(
            content=choice["content"],
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def _call_qwen(
        self,
        client: httpx.AsyncClient,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """
        调用通义千问API.

        Args:
            client: HTTP客户端
            config: 配置
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大Token
            temperature: 温度

        Returns:
            LLMResponse: 响应
        """
        url = f"{config['api_base']}/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        # 转换消息格式
        input_text = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                input_text += f"系统: {content}\n"
            elif role == "user":
                input_text += f"用户: {content}\n"
            elif role == "assistant":
                input_text += f"助手: {content}\n"

        payload = {
            "model": model,
            "input": {"prompt": input_text},
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        }

        response = await client.post(url, headers=headers, json=payload)
        data = response.json()

        if data.get("code"):
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"通义千问API错误: {data.get('message', 'Unknown')}",
            )

        output = data.get("output", {})
        usage = data.get("usage", {})

        return LLMResponse(
            content=output.get("text", ""),
            model=model,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=output.get("finish_reason", "stop"),
        )

    async def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002",
        provider: LLMProvider = LLMProvider.OPENAI,
    ) -> List[float]:
        """
        获取文本Embedding.

        Args:
            text: 输入文本
            model: 模型名称
            provider: 提供商

        Returns:
            List[float]: Embedding向量
        """
        config = self._provider_configs.get(provider)
        if not config:
            raise LLMError(
                error_code=ErrorCode.LLM_ERROR,
                message=f"提供商 {provider} 未配置",
            )

        client = await self._get_client()

        if provider == LLMProvider.OPENAI:
            url = f"{config['api_base']}/embeddings"
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "input": text,
            }

            response = await client.post(url, headers=headers, json=payload)
            data = response.json()

            if response.status_code != 200:
                raise LLMError(
                    error_code=ErrorCode.LLM_ERROR,
                    message="Embedding请求失败",
                )

            return data["data"][0]["embedding"]

        raise LLMError(
            error_code=ErrorCode.LLM_ERROR,
            message=f"提供商 {provider} 暂不支持Embedding",
        )

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        """
        构建消息列表.

        Args:
            prompt: 用户Prompt
            system_prompt: 系统Prompt
            conversation_history: 对话历史

        Returns:
            List: 消息列表
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": prompt})

        return messages

    def _get_default_model(self, provider: LLMProvider) -> str:
        """
        获取默认模型.

        Args:
            provider: 提供商

        Returns:
            str: 默认模型名称
        """
        config = self._provider_configs.get(provider, {})
        return config.get("default_model", "gpt-4")

    def _log_usage(
        self,
        trace_id: str,
        user_id: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: int = 0,
        skill_name: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """
        记录使用日志.

        Args:
            trace_id: 追踪ID
            user_id: 用户ID
            model: 模型名称
            prompt_tokens: 输入Token
            completion_tokens: 输出Token
            latency_ms: 延迟
            skill_name: Skill名称
            success: 是否成功
            error_message: 错误信息
        """
        record = LLMUsageRecord(
            trace_id=trace_id,
            user_id=user_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            skill_name=skill_name,
            success=success,
            error_message=error_message,
        )

        # 按用户记录
        if user_id not in self._usage_stats:
            self._usage_stats[user_id] = []
        self._usage_stats[user_id].append(record)


# 全局LLM网关实例
_llm_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """获取LLM网关实例."""
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
    return _llm_gateway