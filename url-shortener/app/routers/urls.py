from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas import URLCreate, URLRead, URLShortenResponse
from app.services.url_service import URLService

router = APIRouter(prefix="/urls", tags=["urls"])
settings = get_settings()


# ============================================================
# ROTAS DE URLs - Endpoints REST
# Camada fina: valida input (schemas), chama service, retorna response
# ============================================================


@router.post("", response_model=URLShortenResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    url_data: URLCreate,              # Validação automática via Pydantic (body)
    current_user: CurrentUser,        # Dependency: usuário autenticado (JWT válido)
    request: Request,                 # Para construir URL base (http://host:port)
    db: AsyncSession = Depends(get_db),  # Dependency: sessão de banco
):
    """
    Cria URL curta.
    - Requer autenticação (Bearer token)
    - Body: { original_url, expires_at?, description? }
    - Retorna: { short_url, short_code, original_url, clicks, created_at, description }
    """
    service = URLService(db)
    url = await service.create_short_url(
        original_url=str(url_data.original_url),  # HttpUrl -> str
        owner_id=current_user.id,
        expires_at=url_data.expires_at,
        description=url_data.description,
    )
    # Monta URL completa: http://localhost:8000/abc123
    base_url = str(request.base_url).rstrip("/")
    return URLShortenResponse(
        short_url=f"{base_url}/{url.short_code}",
        short_code=url.short_code,
        original_url=url.original_url,
        clicks=url.clicks,
        created_at=url.created_at,
        description=url.description,
    )


@router.get("", response_model=list[URLRead])
async def list_user_urls(
    current_user: CurrentUser,
    skip: int = 0,      # Query param: paginação offset
    limit: int = 100,   # Query param: paginação limit (max 100)
    db: AsyncSession = Depends(get_db),
):
    """
    Lista URLs do usuário autenticado.
    - Paginação via query params: ?skip=0&limit=20
    - Ordena por data de criação (mais recente primeiro)
    """
    service = URLService(db)
    return await service.get_user_urls(current_user.id, skip, limit)


@router.get("/{short_code}", response_model=URLRead)
async def get_url_info(
    short_code: str,                  # Path parameter
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Detalhes de uma URL específica.
    - Verifica ownership (só dono vê)
    - 404 se não existe ou não é do usuário
    """
    service = URLService(db)
    url = await service.get_by_code(short_code)
    if not url or url.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    return url


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    url_id: str,                      # Path param (string, converte para UUID)
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Deleta URL do usuário.
    - Converte url_id string -> UUID
    - Service garante ownership
    - 204 No Content se sucesso, 404 se não encontrou
    """
    from uuid import UUID
    service = URLService(db)
    deleted = await service.delete_url(UUID(url_id), current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")


@router.get("/{short_code}/redirect", include_in_schema=False)
async def redirect_to_original(
    short_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Redirect público (sem autenticação) - o coração do encurtador.
    - include_in_schema=False: não aparece no Swagger/OpenAPI
    - Busca por short_code
    - Verifica expiração (410 Gone se expirado)
    - Incrementa clicks atomicamente
    - Retorna 307 Temporary Redirect para URL original
    """
    service = URLService(db)
    url = await service.get_by_code(short_code)
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    if await service.is_expired(url):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="URL has expired")

    await service.increment_clicks(short_code)
    return RedirectResponse(url=str(url.original_url), status_code=status.HTTP_307_TEMPORARY_REDIRECT)