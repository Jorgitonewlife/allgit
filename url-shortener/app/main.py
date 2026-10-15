from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth, urls

settings = get_settings()


# ============================================================
# APP FACTORY - Ponto de entrada da aplicação FastAPI
# Configuração central: lifespan, middleware, routers, health
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação (startup/shutdown).
    - Startup: cria tabelas no banco (init_db)
    - Shutdown: cleanup (conexões, etc) - aqui vazio
    Substitui @app.on_event("startup") deprecated.
    """
    await init_db()  # Cria tabelas se não existirem (dev only; prod usa Alembic)
    yield
    # cleanup aqui se necessário (ex: fechar pools Redis)


app = FastAPI(
    title="URL Shortener API",
    description="A simple URL shortener service built with FastAPI",
    version="0.1.0",
    lifespan=lifespan,  # Hook de lifecycle
    # Desabilita docs em produção (segurança)
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# CORS: permite frontend local chamar API
# Em produção: restrinja allow_origins para domínio real
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routers (modularização por domínio)
app.include_router(auth.router)   # /auth/*
app.include_router(urls.router)   # /urls/*


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check para load balancer / Kubernetes / monitoramento.
    Retorna status + versão + ambiente.
    Não toca banco (rápido). Para readiness, adicionaria check de DB.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/", tags=["root"])
async def root():
    """Endpoint raiz - aponta para docs"""
    return {"message": "URL Shortener API", "docs": "/docs"}