from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from app.config import settings
from app.auth import (
    create_session_token,
    verify_session_token,
    set_auth_cookie,
    clear_auth_cookie,
)
from app.schemas import LoginRequest, AuthStatusResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    """Vérification du mot de passe unique et création de la session."""
    if payload.password != settings.APP_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe incorrect.",
        )
    token = create_session_token()
    set_auth_cookie(response, token)
    return {"success": True, "token": token}


@router.post("/logout")
def logout(response: Response):
    """Déconnexion et invalidation du cookie."""
    clear_auth_cookie(response)
    return {"success": True}


@router.get("/status", response_model=AuthStatusResponse)
def get_status(request: Request):
    """Vérifie si la session actuelle est valide."""
    token = request.cookies.get(settings.COOKIE_NAME)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    is_authed = verify_session_token(token) if token else False
    return AuthStatusResponse(
        authenticated=is_authed,
        app_name=settings.APP_NAME,
        currency_code="DZD",
        currency_symbol="DA",
    )
