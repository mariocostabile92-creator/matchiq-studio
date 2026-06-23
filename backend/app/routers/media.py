from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.core.config import UPLOADS_DIR


router = APIRouter(prefix="/api/media", tags=["Media"])

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


class MediaAssetResponse(BaseModel):
    filename: str
    url: str
    size: int
    media_type: str


def _media_asset(path: Path) -> MediaAssetResponse:
    return MediaAssetResponse(
        filename=path.name,
        url=f"/uploads/{path.name}",
        size=path.stat().st_size,
        media_type="audio" if path.suffix.lower() in AUDIO_EXTENSIONS else "video" if path.suffix.lower() in VIDEO_EXTENSIONS else "image",
    )


@router.get("", response_model=list[MediaAssetResponse])
def list_media_assets():
    files = [
        path
        for path in UPLOADS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [_media_asset(path) for path in files]


@router.post("/upload", response_model=MediaAssetResponse)
async def upload_media_asset(file: UploadFile):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato non supportato. Puoi caricare immagini, video o audio MP3/WAV/M4A.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File vuoto.")

    max_size = 80 * 1024 * 1024 if extension in VIDEO_EXTENSIONS else 40 * 1024 * 1024 if extension in AUDIO_EXTENSIONS else 18 * 1024 * 1024
    if len(content) > max_size:
        limit = "80 MB" if extension in VIDEO_EXTENSIONS else "40 MB" if extension in AUDIO_EXTENSIONS else "18 MB"
        raise HTTPException(status_code=413, detail=f"File troppo pesante. Massimo {limit}.")

    filename = f"media_{uuid4().hex[:12]}{extension}"
    output_path = UPLOADS_DIR / filename
    output_path.write_bytes(content)

    return _media_asset(output_path)
