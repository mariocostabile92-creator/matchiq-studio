import re
import stat
from pathlib import Path


_USER_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


def user_storage_dir(root: Path, user_id: str) -> Path:
    user_id = str(user_id)
    if not _USER_ID.fullmatch(user_id):
        raise ValueError("Identificativo utente non valido.")

    root_path = root.resolve()
    raw_directory = root_path / user_id
    if raw_directory.is_symlink():
        raise ValueError("La directory utente non puo essere un symlink.")
    directory = raw_directory.resolve()
    if not directory.is_relative_to(root_path):
        raise ValueError("Percorso utente non valido.")
    return directory


def contained_regular_file(directory: Path, filename: str) -> Path | None:
    if not filename or filename in {".", ".."} or "/" in filename or "\\" in filename:
        return None

    try:
        root = directory.resolve(strict=True)
        raw_candidate = root / filename
        if raw_candidate.is_symlink():
            return None
        candidate = raw_candidate.resolve(strict=True)
        candidate.relative_to(root)
        mode = candidate.lstat().st_mode
    except (OSError, RuntimeError, ValueError):
        return None

    if not stat.S_ISREG(mode):
        return None
    return candidate
