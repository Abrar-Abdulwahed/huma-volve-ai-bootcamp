from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config.config_parser import settings
from src.logging.logger import logger
from src.core.factories import ModelFactory
from src.vectorstore.database import VectorDatabaseRepository
from src.routers import ingest_router, query_router
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    ModelFactory.get_embeddings()
    ModelFactory.get_llm()
 
    yield 
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Telecom Customer Support RAG Microservice built with FastAPI, LangChain, FAISS, and Gemini.",
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)