"""
PM Digital Employee - Document Chunker
项目经理数字员工系统 - 文档切片模块

实现多种文档切片策略：固定大小、语义切片、段落切片、递归切片。
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.schemas import ChunkStrategy, DocumentChunk

logger = get_logger(__name__)


class BaseChunker(ABC):
    """
    文档切片基类.

    定义切片接口规范。
    """

    @abstractmethod
    def chunk(
        self,
        content: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        切片方法.

        Args:
            content: 文档内容
            chunk_size: 切片大小（字符数）
            chunk_overlap: 切片重叠
            metadata: 元数据

        Returns:
            List[DocumentChunk]: 切片列表
        """
        pass


class FixedSizeChunker(BaseChunker):
    """
    固定大小切片器.

    按固定字符数切片，支持重叠。
    """

    def chunk(
        self,
        content: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        固定大小切片.

        Args:
            content: 文档内容
            chunk_size: 切片大小
            chunk_overlap: 切片重叠
            metadata: 元数据

        Returns:
            List[DocumentChunk]: 切片列表
        """
        import uuid

        chunks = []
        metadata = metadata or {}

        # 计算步长
        step = chunk_size - chunk_overlap

        # 按固定大小切片
        start = 0
        index = 0

        while start < len(content):
            end = start + chunk_size
            chunk_content = content[start:end]

            # 清理切片内容
            chunk_content = chunk_content.strip()

            if chunk_content:
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                    content=chunk_content,
                    chunk_index=index,
                    metadata={
                        **metadata,
                        "start_char": start,
                        "end_char": min(end, len(content)),
                    },
                )
                chunks.append(chunk)
                index += 1

            start += step

        logger.debug(
            "Fixed size chunking completed",
            total_length=len(content),
            chunk_size=chunk_size,
            chunk_count=len(chunks),
        )

        return chunks


class ParagraphChunker(BaseChunker):
    """
    段落切片器.

    按段落分割文档。
    """

    # 段落分隔符模式
    PARAGRAPH_PATTERN = re.compile(r"\n\s*\n")

    def chunk(
        self,
        content: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        段落切片.

        Args:
            content: 文档内容
            chunk_size: 最大切片大小
            chunk_overlap: 重叠大小
            metadata: 元数据

        Returns:
            List[DocumentChunk]: 切片列表
        """
        import uuid

        chunks = []
        metadata = metadata or {}

        # 按段落分割
        paragraphs = self.PARAGRAPH_PATTERN.split(content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        index = 0
        current_chunk = ""

        for paragraph in paragraphs:
            # 如果单个段落超过最大大小，需要进一步分割
            if len(paragraph) > chunk_size:
                # 先保存当前积累的内容
                if current_chunk:
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                        content=current_chunk.strip(),
                        chunk_index=index,
                        metadata=metadata.copy(),
                    )
                    chunks.append(chunk)
                    index += 1
                    current_chunk = ""

                # 分割长段落
                sub_chunks = self._split_long_paragraph(
                    paragraph,
                    chunk_size,
                    chunk_overlap,
                )

                for sub_content in sub_chunks:
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                        content=sub_content,
                        chunk_index=index,
                        metadata=metadata.copy(),
                    )
                    chunks.append(chunk)
                    index += 1

            # 尝试合并到当前切片
            elif len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            else:
                # 保存当前切片
                if current_chunk:
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                        content=current_chunk.strip(),
                        chunk_index=index,
                        metadata=metadata.copy(),
                    )
                    chunks.append(chunk)
                    index += 1

                current_chunk = paragraph

        # 保存最后一个切片
        if current_chunk:
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                content=current_chunk.strip(),
                chunk_index=index,
                metadata=metadata.copy(),
            )
            chunks.append(chunk)

        logger.debug(
            "Paragraph chunking completed",
            paragraph_count=len(paragraphs),
            chunk_count=len(chunks),
        )

        return chunks

    def _split_long_paragraph(
        self,
        paragraph: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        """
        分割长段落.

        Args:
            paragraph: 段落内容
            chunk_size: 切片大小
            chunk_overlap: 重叠大小

        Returns:
            List[str]: 分割后的内容列表
        """
        result = []
        start = 0
        step = chunk_size - chunk_overlap

        while start < len(paragraph):
            end = start + chunk_size

            # 尝试在句子边界分割
            if end < len(paragraph):
                # 查找最近的句子结束符
                last_period = paragraph.rfind("。", start, end)
                last_exclaim = paragraph.rfind("！", start, end)
                last_question = paragraph.rfind("？", start, end)

                split_point = max(last_period, last_exclaim, last_question)

                if split_point > start + chunk_size // 2:
                    end = split_point + 1

            result.append(paragraph[start:end].strip())
            start += step

        return result


class SemanticChunker(BaseChunker):
    """
    语义切片器.

    基于句子边界和语义连贯性进行切片。
    """

    # 中文句子分隔符
    SENTENCE_PATTERN = re.compile(r"(?<=[。！？\n])\s*")

    def chunk(
        self,
        content: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        语义切片.

        Args:
            content: 文档内容
            chunk_size: 最大切片大小
            chunk_overlap: 重叠句子数
            metadata: 元数据

        Returns:
            List[DocumentChunk]: 切片列表
        """
        import uuid

        chunks = []
        metadata = metadata or {}

        # 按句子分割
        sentences = self.SENTENCE_PATTERN.split(content)
        sentences = [s.strip() for s in sentences if s.strip()]

        index = 0
        current_chunk_sentences: List[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # 检查是否需要创建新切片
            if current_length + sentence_length > chunk_size and current_chunk_sentences:
                # 保存当前切片
                chunk_content = "".join(current_chunk_sentences)
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                    content=chunk_content,
                    chunk_index=index,
                    metadata={
                        **metadata,
                        "sentence_count": len(current_chunk_sentences),
                    },
                )
                chunks.append(chunk)
                index += 1

                # 保留重叠句子
                overlap_sentences = current_chunk_sentences[-chunk_overlap:] if chunk_overlap > 0 else []
                current_chunk_sentences = overlap_sentences
                current_length = sum(len(s) for s in overlap_sentences)

            current_chunk_sentences.append(sentence)
            current_length += sentence_length

        # 保存最后一个切片
        if current_chunk_sentences:
            chunk_content = "".join(current_chunk_sentences)
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=uuid.UUID(metadata.get("document_id", str(uuid.uuid4()))),
                content=chunk_content,
                chunk_index=index,
                metadata={
                    **metadata,
                    "sentence_count": len(current_chunk_sentences),
                },
            )
            chunks.append(chunk)

        logger.debug(
            "Semantic chunking completed",
            sentence_count=len(sentences),
            chunk_count=len(chunks),
        )

        return chunks


class RecursiveChunker(BaseChunker):
    """
    递归切片器.

    按优先级依次尝试不同分隔符，递归分割。
    """

    # 分隔符优先级（从高到低）
    SEPARATORS = [
        "\n\n\n",  # 章节分隔
        "\n\n",  # 段落分隔
        "\n",  # 行分隔
        "。",  # 中文句号
        "！",  # 中文感叹号
        "？",  # 中文问号
        "；",  # 中文分号
        "，",  # 中文逗号
        " ",  # 空格
        "",  # 字符级
    ]

    def chunk(
        self,
        content: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        递归切片.

        Args:
            content: 文档内容
            chunk_size: 切片大小
            chunk_overlap: 切片重叠
            metadata: 元数据

        Returns:
            List[DocumentChunk]: 切片列表
        """
        import uuid

        metadata = metadata or {}
        document_id = uuid.UUID(metadata.get("document_id", str(uuid.uuid4())))

        # 递归分割
        raw_chunks = self._split_recursive(
            content,
            chunk_size,
            chunk_overlap,
            self.SEPARATORS,
        )

        # 转换为DocumentChunk对象
        chunks = []
        for i, chunk_content in enumerate(raw_chunks):
            if chunk_content.strip():
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    content=chunk_content.strip(),
                    chunk_index=i,
                    metadata=metadata.copy(),
                )
                chunks.append(chunk)

        logger.debug(
            "Recursive chunking completed",
            total_length=len(content),
            chunk_count=len(chunks),
        )

        return chunks

    def _split_recursive(
        self,
        content: str,
        chunk_size: int,
        chunk_overlap: int,
        separators: List[str],
    ) -> List[str]:
        """
        递归分割.

        Args:
            content: 内容
            chunk_size: 切片大小
            chunk_overlap: 重叠大小
            separators: 分隔符列表

        Returns:
            List[str]: 分割后的内容列表
        """
        if not content:
            return []

        # 如果内容已经够小，直接返回
        if len(content) <= chunk_size:
            return [content]

        # 尝试使用分隔符分割
        for i, separator in enumerate(separators):
            if separator and separator in content:
                # 按当前分隔符分割
                splits = content.split(separator)
                splits = [s + separator for s in splits[:-1]] + [splits[-1]]

                # 合并小的分割
                result = []
                current = ""

                for split in splits:
                    if len(current) + len(split) <= chunk_size:
                        current += split
                    else:
                        if current:
                            result.append(current)
                        current = split

                if current:
                    result.append(current)

                # 检查是否还有过大的分割
                final_result = []
                for r in result:
                    if len(r) > chunk_size:
                        # 递归使用下一级分隔符
                        sub_result = self._split_recursive(
                            r,
                            chunk_size,
                            chunk_overlap,
                            separators[i + 1:],
                        )
                        final_result.extend(sub_result)
                    else:
                        final_result.append(r)

                return final_result

        # 如果没有找到分隔符，按字符分割
        result = []
        for i in range(0, len(content), chunk_size - chunk_overlap):
            result.append(content[i:i + chunk_size])

        return result


class ChunkerFactory:
    """
    切片器工厂.

    根据策略创建对应的切片器。
    """

    _chunkers: Dict[ChunkStrategy, type] = {
        ChunkStrategy.FIXED_SIZE: FixedSizeChunker,
        ChunkStrategy.PARAGRAPH: ParagraphChunker,
        ChunkStrategy.SEMANTIC: SemanticChunker,
        ChunkStrategy.RECURSIVE: RecursiveChunker,
    }

    @classmethod
    def create(
        cls,
        strategy: ChunkStrategy,
    ) -> BaseChunker:
        """
        创建切片器.

        Args:
            strategy: 切片策略

        Returns:
            BaseChunker: 切片器实例
        """
        chunker_class = cls._chunkers.get(strategy)
        if chunker_class is None:
            raise ValueError(f"Unknown chunk strategy: {strategy}")
        return chunker_class()

    @classmethod
    def register(
        cls,
        strategy: ChunkStrategy,
        chunker_class: type,
    ) -> None:
        """
        注册切片器.

        Args:
            strategy: 切片策略
            chunker_class: 切片器类
        """
        cls._chunkers[strategy] = chunker_class


def chunk_document(
    content: str,
    strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[DocumentChunk]:
    """
    便捷函数：切分文档.

    Args:
        content: 文档内容
        strategy: 切片策略
        chunk_size: 切片大小
        chunk_overlap: 切片重叠
        metadata: 元数据

    Returns:
        List[DocumentChunk]: 切片列表
    """
    chunker = ChunkerFactory.create(strategy)
    return chunker.chunk(
        content=content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        metadata=metadata,
    )