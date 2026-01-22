"""FastAPI application for FinanceAI."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # Load .env file before any other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routers import analysis, chat, knowledge_base, research, search, stock, system, youtube
from src.core.config import get_project_root


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("FinanceAI API starting...")
    yield
    # Shutdown
    print("FinanceAI API shutting down...")


app = FastAPI(
    title="FinanceAI API",
    description="AI-Powered Stock Analysis Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stock.router, prefix="/api/v1/stock", tags=["Stock"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(research.router, prefix="/api/v1/research", tags=["Research"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(knowledge_base.router, prefix="/api/v1/knowledge", tags=["Knowledge Base"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["YouTube"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])

# Static files for outputs
data_dir = get_project_root() / "data" / "user"
if data_dir.exists():
    app.mount("/api/outputs", StaticFiles(directory=str(data_dir)), name="outputs")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FinanceAI API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
