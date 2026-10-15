from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import TokenData

settings = get_settings()

# Configuração de hash: bcrypt (padrão seguro, lento = resistente a brute force)
# deprecated="auto": avisa se hash fraco for detectado
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica senha pura contra hash bcrypt.
    Usa constant-time comparison (evita timing attacks).
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash bcrypt da senha.
    Cost factor padrão (12 rounds) = ~250ms por hash em CPU moderna.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Cria JWT (JSON Web Token) assinado com HS256.
    - data: payload (ex: {"sub": "user-uuid"})
    - expires_delta: expiração customizada ou default (30min)
    - Retorna token string (ex: "eyJhbGciOiJIUzI1NiIs...")
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})  # Claim padrão "exp" (expiration timestamp)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenData | None:
    """
    Decodifica e valida JWT.
    - Verifica assinatura (secret_key)
    - Verifica expiração (claim "exp")
    - Extrai user_id do claim "sub" (subject)
    - Retorna TokenData ou None se inválido/expirado
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=UUID(user_id))
    except (JWTError, ValidationError):
        # Qualquer erro (assinatura, expiração, formato) -> None
        return None