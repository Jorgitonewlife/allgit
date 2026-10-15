from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# ============================================================
# ESQUEMAS (SCHEMAS) - Definição de contratos da API
# Pydantic v2: validação, serialização, documentação OpenAPI
# ============================================================


class UserBase(BaseModel):
    """Campos base do usuário - compartilhado entre create/read"""
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")  # Validação regex simples de email


class UserCreate(UserBase):
    """Payload para criar usuário (POST /auth/register)"""
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt limita a 72 chars


class UserRead(UserBase):
    """Resposta ao ler usuário (GET /auth/me) - inclui campos do banco"""
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Permite ler direto de ORM (SQLAlchemy)


class Token(BaseModel):
    """Resposta do login - JWT access token"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Dados decodificados do JWT (usado internamente no auth)"""
    user_id: UUID | None = None


class URLBase(BaseModel):
    """Campos base da URL - compartilhado entre create/read"""
    original_url: HttpUrl = Field(..., max_length=2048)  # Valida URL real + limite tamanho
    expires_at: datetime | None = None  # Opcional: expiração da URL curta
    description: str | None = Field(None, max_length=500)  # Opcional: descrição livre


class URLCreate(URLBase):
    """Payload para criar URL curta (POST /urls) - herda de URLBase"""
    pass  # Nada a mais por enquanto


class URLRead(URLBase):
    """Resposta ao ler URL (GET /urls/{code}) - inclui campos do banco"""
    id: UUID
    short_code: str
    clicks: int
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Lê direto do modelo SQLAlchemy


class URLShortenResponse(BaseModel):
    """Resposta ao criar URL (POST /urls) - foco no que o cliente precisa"""
    short_url: str  # URL completa pronta para uso (ex: http://localhost:8000/abc123)
    short_code: str  # Apenas o código (ex: abc123)
    original_url: HttpUrl
    clicks: int
    created_at: datetime
    description: str | None = None


class HealthResponse(BaseModel):
    """Health check (GET /health) - para monitoramento/load balancer"""
    status: str
    version: str
    environment: str