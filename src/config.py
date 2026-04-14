"""Configuration management for Dead Regulations Detector."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TEST_DATA_DIR = DATA_DIR / "test"
FILES_DATA_DIR = DATA_DIR / "files"
HISTORY_DATA_DIR = DATA_DIR / "history"
REPORTS_DATA_DIR = DATA_DIR / "reports"
LOGS_DATA_DIR = DATA_DIR / "logs"
BACKEND_DB_PATH = DATA_DIR / "backend.db"

# Create directories if they don't exist
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    TEST_DATA_DIR,
    FILES_DATA_DIR,
    HISTORY_DATA_DIR,
    REPORTS_DATA_DIR,
    LOGS_DATA_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "github")  # github, openai, openrouter or claude

# GitHub Models (FREE!)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "gpt-4o-mini")

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# OpenRouter (free-tier friendly, OpenAI-compatible)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "moonshotai/kimi-k2:free")

# Claude API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4.5")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/regulations.db")

# Application
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Scraper
ADILET_BASE_URL = os.getenv("ADILET_BASE_URL", "https://adilet.zan.kz")
MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS", "100"))
SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", "1"))

# Vector DB
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chromadb")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
VECTOR_DB_PATH = DATA_DIR / "chroma_db"

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Streamlit
STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))

# Validation
if AI_PROVIDER == "github":
    if not GITHUB_TOKEN:
        print("ℹ️  GitHub Models not configured. Add GITHUB_TOKEN to .env")
elif AI_PROVIDER == "openai":
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-key-here":
        print("ℹ️  OpenAI API not configured. Add OPENAI_API_KEY to .env")
elif AI_PROVIDER == "openrouter":
    if not OPENROUTER_API_KEY:
        print("ℹ️  OpenRouter not configured. Add OPENROUTER_API_KEY to .env")
elif AI_PROVIDER == "claude":
    if not CLAUDE_API_KEY or CLAUDE_API_KEY == "sk-ant-your-key-here":
        print("ℹ️  Claude API not configured. Add CLAUDE_API_KEY to .env")
else:
    print(f"ℹ️  AI Provider set to: {AI_PROVIDER}")
