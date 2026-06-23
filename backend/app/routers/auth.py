import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.app.core.config import STORAGE_DIR

router = APIRouter(prefix="/api/auth", tags=["auth"])

AUTH_DIR = STORAGE_DIR / "auth"
USERS_PATH = AUTH_DIR / "users.json"
SESSIONS_PATH = AUTH_DIR / "sessions.json"
AUTH_DIR.mkdir(parents=True, exist_ok=True)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=1, max_length=128)


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest)


def _normalize_email(email: str) -> str:
    email = email.lower().strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=422, detail="Inserisci una email valida.")
    return email


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
    }


def _create_session(response: Response, user_id: str) -> None:
    sessions = _read_json(SESSIONS_PATH, {})
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(SESSIONS_PATH, sessions)
    response.set_cookie(
        "matchiq_session",
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 30,
    )


def _current_user_from_request(request: Request) -> dict | None:
    token = request.cookies.get("matchiq_session")
    if not token:
        return None
    sessions = _read_json(SESSIONS_PATH, {})
    session = sessions.get(token)
    if not session:
        return None
    users = _read_json(USERS_PATH, {})
    for user in users.values():
        if user.get("id") == session.get("user_id"):
            return user
    return None


@router.post("/register")
def register(payload: RegisterRequest, response: Response):
    users = _read_json(USERS_PATH, {})
    email = _normalize_email(payload.email)
    if email in users:
        return {"success": False, "message": "Esiste gia un account con questa email. Usa Login."}
    user = {
        "id": secrets.token_hex(12),
        "name": payload.name.strip(),
        "email": email,
        "password_hash": _hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users[email] = user
    _write_json(USERS_PATH, users)
    _create_session(response, user["id"])
    return {"success": True, "user": _public_user(user)}


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    users = _read_json(USERS_PATH, {})
    email = _normalize_email(payload.email)
    user = users.get(email)
    if not user or not _verify_password(payload.password, user.get("password_hash", "")):
        return {"success": False, "message": "Email o password non corretti. Se e il primo accesso usa Registrazione."}
    _create_session(response, user["id"])
    return {"success": True, "user": _public_user(user)}


@router.get("/me")
def me(request: Request):
    user = _current_user_from_request(request)
    if not user:
        return {"success": False, "user": None}
    return {"success": True, "user": _public_user(user)}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("matchiq_session")
    sessions = _read_json(SESSIONS_PATH, {})
    if token in sessions:
        del sessions[token]
        _write_json(SESSIONS_PATH, sessions)
    response.delete_cookie("matchiq_session")
    return {"success": True}
