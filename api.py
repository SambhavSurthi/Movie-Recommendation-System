import os
from typing import Optional, List, Dict, Any, Tuple
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.pipeline.prediction_pipeline import PredictionPipeline

# =========================
# ENV
# =========================
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"

if not TMDB_API_KEY:
    raise RuntimeError("TMDB_API_KEY missing. Put it in .env as TMDB_API_KEY=xxxx")


# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="Movie Recommender API (Modularized)", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# GLOBALS & PREDICTION INSTANCE
# =========================
recommender = PredictionPipeline()


# =========================
# MODELS
# =========================
class TMDBMovieCard(BaseModel):
    tmdb_id: int
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None

class TMDBMovieDetails(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: List[dict] = []

class TFIDFRecItem(BaseModel):
    title: str
    score: float
    tmdb: Optional[TMDBMovieCard] = None

class SearchBundleResponse(BaseModel):
    query: str
    movie_details: TMDBMovieDetails
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]


# =========================
# UTILS (TMDB Fetch logic)
# =========================
def make_img_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f"{TMDB_IMG_500}{path}"

async def tmdb_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(params)
    q["api_key"] = TMDB_API_KEY
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{TMDB_BASE}{path}", params=q)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"TMDB request error: {type(e).__name__} | {repr(e)}",
        )
    if r.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"TMDB error {r.status_code}: {r.text}"
        )
    return r.json()

async def tmdb_cards_from_results(results: List[dict], limit: int = 20) -> List[TMDBMovieCard]:
    out: List[TMDBMovieCard] = []
    for m in (results or [])[:limit]:
        out.append(
            TMDBMovieCard(
                tmdb_id=int(m["id"]),
                title=m.get("title") or m.get("name") or "",
                poster_url=make_img_url(m.get("poster_path")),
                release_date=m.get("release_date"),
                vote_average=m.get("vote_average"),
            )
        )
    return out

async def tmdb_movie_details(movie_id: int) -> TMDBMovieDetails:
    data = await tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})
    return TMDBMovieDetails(
        tmdb_id=int(data["id"]),
        title=data.get("title") or "",
        overview=data.get("overview"),
        release_date=data.get("release_date"),
        poster_url=make_img_url(data.get("poster_path")),
        backdrop_url=make_img_url(data.get("backdrop_path")),
        genres=data.get("genres", []) or [],
    )

async def tmdb_search_movies(query: str, page: int = 1) -> Dict[str, Any]:
    return await tmdb_get(
        "/search/movie",
        {"query": query, "include_adult": "false", "language": "en-US", "page": page},
    )

async def tmdb_search_first(query: str) -> Optional[dict]:
    data = await tmdb_search_movies(query=query, page=1)
    results = data.get("results", [])
    return results[0] if results else None

async def attach_tmdb_card_by_title(title: str) -> Optional[TMDBMovieCard]:
    try:
        m = await tmdb_search_first(title)
        if not m:
            return None
        return TMDBMovieCard(
            tmdb_id=int(m["id"]),
            title=m.get("title") or title,
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
        )
    except Exception:
        return None


# =========================
# STARTUP: PRE-LOAD PREDICTION PIPELINE
# =========================
@app.on_event("startup")
def load_artifacts():
    # Note: Will throw Exception if you haven't run Training Pipeline first!
    try:
        recommender.load_artifacts()
    except Exception as e:
        print(f"Warning: Models not found. You must run 'python main.py' to generate artifacts! Error: {e}")


# =========================
# ROUTES
# =========================
@app.get("/health")
def health():
    return {"status": "ok", "system": "Modular ML Project"}

@app.get("/home", response_model=List[TMDBMovieCard])
async def home(category: str = Query("popular"), limit: int = Query(24, ge=1, le=50)):
    try:
        if category == "trending":
            data = await tmdb_get("/trending/movie/day", {"language": "en-US"})
            return await tmdb_cards_from_results(data.get("results", []), limit=limit)
        if category not in {"popular", "top_rated", "upcoming", "now_playing"}:
            raise HTTPException(status_code=400, detail="Invalid category")
        data = await tmdb_get(f"/movie/{category}", {"language": "en-US", "page": 1})
        return await tmdb_cards_from_results(data.get("results", []), limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Home route failed: {e}")

@app.get("/tmdb/search")
async def tmdb_search(query: str = Query(..., min_length=1), page: int = Query(1, ge=1, le=10)):
    return await tmdb_search_movies(query=query, page=page)

@app.get("/movie/id/{tmdb_id}", response_model=TMDBMovieDetails)
async def movie_details_route(tmdb_id: int):
    return await tmdb_movie_details(tmdb_id)

@app.get("/recommend/genre", response_model=List[TMDBMovieCard])
async def recommend_genre(tmdb_id: int = Query(...), limit: int = Query(18, ge=1, le=50)):
    details = await tmdb_movie_details(tmdb_id)
    if not details.genres:
        return []
    genre_id = details.genres[0]["id"]
    discover = await tmdb_get(
        "/discover/movie",
        {"with_genres": genre_id, "language": "en-US", "sort_by": "popularity.desc", "page": 1},
    )
    cards = await tmdb_cards_from_results(discover.get("results", []), limit=limit)
    return [c for c in cards if c.tmdb_id != tmdb_id]

@app.get("/recommend/tfidf")
async def recommend_tfidf(title: str = Query(..., min_length=1), top_n: int = Query(10, ge=1, le=50)):
    recs = recommender.recommend_titles(title, top_n=top_n)
    return [{"title": t, "score": s} for t, s in recs]

@app.get("/movie/search", response_model=SearchBundleResponse)
async def search_bundle(query: str = Query(..., min_length=1), tfidf_top_n: int = Query(12, ge=1, le=30), genre_limit: int = Query(12, ge=1, le=30)):
    best = await tmdb_search_first(query)
    if not best:
        raise HTTPException(status_code=404, detail=f"No TMDB movie found for query: {query}")
    tmdb_id = int(best["id"])
    details = await tmdb_movie_details(tmdb_id)

    tfidf_items: List[TFIDFRecItem] = []
    recs: List[Tuple[str, float]] = []
    try:
        recs = recommender.recommend_titles(details.title, top_n=tfidf_top_n)
    except Exception:
        try:
            recs = recommender.recommend_titles(query, top_n=tfidf_top_n)
        except Exception:
            recs = []

    for title, score in recs:
        card = await attach_tmdb_card_by_title(title)
        tfidf_items.append(TFIDFRecItem(title=title, score=score, tmdb=card))

    genre_recs: List[TMDBMovieCard] = []
    if details.genres:
        genre_id = details.genres[0]["id"]
        discover = await tmdb_get(
            "/discover/movie",
            {"with_genres": genre_id, "language": "en-US", "sort_by": "popularity.desc", "page": 1},
        )
        cards = await tmdb_cards_from_results(discover.get("results", []), limit=genre_limit)
        genre_recs = [c for c in cards if c.tmdb_id != details.tmdb_id]

    return SearchBundleResponse(
        query=query,
        movie_details=details,
        tfidf_recommendations=tfidf_items,
        genre_recommendations=genre_recs,
    )
