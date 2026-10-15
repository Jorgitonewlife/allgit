from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_token
from app.database import get_db
from app.models import User

# Esquema OAuth2: define onde pegar token (header Authorization: Bearer <token>)
# tokenUrl: endpoint que gera token (usado no Swagger para "Authorize")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],      # Extrai token do header
    db: Annotated[AsyncSession, Depends(get_db)],       # Injeta sessão DB
) -> User:
    """
    Dependency: valida JWT e retorna usuário do banco.
    - Decodifica token (assinatura + expiração)
    - Busca usuário por ID no banco
    - Levanta 401 se qualquer etapa falhar
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    # Busca usuário no banco (garante que não foi deletado)
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency: garante que usuário está ativo (is_active=True).
    Usa get_current_user internamente (cadeia de dependencies).
    Levanta 400 se usuário desativado.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_INACTIVE, detail="Inactive user")
    return user


# Type aliases para uso nos routers (limpos e reutilizáveis)
# CurrentUser: exige usuário autenticado E ativo
# CurrentUserOptional: permite None (útil em endpoints públicos que personalizam se logado)
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user)]