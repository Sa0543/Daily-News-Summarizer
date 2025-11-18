from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from news_scraper import NewsScraper
from rag_processor import RAGProcessor

app = FastAPI(title="RAG News API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = NewsScraper()
rag = RAGProcessor()

# Mount static files - MUST BE BEFORE THE ROOT ROUTE
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Models
class FetchRequest(BaseModel):
    categories: Optional[List[str]] = None
    max_articles: int = 20

class SummarizeRequest(BaseModel):
    text: str
    summary_length: Optional[str] = "Medium"

class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = 5

LENGTH_MAP = {
    "Brief": (30, 50),
    "Medium": (50, 100),
    "Detailed": (100, 150)
}

# API endpoints FIRST
@app.post("/fetch-news")
def fetch_news(req: FetchRequest):
    try:
        categories = req.categories or scraper.get_available_categories()
        articles = scraper.fetch_rss_news(max_articles=req.max_articles, categories=categories)
        rag.process_articles(articles)
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
def summarize(req: SummarizeRequest):
    try:
        min_len, max_len = LENGTH_MAP.get(req.summary_length, (50, 100))
        summary = rag.summarize_article(req.text, max_length=max_len, min_length=min_len)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search(req: SearchRequest):
    try:
        results = rag.retrieve_relevant_articles(req.query, k=req.k)
        out = []
        for doc in results:
            md = doc.metadata if hasattr(doc, "metadata") else getattr(doc, "meta", {})
            out.append({
                "title": md.get("title", "") or md.get("source", ""),
                "source": md.get("source", ""),
                "url": md.get("url", ""),
                "published": md.get("published", ""),
                "snippet": (doc.page_content[:400] + "...") if len(doc.page_content) > 400 else doc.page_content
            })
        return {"count": len(out), "results": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve HTML LAST
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")
