
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from src.api.routes import router as api_router
from src.core.config import settings
from src.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    print(f"🚀 Starting Semantic Mapping System v{settings.VERSION}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    
    yield
    
    print("🛑 Shutting down Semantic Mapping System")


def create_app() -> FastAPI:

    app = FastAPI(
        title="Semantic Database Schema Mapping System",
        description="AI-powered system for mapping database schemas to semantic web technologies",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router, prefix="/api/v1")
    
    try:
        app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    except RuntimeError:
        pass
    
    return app


def main():
    app = create_app()
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
