from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_password_hash, verify_password
from app.database import get_db
from app.dependencies import CurrentUser
from app.models import User
from app.schemas import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# ROTAS DE AUTENTICAÇÃO - Register, Login, Me
# Stateless JWT: servidor não guarda sessão, token carrega user_id
# ============================================================


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra novo usuário.
    - Valida email único (400 se já existe)
    - Hash da senha com bcrypt (nunca salva senha pura)
    - Retorna usuário criado (sem senha, claro)
    """
    # Verifica se email já cadastrado
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Cria usuário com senha hasheada
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # Preenche id, created_at, etc do banco
    return user  # Serializa via UserRead (from_attributes=True)


@router.post("/login", response_model=Token)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Login: valida credenciais e retorna JWT.
    - Busca usuário por email
    - Verifica senha com bcrypt (verify_password)
    - Gera JWT com user_id no claim "sub"
    - Retorna { access_token, token_type: "bearer" }
    """
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    # Mesmo erro para "não existe" e "senha errada" (evita enumeração de usuários)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},  # Padrão OAuth2
        )

    # Token expira em ACCESS_TOKEN_EXPIRE_MINUTES (default 30min)
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser):
    """
    Retorna usuário autenticado (baseado no JWT).
    - CurrentUser = dependency que valida token + busca usuário no banco
    - 401 se token inválido/expirado
    - 403 se usuário inativo
    """
    return current_user