"""
PM Digital Employee - Safety Guard
项目经理数字员工系统 - AI安全防护模块

实现提示词注入检测、内容合规检查、敏感数据过滤等安全防护。
"""

import re
from typing import Any, Dict, List, Optional, Set

from app.ai.schemas import (
    ContentComplianceResult,
    PromptInjectionCheckResult,
    SafetyCheckResult,
)
from app.core.config import settings
from app.core.exceptions import ErrorCode, SafetyViolationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SafetyGuard:
    """
    AI安全防护模块.

    实现多层次安全防护：
    - 提示词注入检测
    - 敏感内容过滤
    - 数据脱敏
    - 输出内容合规检查
    """

    def __init__(self) -> None:
        """初始化安全防护模块."""
        # 提示词注入模式
        self._injection_patterns = self._load_injection_patterns()

        # 敏感词列表
        self._sensitive_words = self._load_sensitive_words()

        # PII模式
        self._pii_patterns = self._load_pii_patterns()

        # 合规类别
        self._compliance_categories = [
            "violence",
            "hate_speech",
            "sexual_content",
            "harassment",
            "illegal_activity",
            "self_harm",
            "misinformation",
        ]

    def _load_injection_patterns(self) -> List[re.Pattern]:
        """
        加载提示词注入检测模式.

        Returns:
            List: 正则表达式模式列表
        """
        patterns = [
            # 忽略之前的指令
            re.compile(
                r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
                re.IGNORECASE,
            ),
            # 系统提示词泄露
            re.compile(
                r"(show|reveal|display|print|write)\s+(your|the|system)\s+(prompt|instructions?|rules?)",
                re.IGNORECASE,
            ),
            # 角色扮演攻击
            re.compile(
                r"(you\s+are|act\s+as|pretend\s+to\s+be|roleplay)\s+",
                re.IGNORECASE,
            ),
            # 输出控制
            re.compile(
                r"(output|print|say|respond)\s+(only|exactly):",
                re.IGNORECASE,
            ),
            # 绕过限制
            re.compile(
                r"(bypass|override|disable|deactivate)\s+(restrictions?|filters?|safety)",
                re.IGNORECASE,
            ),
            # JSON注入
            re.compile(
                r'"\s*:\s*"(?:system|admin|root)',
                re.IGNORECASE,
            ),
            # 分隔符注入
            re.compile(
                r"###\s*(?:instruction|system|admin)",
                re.IGNORECASE,
            ),
            # 编码绕过
            re.compile(
                r"(?:base64|hex|url|unicode)\s*(?:encode|decode)",
                re.IGNORECASE,
            ),
            # DAN模式
            re.compile(
                r"(?:DAN|do\s+anything\s+now)",
                re.IGNORECASE,
            ),
        ]
        return patterns

    def _load_sensitive_words(self) -> Set[str]:
        """
        加载敏感词列表.

        Returns:
            Set: 敏感词集合
        """
        # 基础敏感词（实际项目中应从配置或数据库加载）
        words = {
            # 政治敏感词（示例，实际应更全面）
            "政治敏感词",
            # 色情词汇
            "色情",
            "裸体",
            # 暴力词汇
            "暴力",
            "杀人",
            # 其他
        }
        return words

    def _load_pii_patterns(self) -> Dict[str, re.Pattern]:
        """
        加载PII（个人身份信息）检测模式.

        Returns:
            Dict: PII模式映射
        """
        return {
            "phone": re.compile(
                r"(?:手机|电话|手机号)?[:：]?\s*1[3-9]\d{9}",
            ),
            "id_card": re.compile(
                r"(?:身份证|证件号)?[:：]?\s*\d{17}[\dXx]",
            ),
            "bank_card": re.compile(
                r"(?:银行卡|卡号)?[:：]?\s*\d{16,19}",
            ),
            "email": re.compile(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            ),
            "password": re.compile(
                r"(?:密码|password)[:：]\s*\S+",
                re.IGNORECASE,
            ),
        }

    async def check_prompt_injection(
        self,
        prompt: str,
    ) -> PromptInjectionCheckResult:
        """
        检测提示词注入.

        Args:
            prompt: 用户输入的Prompt

        Returns:
            PromptInjectionCheckResult: 检测结果
        """
        detected_patterns: List[str] = []
        risk_level = "low"

        # 检查注入模式
        for pattern in self._injection_patterns:
            if pattern.search(prompt):
                detected_patterns.append(pattern.pattern)

        if detected_patterns:
            # 根据检测到的模式数量评估风险
            if len(detected_patterns) >= 3:
                risk_level = "critical"
            elif len(detected_patterns) >= 2:
                risk_level = "high"
            else:
                risk_level = "medium"

            logger.warning(
                "Potential prompt injection detected",
                risk_level=risk_level,
                patterns=detected_patterns,
                prompt_preview=prompt[:100],
            )

        return PromptInjectionCheckResult(
            is_malicious=len(detected_patterns) > 0,
            risk_level=risk_level,
            detected_patterns=detected_patterns,
            explanation=self._generate_injection_explanation(
                detected_patterns,
            ),
        )

    def _generate_injection_explanation(
        self,
        patterns: List[str],
    ) -> str:
        """
        生成注入检测解释.

        Args:
            patterns: 检测到的模式

        Returns:
            str: 解释说明
        """
        if not patterns:
            return ""

        explanations = []

        if any("ignore" in p.lower() for p in patterns):
            explanations.append("检测到尝试忽略系统指令的行为")

        if any("prompt" in p.lower() or "instruction" in p.lower() for p in patterns):
            explanations.append("检测到尝试获取系统提示词的行为")

        if any("bypass" in p.lower() or "override" in p.lower() for p in patterns):
            explanations.append("检测到尝试绕过安全限制的行为")

        if any("roleplay" in p.lower() or "act as" in p.lower() for p in patterns):
            explanations.append("检测到角色扮演攻击尝试")

        return "; ".join(explanations) if explanations else "检测到可疑的输入模式"

    async def sanitize_prompt(
        self,
        prompt: str,
    ) -> str:
        """
        净化Prompt.

        移除或替换潜在的恶意内容。

        Args:
            prompt: 原始Prompt

        Returns:
            str: 净化后的Prompt
        """
        sanitized = prompt

        # 移除注入模式
        for pattern in self._injection_patterns:
            sanitized = pattern.sub("[已过滤]", sanitized)

        # 脱敏PII
        for pii_type, pii_pattern in self._pii_patterns.items():
            sanitized = pii_pattern.sub(f"[{pii_type}已脱敏]", sanitized)

        return sanitized

    async def check_content_compliance(
        self,
        content: str,
    ) -> ContentComplianceResult:
        """
        检查内容合规性.

        Args:
            content: 待检查的内容

        Returns:
            ContentComplianceResult: 合规检查结果
        """
        violations: List[str] = []
        categories: List[str] = []

        # 检查敏感词
        content_lower = content.lower()
        for word in self._sensitive_words:
            if word.lower() in content_lower:
                violations.append(f"包含敏感词: {word}")

        # 暴力内容检测（简化版）
        violence_keywords = ["杀人", "暴力", "伤害"]
        if any(kw in content for kw in violence_keywords):
            violations.append("可能包含暴力内容")
            categories.append("violence")

        # 仇恨言论检测（简化版）
        hate_keywords = ["仇恨", "歧视"]
        if any(kw in content for kw in hate_keywords):
            violations.append("可能包含仇恨言论")
            categories.append("hate_speech")

        is_compliant = len(violations) == 0

        if not is_compliant:
            logger.warning(
                "Content compliance violation detected",
                violations=violations,
                categories=categories,
            )

        return ContentComplianceResult(
            is_compliant=is_compliant,
            violations=violations,
            categories=categories,
            confidence=0.85,  # 简化版置信度
            original_content=content[:200],
        )

    async def check_output_safety(
        self,
        output: str,
    ) -> SafetyCheckResult:
        """
        检查输出安全性.

        Args:
            output: LLM输出内容

        Returns:
            SafetyCheckResult: 安全检查结果
        """
        # 合规检查
        compliance_result = await self.check_content_compliance(output)

        # PII检测
        pii_found = []
        for pii_type, pii_pattern in self._pii_patterns.items():
            if pii_pattern.search(output):
                pii_found.append(pii_type)

        # 敏感词检查
        sensitive_found = []
        output_lower = output.lower()
        for word in self._sensitive_words:
            if word.lower() in output_lower:
                sensitive_found.append(word)

        # 综合判断
        is_safe = compliance_result.is_compliant and not pii_found and not sensitive_found

        violations = compliance_result.violations.copy()
        if pii_found:
            violations.append(f"包含PII: {', '.join(pii_found)}")
        if sensitive_found:
            violations.append(f"包含敏感词: {', '.join(sensitive_found[:3])}")

        # 计算风险等级
        if violations:
            risk_level = "high" if len(violations) > 2 else "medium"
        else:
            risk_level = "low"

        # 生成净化版本
        sanitized = None
        if not is_safe:
            sanitized = await self.sanitize_prompt(output)

        return SafetyCheckResult(
            is_safe=is_safe,
            is_malicious=False,  # 输出检测不标记为恶意
            risk_level=risk_level,
            violations=violations,
            explanation=self._generate_safety_explanation(violations),
            original_content=output[:200],
            sanitized_content=sanitized,
        )

    def _generate_safety_explanation(
        self,
        violations: List[str],
    ) -> str:
        """
        生成安全检查解释.

        Args:
            violations: 违规项列表

        Returns:
            str: 解释说明
        """
        if not violations:
            return "内容安全"

        return f"检测到以下问题: {'; '.join(violations)}"

    async def mask_pii(
        self,
        text: str,
        mask_char: str = "*",
    ) -> str:
        """
        脱敏PII信息.

        Args:
            text: 原始文本
            mask_char: 掩码字符

        Returns:
            str: 脱敏后的文本
        """
        masked = text

        for pii_type, pattern in self._pii_patterns.items():
            def mask_match(match: re.Match) -> str:
                matched = match.group(0)
                if len(matched) <= 4:
                    return mask_char * len(matched)
                return matched[:2] + mask_char * (len(matched) - 4) + matched[-2:]

            masked = pattern.sub(mask_match, masked)

        return masked

    async def validate_prompt_length(
        self,
        prompt: str,
        max_length: int = 8000,
    ) -> bool:
        """
        验证Prompt长度.

        Args:
            prompt: Prompt内容
            max_length: 最大长度

        Returns:
            bool: 是否有效
        """
        return len(prompt) <= max_length

    async def check_rate_limit(
        self,
        user_id: str,
        max_requests: int = 100,
        window_seconds: int = 3600,
    ) -> bool:
        """
        检查用户请求频率限制.

        Args:
            user_id: 用户ID
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            bool: 是否在限制内
        """
        # TODO: 实现基于Redis的频率限制
        return True

    def add_sensitive_word(
        self,
        word: str,
    ) -> None:
        """
        添加敏感词.

        Args:
            word: 敏感词
        """
        self._sensitive_words.add(word)

    def remove_sensitive_word(
        self,
        word: str,
    ) -> None:
        """
        移除敏感词.

        Args:
            word: 敏感词
        """
        self._sensitive_words.discard(word)


class PromptInjectionGuard(SafetyGuard):
    """
    提示词注入防护专用类.
    """

    async def guard(
        self,
        prompt: str,
        raise_on_violation: bool = True,
    ) -> PromptInjectionCheckResult:
        """
        执行注入防护.

        Args:
            prompt: 用户输入
            raise_on_violation: 发现违规时是否抛出异常

        Returns:
            PromptInjectionCheckResult: 检测结果

        Raises:
            SafetyViolationError: 发现注入攻击
        """
        result = await self.check_prompt_injection(prompt)

        if result.is_malicious:
            logger.warning(
                "Prompt injection blocked",
                risk_level=result.risk_level,
                patterns=result.detected_patterns,
            )

            if raise_on_violation:
                raise SafetyViolationError(
                    error_code=ErrorCode.SAFETY_VIOLATION,
                    message="检测到潜在的恶意输入，请求已被阻止",
                    violation_type="prompt_injection",
                )

        return result


# 全局安全防护实例
_safety_guard: Optional[SafetyGuard] = None
_prompt_injection_guard: Optional[PromptInjectionGuard] = None


def get_safety_guard() -> SafetyGuard:
    """获取安全防护实例."""
    global _safety_guard
    if _safety_guard is None:
        _safety_guard = SafetyGuard()
    return _safety_guard


def get_prompt_injection_guard() -> PromptInjectionGuard:
    """获取提示词注入防护实例."""
    global _prompt_injection_guard
    if _prompt_injection_guard is None:
        _prompt_injection_guard = PromptInjectionGuard()
    return _prompt_injection_guard