from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import APP_NAME, APP_VERSION, FRONTEND_DIR, RENDERS_DIR, UPLOADS_DIR
from backend.app.routers import campaigns, media, projects, reels

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_for_app_shell(request, call_next):
    response = await call_next(request)
    path = request.url.path

    if (
        path == "/"
        or path.endswith(".html")
        or path.endswith(".js")
        or path.endswith(".css")
        or path.endswith(".json")
        or path.endswith(".svg")
        or path == "/sw.js"
    ):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

app.include_router(reels.router)
app.include_router(projects.router)
app.include_router(campaigns.router)
app.include_router(media.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(FRONTEND_DIR / "favicon.ico", media_type="image/x-icon")


app.mount("/renders", StaticFiles(directory=str(RENDERS_DIR)), name="renders")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
