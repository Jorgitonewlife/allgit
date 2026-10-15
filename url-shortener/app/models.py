from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ============================================================
# MODELOS (MODELS) - Tabelas do banco de dados (SQLAlchemy 2.0)
# Mapped/mapped_column = tipagem nativa Python + mapeamento ORM
# ============================================================


class User(Base):
    """Tabela 'users' - usuários do sistema"""
    __tablename__ = "users"

    # PK: UUID gerado automaticamente (uuid4)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Email único + index para login rápido
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Senha hasheada com bcrypt (nunca salva senha pura)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Soft delete / desativação sem apagar dados
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps automáticos (banco preenche)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamento 1:N com URLs (lazy="selectin" evita N+1 queries)
    urls: Mapped[list["URL"]] = relationship(back_populates="owner", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class URL(Base):
    """Tabela 'urls' - URLs encurtadas"""
    __tablename__ = "urls"

    # PK: UUID
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Código curto único (ex: "abc123") - index para redirect rápido
    short_code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)

    # URL original (até 2048 chars)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Contador de cliques (incrementado no redirect)
    clicks: Mapped[int] = mapped_column(default=0)

    # FK para User - dono da URL
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Descrição opcional da URL
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps automáticos
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Expiração opcional (UTC)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relacionamento N:1 com User
    owner: Mapped["User"] = relationship(back_populates="urls", lazy="selectin")

    # Index composto para listar URLs do usuário ordenadas por data
    __table_args__ = (
        Index("ix_urls_owner_created", "owner_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<URL(short_code={self.short_code}, original_url={self.original_url})>"