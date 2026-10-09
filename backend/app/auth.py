import hmac
import hashlib
import time
from typing import Optional
from fastapi import Request, HTTPException, status, Response
from app.config import settings


def create_session_token() -> str:
    """Génère un token de session signé contenant le timestamp d'émission."""
    ts = str(int(time.time()))
    sig = hmac.new(
        settings.SECRET_KEY.encode(), ts.encode(), hashlib.sha256
    ).hexdigest()
    return f"{ts}:{sig}"


def verify_session_token(token: str) -> bool:
    """Vérifie l'authenticité et la validité du token de session."""
    if not token or ":" not in token:
        return False
    try:
        ts_str, sig = token.split(":", 1)
        ts = int(ts_str)
        max_age_seconds = settings.COOKIE_MAX_AGE_DAYS * 86400
        if time.time() - ts > max_age_seconds:
            return False  # Expiré
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(), ts_str.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False


def set_auth_cookie(response: Response, token: str):
    """Place le cookie de session sécurisé HttpOnly."""
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        max_age=settings.COOKIE_MAX_AGE_DAYS * 86400,
        httponly=True,
        samesite="lax",
        secure=False,  # Laissé à False pour supporter HTTP local / reverse proxy avec HTTPS externe
    )


def clear_auth_cookie(response: Response):
    """Supprime le cookie de session."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite="lax",
    )


def require_auth(request: Request) -> bool:
    """Dépendance FastAPI pour protéger les routes privées."""
    token = request.cookies.get(settings.COOKIE_NAME)
    # Permet aussi un header Authorization Bearer si besoin
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    if not token or not verify_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session non valide ou expirée. Veuillez vous connecter.",
        )
    return True
