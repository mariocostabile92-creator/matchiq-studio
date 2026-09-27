from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class CookieOriginMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_origins: tuple[str, ...]):
        super().__init__(app)
        self.allowed_origins = frozenset(allowed_origins)

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
            origin = request.headers.get("origin")
            cookie_present = "matchiq_session" in request.cookies
            authorization_present = request.headers.get("authorization") is not None
            public_auth_endpoint = request.url.path in {"/api/auth/login", "/api/auth/register"}

            if (
                cookie_present
                and not authorization_present
                and not public_auth_endpoint
                and origin not in self.allowed_origins
            ):
                return JSONResponse(
                    {"detail": "Origin non consentita per una richiesta autenticata."},
                    status_code=403,
                )
            if public_auth_endpoint and origin is not None and origin not in self.allowed_origins:
                return JSONResponse({"detail": "Origin non consentita."}, status_code=403)

        return await call_next(request)
