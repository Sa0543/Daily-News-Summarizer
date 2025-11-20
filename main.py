from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from news_scraper import NewsScraper
from rag_processor import RAGProcessor
from dotenv import load_dotenv
import os
from pathlib import Path
import traceback

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="RAG News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get absolute paths for frontend directory
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Verify frontend directory exists
if not FRONTEND_DIR.exists():
    print(f"⚠️ Warning: Frontend directory not found at {FRONTEND_DIR}")
else:
    print(f"✅ Frontend directory found at {FRONTEND_DIR}")

# Mount static files directory
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize components
try:
    scraper = NewsScraper()
    rag = RAGProcessor()
    print("✅ Scraper and RAG processor initialized successfully")
except Exception as e:
    print(f"❌ Error initializing components: {e}")
    traceback.print_exc()

class FetchAndSummarizeRequest(BaseModel):
    categories: List[str]
    max_articles: int = 10

@app.get("/api/categories")
def get_categories():
    """Get available news categories"""
    return {
        "categories": [
            {"name": "General", "icon": "📰"},
            {"name": "Politics", "icon": "🏛️"},
            {"name": "Sports", "icon": "⚽"},
            {"name": "Business", "icon": "💼"},
            {"name": "Technology", "icon": "💻"},
            {"name": "Education", "icon": "📚"},
            {"name": "Entertainment", "icon": "🎬"},
            {"name": "International", "icon": "🌍"},
            {"name": "Health", "icon": "🏥"}
        ]
    }

@app.post("/api/fetch-and-summarize")
def fetch_and_summarize(req: FetchAndSummarizeRequest):
    """Fetch articles and return summaries immediately"""
    try:
        print(f"\n{'='*60}")
        print(f"📥 Request: Fetching {req.max_articles} articles")
        print(f"📑 Categories: {', '.join(req.categories)}")
        print(f"{'='*60}")

        # Fetch articles
        articles = scraper.fetch_rss_news(
            max_articles=req.max_articles,
            categories=req.categories
        )

        print(f"✅ Found {len(articles)} articles")

        if not articles:
            print("⚠️ No articles found")
            return {
                "count": 0,
                "results": [],
                "message": "No articles found for selected categories"
            }

        # Summarize articles
        print(f"🤖 Starting summarization process...")
        summarized = rag.summarize_articles_bulk(articles)

        print(f"✅ Successfully summarized {len(summarized)} articles")
        print(f"{'='*60}\n")

        return {
            "count": len(summarized),
            "results": summarized
        }

    except Exception as e:
        print(f"\n❌ ERROR occurred:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        print(f"\n📋 Full Traceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")

        raise HTTPException(
            status_code=500, 
            detail=f"{type(e).__name__}: {str(e)}"
        )

@app.get("/")
def serve_ui():
    """Serve the main HTML page"""
    return FileResponse("frontend/index.html")

@app.get("/health")
def health_check():
    """Health check endpoint to verify setup"""
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")

    return {
        "status": "healthy",
        "frontend_directory": str(FRONTEND_DIR),
        "frontend_exists": FRONTEND_DIR.exists(),
        "index_html_exists": (FRONTEND_DIR / "index.html").exists(),
        "style_css_exists": (FRONTEND_DIR / "style.css").exists(),
        "script_js_exists": (FRONTEND_DIR / "script.js").exists(),
        "huggingface_token_configured": bool(hf_token)
    }
