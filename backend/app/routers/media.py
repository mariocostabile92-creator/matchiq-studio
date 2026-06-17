from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.core.config import UPLOADS_DIR


router = APIRouter(prefix="/api/media", tags=["Media"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class MediaAssetResponse(BaseModel):
    filename: str
    url: str
    size: int


def _media_asset(path: Path) -> MediaAssetResponse:
    return MediaAssetResponse(
        filename=path.name,
        url=f"/uploads/{path.name}",
        size=path.stat().st_size,
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
        raise HTTPException(status_code=400, detail="Formato immagine non supportato.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File immagine vuoto.")

    if len(content) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Immagine troppo pesante. Massimo 12 MB.")

    filename = f"media_{uuid4().hex[:12]}{extension}"
    output_path = UPLOADS_DIR / filename
    output_path.write_bytes(content)

    return _media_asset(output_path)
