from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ============================================================
# ENGINE - Conexão assíncrona com PostgreSQL (asyncpg driver)
# create_async_engine: pool de conexões thread-safe para async
# ============================================================
engine = create_async_engine(
    settings.database_url,                    # postgresql+asyncpg://user:pass@host:port/db
    echo=settings.environment == "development",  # Log SQL no console (dev only)
    pool_pre_ping=True,                       # Testa conexão antes de usar (evita "MySQL gone away")
    pool_size=10,                             # Conexões permanentes no pool
    max_overflow=20,                          # Conexões extras sob carga (total max = 30)
)

# ============================================================
# SESSION FACTORY - Cria sessões (transações) sob demanda
# expire_on_commit=False: objetos não expiram após commit (útil p/ retornar dados)
# autoflush=False: controle manual de flush (evita queries surpresa)
# ============================================================
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Base class para todos os models (SQLAlchemy 2.0 style)
class Base(DeclarativeBase):
    pass


# ============================================================
# DEPENDENCY: get_db() - Usado via Depends(get_db) nos routers
# - Cria sessão por request
# - Yield: entrega sessão ao router
# - Finally: garante close (mesmo se erro)
# ============================================================
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================
# INIT DB - Cria tabelas no startup (apenas dev)
# Em produção: use Alembic migrations (alembic upgrade head)
# ============================================================
async def init_db() -> None:
    async with engine.begin() as conn:
        # run_sync: executa código síncrono (metadata.create_all) no loop async
        await conn.run_sync(Base.metadata.create_all)