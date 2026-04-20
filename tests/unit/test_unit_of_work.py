"""
PM Digital Employee - Unit of Work Tests
Tests for UnitOfWork pattern implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestUnitOfWork:
    """Tests for UnitOfWork pattern."""

    @pytest.mark.asyncio
    async def test_unit_of_work_initialization(self, mock_session):
        """Should initialize UnitOfWork with session."""
        from app.core.unit_of_work import UnitOfWork

        uow = UnitOfWork(mock_session)
        assert uow.session == mock_session
        assert uow.is_active

    @pytest.mark.asyncio
    async def test_begin_transaction(self, mock_session):
        """Should begin transaction."""
        from app.core.unit_of_work import UnitOfWork

        uow = UnitOfWork(mock_session)
        await uow.begin()
        
        assert uow.is_active
        assert not uow._committed
        assert not uow._rolled_back

    @pytest.mark.asyncio
    async def test_commit_transaction(self, mock_session):
        """Should commit transaction."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.commit = AsyncMock()

        uow = UnitOfWork(mock_session)
        await uow.commit()

        assert uow._committed
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_transaction(self, mock_session):
        """Should rollback transaction."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.rollback = AsyncMock()

        uow = UnitOfWork(mock_session)
        await uow.rollback()

        assert uow._rolled_back
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_double_commit_warning(self, mock_session):
        """Should warn on double commit."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.commit = AsyncMock()

        uow = UnitOfWork(mock_session)
        await uow.commit()
        await uow.commit()  # Second commit should be safe

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cannot_commit_after_rollback(self, mock_session):
        """Should raise error when committing after rollback."""
        from app.core.unit_of_work import UnitOfWork
        from app.core.exceptions import DatabaseError

        mock_session.rollback = AsyncMock()

        uow = UnitOfWork(mock_session)
        await uow.rollback()

        with pytest.raises(DatabaseError):
            await uow.commit()

    @pytest.mark.asyncio
    async def test_cannot_rollback_after_commit(self, mock_session):
        """Should raise error when rolling back after commit."""
        from app.core.unit_of_work import UnitOfWork
        from app.core.exceptions import DatabaseError

        mock_session.commit = AsyncMock()

        uow = UnitOfWork(mock_session)
        await uow.commit()

        with pytest.raises(DatabaseError):
            await uow.rollback()

    @pytest.mark.asyncio
    async def test_flush_operation(self, mock_session):
        """Should flush changes without commit."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.flush = AsyncMock()

        uow = UnitOfWork(mock_session)
        await uow.flush()

        mock_session.flush.assert_called_once()
        assert uow.is_active

    @pytest.mark.asyncio
    async def test_transaction_context_manager_success(self, mock_session):
        """Should auto-commit on successful exit."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.commit = AsyncMock()

        uow = UnitOfWork(mock_session)
        
        async with uow.transaction():
            # Do some work
            pass

        assert uow._committed
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_context_manager_failure(self, mock_session):
        """Should auto-rollback on exception."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.rollback = AsyncMock()

        uow = UnitOfWork(mock_session)
        
        with pytest.raises(ValueError):
            async with uow.transaction():
                raise ValueError("Test error")

        assert uow._rolled_back
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_active_property(self, mock_session):
        """Should correctly report is_active status."""
        from app.core.unit_of_work import UnitOfWork

        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        uow = UnitOfWork(mock_session)
        assert uow.is_active  # Initially active

        await uow.commit()
        assert not uow.is_active  # Not active after commit

        uow2 = UnitOfWork(mock_session)
        await uow2.rollback()
        assert not uow2.is_active  # Not active after rollback


class TestUnitOfWorkManager:
    """Tests for UnitOfWorkManager."""

    @pytest.mark.asyncio
    async def test_manager_create(self):
        """Should create UnitOfWork from factory."""
        from app.core.unit_of_work import UnitOfWorkManager

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        factory = lambda: mock_session
        manager = UnitOfWorkManager(factory)

        async with manager.create() as uow:
            assert uow.session == mock_session
            assert uow.is_active

        # Should auto-commit on exit
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_rollback_on_error(self):
        """Should rollback on exception."""
        from app.core.unit_of_work import UnitOfWorkManager

        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        factory = lambda: mock_session
        manager = UnitOfWorkManager(factory)

        with pytest.raises(ValueError):
            async with manager.create() as uow:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestCreateUnitOfWork:
    """Tests for create_unit_of_work helper."""

    def test_create_unit_of_work(self, mock_session):
        """Should create UnitOfWork instance."""
        from app.core.unit_of_work import create_unit_of_work

        uow = create_unit_of_work(mock_session)
        assert uow.session == mock_session
        assert uow.is_active