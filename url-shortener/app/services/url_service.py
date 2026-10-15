import secrets
import string
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import URL


# ============================================================
# SERVIÇO (SERVICE) - Lógica de negócio isolada dos routers
# Recebe AsyncSession (banco), retorna models (não schemas)
# ============================================================


class URLService:
    """Encapsula toda lógica de URLs: criação, busca, contadores, expiração"""

    def __init__(self, db: AsyncSession):
        """Injeção de dependência: recebe sessão de banco assíncrona"""
        self.db = db

    @staticmethod
    def generate_short_code(length: int = 6) -> str:
        """
        Gera código aleatório alfanumérico (a-z, A-Z, 0-9).
        6 chars = 62^6 ≈ 56 bilhões de combinações.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_short_url(
        self,
        original_url: str,
        owner_id: UUID,
        expires_at: datetime | None = None,
        custom_code: str | None = None,
        description: str | None = None,
    ) -> URL:
        """
        Cria nova URL curta.
        - Se custom_code fornecido: valida unicidade
        - Senão: gera código único aleatório (tenta até 10x)
        - Salva no banco e retorna o model completo
        """
        if custom_code:
            existing = await self.get_by_code(custom_code)
            if existing:
                raise ValueError("Short code already in use")
            short_code = custom_code
        else:
            short_code = await self._generate_unique_code()

        url = URL(
            short_code=short_code,
            original_url=original_url,
            owner_id=owner_id,
            expires_at=expires_at,
            description=description,
        )
        self.db.add(url)
        await self.db.commit()
        await self.db.refresh(url)  # Recarrega com IDs/timestamps do banco
        return url

    async def _generate_unique_code(self, max_attempts: int = 10) -> str:
        """
        Gera código único tentanto até max_attempts vezes.
        Colisão é rara (56 bi combos), mas possível em alta concorrência.
        """
        for _ in range(max_attempts):
            code = self.generate_short_code()
            existing = await self.get_by_code(code)
            if not existing:
                return code
        raise RuntimeError("Could not generate unique short code")

    async def get_by_code(self, short_code: str) -> URL | None:
        """Busca URL pelo código curto (usado no redirect público)"""
        result = await self.db.execute(select(URL).where(URL.short_code == short_code))
        return result.scalar_one_or_none()

    async def get_by_id(self, url_id: UUID, owner_id: UUID) -> URL | None:
        """Busca URL por ID + dono (garante que usuário só veja suas URLs)"""
        result = await self.db.execute(
            select(URL).where(URL.id == url_id, URL.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_user_urls(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> list[URL]:
        """
        Lista URLs do usuário com paginação.
        Ordena por created_at desc (mais recentes primeiro).
        Usa index composto ix_urls_owner_created.
        """
        result = await self.db.execute(
            select(URL)
            .where(URL.owner_id == owner_id)
            .order_by(URL.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def increment_clicks(self, short_code: str) -> URL | None:
        """
        Incrementa contador de cliques atomicamente (UPDATE ... RETURNING).
        Evita race condition: single query no banco.
        """
        result = await self.db.execute(
            update(URL)
            .where(URL.short_code == short_code)
            .values(clicks=URL.clicks + 1)
            .returning(URL)
        )
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete_url(self, url_id: UUID, owner_id: UUID) -> bool:
        """Deleta URL se pertencer ao usuário. Retorna True se deletou."""
        url = await self.get_by_id(url_id, owner_id)
        if not url:
            return False
        await self.db.delete(url)
        await self.db.commit()
        return True

    async def is_expired(self, url: URL) -> bool:
        """Verifica se URL expirou (compara UTC now com expires_at)"""
        if url.expires_at is None:
            return False
        return datetime.now(timezone.utc) > url.expires_at