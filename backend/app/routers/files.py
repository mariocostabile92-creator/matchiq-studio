import mimetypes
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.app.core.config import RENDERS_DIR, UPLOADS_DIR
from backend.app.core.private_files import contained_regular_file, user_storage_dir
from backend.app.routers.auth import get_current_user


router = APIRouter(tags=["Private files"])
_UPLOAD_NAME = re.compile(r"media_[0-9a-f]{12}\.(?:jpg|jpeg|png|webp|mp4|mov|webm|m4v|mp3|wav|m4a|aac|ogg)\Z")
_RENDER_NAME = re.compile(r"matchiq_studio_reel_[0-9a-f]{10}\.mp4\Z")


def _serve_private_file(root, filename: str, user, pattern: re.Pattern) -> FileResponse:
    if not pattern.fullmatch(filename):
        raise HTTPException(status_code=404, detail="File non trovato.")
    try:
        directory = user_storage_dir(root, user["id"])
    except ValueError:
        raise HTTPException(status_code=404, detail="File non trovato.") from None
    path = contained_regular_file(directory, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="File non trovato.")

    response = FileResponse(path, media_type=mimetypes.guess_type(path.name)[0])
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@router.get("/uploads/{filename}", include_in_schema=False)
def get_uploaded_file(filename: str, user=Depends(get_current_user)):
    return _serve_private_file(UPLOADS_DIR, filename, user, _UPLOAD_NAME)


@router.get("/renders/{filename}", include_in_schema=False)
def get_rendered_file(filename: str, user=Depends(get_current_user)):
    return _serve_private_file(RENDERS_DIR, filename, user, _RENDER_NAME)
