"""
test RAG retriever for PM Digital Employee.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.schemas import RAGRequest, RAGResponse, RetrievedDocument
from app.rag.retriever import PermissionAwareRetriever
from app.rag.chunker import FixedSizeChunker, ParagraphChunker


class TestFixedSizeChunker:
    """Test FixedSizeChunker."""

    def test_chunk_text(self):
        """Test text chunking."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        text = "这是一段测试文本，用于测试文本分块功能。" * 10

        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(len(chunk.content) <= 100 for chunk in chunks)

    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk("")

        assert len(chunks) == 0


class TestParagraphChunker:
    """Test ParagraphChunker."""

    def test_chunk_by_paragraph(self):
        """Test paragraph-based chunking."""
        chunker = ParagraphChunker()
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"

        chunks = chunker.chunk(text)

        assert len(chunks) == 3


class TestPermissionAwareRetriever:
    """Test PermissionAwareRetriever."""

    @pytest.mark.asyncio
    async def test_retrieve_with_permissions(self):
        """Test retrieval with permission filtering."""
        retriever = PermissionAwareRetriever()

        # Mock database session
        with patch.object(retriever, "_search_vectors", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                RetrievedDocument(
                    id="doc1",
                    content="测试内容",
                    score=0.9,
                    metadata={"project_id": "test_project"},
                ),
                RetrievedDocument(
                    id="doc2",
                    content="其他内容",
                    score=0.8,
                    metadata={"project_id": "other_project"},
                ),
            ]

            request = RAGRequest(
                query="测试查询",
                user_id="test_user",
                project_id="test_project",
                top_k=5,
            )

            response = await retriever.retrieve(request)

            # Should only return documents from the same project
            assert len(response.documents) == 1
            assert response.documents[0].id == "doc1"

    @pytest.mark.asyncio
    async def test_retrieve_no_results(self):
        """Test retrieval with no results."""
        retriever = PermissionAwareRetriever()

        with patch.object(retriever, "_search_vectors", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            request = RAGRequest(
                query="无匹配查询",
                user_id="test_user",
                project_id="test_project",
                top_k=5,
            )

            response = await retriever.retrieve(request)

            assert len(response.documents) == 0
            assert response.has_answer is False


class TestRAGRequest:
    """Test RAGRequest."""

    def test_create_request(self):
        """Test request creation."""
        request = RAGRequest(
            query="测试问题",
            user_id="user1",
            project_id="project1",
            top_k=10,
        )

        assert request.query == "测试问题"
        assert request.top_k == 10

    def test_request_defaults(self):
        """Test request defaults."""
        request = RAGRequest(
            query="测试",
            user_id="user1",
            project_id="project1",
        )

        assert request.top_k == 5
        assert request.threshold == 0.5


class TestRetrievedDocument:
    """Test RetrievedDocument."""

    def test_document_creation(self):
        """Test document creation."""
        doc = RetrievedDocument(
            id="doc1",
            content="测试文档内容",
            score=0.85,
            metadata={"source": "policy", "page": 1},
        )

        assert doc.id == "doc1"
        assert doc.score == 0.85
        assert doc.metadata["source"] == "policy"