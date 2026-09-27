import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.app.core.config import SESSION_COOKIE_SECURE, STORAGE_DIR

router = APIRouter(prefix="/api/auth", tags=["auth"])

AUTH_DIR = STORAGE_DIR / "auth"
USERS_PATH = AUTH_DIR / "users.json"
SESSIONS_PATH = AUTH_DIR / "sessions.json"
SQLITE_PATH = AUTH_DIR / "matchiq_auth.sqlite3"
DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
AUTH_DIR.mkdir(parents=True, exist_ok=True)


class _ClosingSQLiteConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=1, max_length=128)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect():
    if USE_POSTGRES:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("DATABASE_URL richiede psycopg. Aggiungi psycopg[binary] a requirements.txt.") from exc
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    conn = sqlite3.connect(SQLITE_PATH, timeout=20, factory=_ClosingSQLiteConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _param() -> str:
    return "%s" if USE_POSTGRES else "?"


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def _execute(conn, sql: str, params=()):
    return conn.execute(sql, params)


def _insert_user_ignore(conn, user: dict) -> None:
    if USE_POSTGRES:
        conn.execute(
            """
            INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (user["id"], user["email"], user["name"], user["password_hash"], user["created_at"], user["updated_at"]),
        )
    else:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, email, name, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user["id"], user["email"], user["name"], user["password_hash"], user["created_at"], user["updated_at"]),
        )


def _init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")

        legacy_users = _read_json(USERS_PATH, {})
        for email, user in legacy_users.items():
            if not isinstance(user, dict):
                continue
            normalized = _normalize_email(user.get("email") or email)
            _insert_user_ignore(conn, {
                "id": user.get("id") or secrets.token_hex(12),
                "email": normalized,
                "name": user.get("name") or "Creator",
                "password_hash": user.get("password_hash") or "",
                "created_at": user.get("created_at") or _now(),
                "updated_at": _now(),
            })

        # Legacy JSON sessions have no reliable revocation/expiry history; require a fresh login.


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 180_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest)


def _normalize_email(email: str) -> str:
    email = (email or "").lower().strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=422, detail="Inserisci una email valida.")
    return email


def _public_user(user) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
    }


def _fetchone(sql: str, params=()):
    with _connect() as conn:
        return conn.execute(sql, params).fetchone()


def _get_user_by_email(email: str):
    return _fetchone(f"SELECT * FROM users WHERE email = {_param()}", (email,))


def _create_user(name: str, email: str, password: str):
    user = {
        "id": secrets.token_hex(12),
        "email": email,
        "name": name.strip() or "Creator",
        "password_hash": _hash_password(password),
        "created_at": _now(),
        "updated_at": _now(),
    }
    with _connect() as conn:
        conn.execute(
            f"""
            INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
            VALUES ({_param()}, {_param()}, {_param()}, {_param()}, {_param()}, {_param()})
            """,
            (user["id"], user["email"], user["name"], user["password_hash"], user["created_at"], user["updated_at"]),
        )
    return _get_user_by_email(email)


def _create_session(response: Response, user_id: str) -> None:
    token = secrets.token_urlsafe(40)
    max_age = 60 * 60 * 24 * 180
    expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    with _connect() as conn:
        conn.execute(
            f"INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES ({_param()}, {_param()}, {_param()}, {_param()})",
            (token, user_id, _now(), expires.isoformat()),
        )
        conn.execute(
            f"DELETE FROM sessions WHERE expires_at < {_param()}",
            (datetime.now(timezone.utc).isoformat(),),
        )
    response.set_cookie(
        "matchiq_session",
        token,
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
        max_age=max_age,
        expires=expires,
        path="/",
    )


def _session_token_from_request(request: Request) -> str | None:
    cookie_present = "matchiq_session" in request.cookies
    authorization = request.headers.get("authorization")
    if cookie_present and authorization is not None:
        raise HTTPException(status_code=401, detail="Invia una sola credenziale per richiesta.")
    if authorization is not None:
        scheme, separator, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token.strip():
            raise HTTPException(status_code=401, detail="Credenziale Authorization non valida.")
        return token.strip()
    if cookie_present:
        return request.cookies.get("matchiq_session") or ""
    return None


def _current_user_from_request(request: Request):
    token = _session_token_from_request(request)
    if not token:
        return None
    return _fetchone(
        f"""
        SELECT users.* FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = {_param()} AND sessions.expires_at > {_param()}
        """,
        (token, datetime.now(timezone.utc).isoformat()),
    )


def get_current_user(request: Request):
    user = _current_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sessione assente, non valida o scaduta.")
    return user


@router.get("/health")
def auth_health():
    return {"success": True}


@router.post("/register")
def register(payload: RegisterRequest, response: Response):
    email = _normalize_email(payload.email)
    existing_user = _get_user_by_email(email)
    if existing_user:
        if _verify_password(payload.password, existing_user["password_hash"]):
            _create_session(response, existing_user["id"])
            return {
                "success": True,
                "message": "Account gia esistente. Accesso effettuato.",
                "user": _public_user(existing_user),
            }
        return {"success": False, "message": "Esiste gia un account con questa email. Usa Login con la password corretta."}

    user = _create_user(payload.name, email, payload.password)
    _create_session(response, user["id"])
    return {"success": True, "user": _public_user(user)}


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    email = _normalize_email(payload.email)
    user = _get_user_by_email(email)
    if not user or not _verify_password(payload.password, user["password_hash"]):
        return {"success": False, "message": "Email o password non corretti. Se e il primo accesso usa Registrazione."}
    _create_session(response, user["id"])
    return {"success": True, "user": _public_user(user)}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"success": True, "user": _public_user(user)}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = _session_token_from_request(request)
    if token:
        with _connect() as conn:
            conn.execute(f"DELETE FROM sessions WHERE token = {_param()}", (token,))
    response.delete_cookie(
        "matchiq_session",
        path="/",
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
    )
    return {"success": True}


_init_db()
