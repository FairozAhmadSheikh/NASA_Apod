# api/index.py
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
from requests.adapters import HTTPAdapter, Retry
from cachetools import TTLCache
from dotenv import load_dotenv
import logging

# load local .env for local dev only (Vercel env vars are used in production)
load_dotenv()

logger = logging.getLogger("uvicorn.error")

# Read required env (do not hardcode secrets)
NASA_API_KEY = os.getenv("NASA_API_KEY")

app = FastAPI()

# Serve static files from /static (ensure this folder exists at repo root)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja templates in repo root 'templates' folder
templates = Jinja2Templates(directory="templates")

# Robust requests session (retries + timeouts)
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.3, status_forcelist=(500,502,504))
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Small in-memory cache for APOD metadata (ephemeral; persists only on warm instances)
meta_cache = TTLCache(maxsize=256, ttl=60*60)  # 1 hour

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

def safe_date_input(date_str: str):
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        if dt < datetime(1995, 6, 16).date() or dt > datetime.now().date():
            return None
        return dt.isoformat()
    except ValueError:
        return None

@app.get("/", response_class=HTMLResponse)
def index(request: Request, date: str = None):
    """
    Render APOD page. If NASA_API_KEY is not set in env, show an error message
    (Vercel: set the env var in Project Settings).
    """
    if not NASA_API_KEY:
        # Don't crash at import; show friendly error
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "apod": None, "error": "NASA_API_KEY not set. Configure it in Vercel Project Settings."}
        )

    date_val = safe_date_input(date)
    cache_key = date_val or "today"

    # serve from metadata cache if available
    if cache_key in meta_cache:
        apod = meta_cache[cache_key]
    else:
        params = {"api_key": NASA_API_KEY, "hd": True}
        if date_val:
            params["date"] = date_val

        try:
            resp = session.get(NASA_APOD_URL, params=params, timeout=6)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.exception("Failed to fetch APOD")
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "apod": None, "error": "Failed to contact NASA APOD service."}
            )

        # Normalize minimal fields for the template
        apod = {
            "title": data.get("title"),
            "date": data.get("date"),
            "explanation": data.get("explanation"),
            "media_type": data.get("media_type"),
            "url": data.get("url"),
            "hdurl": data.get("hdurl")
        }
        meta_cache[cache_key] = apod

    return templates.TemplateResponse("index.html", {"request": request, "apod": apod, "error": None})

# Simple healthcheck
@app.get("/_health")
def health():
    return {"ok": True}
