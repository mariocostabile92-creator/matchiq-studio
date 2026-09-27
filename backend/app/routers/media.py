from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from backend.app.core.config import UPLOADS_DIR
from backend.app.core.private_files import contained_regular_file, user_storage_dir
from backend.app.routers.auth import get_current_user


router = APIRouter(prefix="/api/media", tags=["Media"], dependencies=[Depends(get_current_user)])

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
MAX_VIDEO_UPLOAD_BYTES = 80 * 1024 * 1024
MAX_AUDIO_UPLOAD_BYTES = 40 * 1024 * 1024
MAX_IMAGE_UPLOAD_BYTES = 18 * 1024 * 1024


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
def list_media_assets(user=Depends(get_current_user)):
    try:
        user_dir = user_storage_dir(UPLOADS_DIR, user["id"])
    except ValueError:
        raise HTTPException(status_code=404, detail="Media non trovati.") from None
    if not user_dir.is_dir():
        return []
    files = [
        path
        for path in user_dir.iterdir()
        if path.suffix.lower() in ALLOWED_EXTENSIONS
        and path.name.startswith("media_")
        and contained_regular_file(user_dir, path.name) is not None
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [_media_asset(path) for path in files]


@router.post("/upload", response_model=MediaAssetResponse)
async def upload_media_asset(file: UploadFile, user=Depends(get_current_user)):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato non supportato. Puoi caricare immagini, video o audio MP3/WAV/M4A.")

    max_size = MAX_VIDEO_UPLOAD_BYTES if extension in VIDEO_EXTENSIONS else MAX_AUDIO_UPLOAD_BYTES if extension in AUDIO_EXTENSIONS else MAX_IMAGE_UPLOAD_BYTES
    limit = "80 MB" if extension in VIDEO_EXTENSIONS else "40 MB" if extension in AUDIO_EXTENSIONS else "18 MB"
    try:
        user_dir = user_storage_dir(UPLOADS_DIR, user["id"])
    except ValueError:
        raise HTTPException(status_code=404, detail="Percorso media non disponibile.") from None
    user_dir.mkdir(parents=True, exist_ok=True)

    temp_path = None
    total_size = 0
    try:
        with NamedTemporaryFile(mode="wb", prefix=".upload_", suffix=".part", dir=user_dir, delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(status_code=413, detail=f"File troppo pesante. Massimo {limit}.")
                temp_file.write(chunk)

        if total_size == 0:
            raise HTTPException(status_code=400, detail="File vuoto.")

        if extension in IMAGE_EXTENSIONS:
            expected_format = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[extension]
            try:
                with Image.open(temp_path) as image:
                    if image.format != expected_format:
                        raise HTTPException(status_code=400, detail="Il contenuto non corrisponde al formato immagine dichiarato.")
                    image.verify()
            except (OSError, UnidentifiedImageError, ValueError, SyntaxError):
                raise HTTPException(status_code=400, detail="File immagine non valido.") from None

        while True:
            filename = f"media_{uuid4().hex[:12]}{extension}"
            output_path = user_dir / filename
            try:
                output_path.hardlink_to(temp_path)
                break
            except FileExistsError:
                continue
        temp_path.unlink()
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return _media_asset(output_path)
