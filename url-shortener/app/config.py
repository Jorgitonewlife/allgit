from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# CONFIG - Centraliza todas as variáveis de ambiente
# Pydantic Settings: validação automática + type hints + .env file
# ============================================================


class Settings(BaseSettings):
    """
    Configuração da aplicação.
    Valores vêm de (ordem de prioridade):
    1. Variáveis de ambiente (OS)
    2. Arquivo .env (local dev)
    3. Defaults definidos abaixo
    """
    # Lê .env na raiz do projeto (utf-8), ignora vars extras não definidas
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Banco: asyncpg driver nativo async para PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/url_shortener"

    # Redis: para cache, rate limiting, sessions (futuro)
    redis_url: str = "redis://localhost:6379/0"

    # JWT: CHAVE SECRETA - OBRIGATÓRIO MUDAR EM PRODUÇÃO!
    # Use: openssl rand -hex 32  (gera 64 chars hex)
    secret_key: str = "change-me-in-production"

    # Algoritmo JWT (HS256 = simétrico, RS256 = assimétrico p/ produção)
    algorithm: str = "HS256"

    # Expiração do access token (minutos)
    access_token_expire_minutes: int = 30

    # Ambiente: development | production | testing
    # Controla: echo SQL, CORS, docs habilitadas, etc
    environment: str = "development"


# ============================================================
# SINGLETON: get_settings() cached
# @lru_cache: instancia Settings uma vez só (performance)
# FastAPI Depends(get_settings) reusa mesma instância
# ============================================================
@lru_cache
def get_settings() -> Settings:
    return Settings()