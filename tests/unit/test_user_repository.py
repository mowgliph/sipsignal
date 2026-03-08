"""Tests para el protocolo UserRepository."""

from abc import ABC

import pytest

from bot.domain.ports.repositories import UserRepository


class TestUserRepositoryProtocol:
    def test_is_abstract(self):
        """Verifica que UserRepository sea una clase abstracta."""
        assert issubclass(UserRepository, ABC)

    def test_cannot_instantiate(self):
        """Verifica que no se pueda instanciar UserRepository directamente."""
        with pytest.raises(TypeError):
            UserRepository()


class ConcreteUserRepository(UserRepository):
    """Implementación concreta para tests."""

    async def get(self, user_id: int) -> dict | None:
        return {"user_id": user_id, "status": "approved"}

    async def save(self, user: dict) -> None:
        pass

    async def get_all(self) -> list[dict]:
        return []

    async def get_by_status(self, status: str) -> list[dict]:
        return []

    async def update_last_seen(self, user_id: int) -> None:
        pass

    async def get_user_status(self, user_id: int) -> str | None:
        return "approved"

    async def request_access(self, user_id: int) -> bool:
        return True

    async def approve_user(self, user_id: int) -> bool:
        return True

    async def deny_user(self, user_id: int) -> bool:
        return True

    async def make_admin(self, user_id: int) -> bool:
        return True


class TestConcreteUserRepository:
    """Tests para la implementación concreta de UserRepository."""

    @pytest.mark.asyncio
    async def test_get(self):
        """Test del método get."""
        repo = ConcreteUserRepository()
        result = await repo.get(123)
        assert result is not None
        assert result["user_id"] == 123
        assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test del método get cuando no existe el usuario."""
        repo = ConcreteUserRepository()

        # Override para retornar None
        original_get = repo.get

        async def mock_get(user_id: int) -> dict | None:
            return None

        repo.get = mock_get
        result = await repo.get(999)
        assert result is None

        # Restaurar
        repo.get = original_get

    @pytest.mark.asyncio
    async def test_save(self):
        """Test del método save."""
        repo = ConcreteUserRepository()
        user = {"user_id": 123, "status": "pending"}
        await repo.save(user)
        # No retorna nada, solo verificamos que no lance excepción

    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test del método get_all."""
        repo = ConcreteUserRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_by_status(self):
        """Test del método get_by_status."""
        repo = ConcreteUserRepository()
        result = await repo.get_by_status("approved")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_update_last_seen(self):
        """Test del método update_last_seen."""
        repo = ConcreteUserRepository()
        await repo.update_last_seen(123)
        # No retorna nada, solo verificamos que no lance excepción

    @pytest.mark.asyncio
    async def test_get_user_status(self):
        """Test del método get_user_status."""
        repo = ConcreteUserRepository()
        result = await repo.get_user_status(123)
        assert result == "approved"

    @pytest.mark.asyncio
    async def test_request_access(self):
        """Test del método request_access."""
        repo = ConcreteUserRepository()
        result = await repo.request_access(123)
        assert result is True

    @pytest.mark.asyncio
    async def test_approve_user(self):
        """Test del método approve_user."""
        repo = ConcreteUserRepository()
        result = await repo.approve_user(123)
        assert result is True

    @pytest.mark.asyncio
    async def test_deny_user(self):
        """Test del método deny_user."""
        repo = ConcreteUserRepository()
        result = await repo.deny_user(123)
        assert result is True

    @pytest.mark.asyncio
    async def test_make_admin(self):
        """Test del método make_admin."""
        repo = ConcreteUserRepository()
        result = await repo.make_admin(123)
        assert result is True
