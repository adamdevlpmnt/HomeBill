import json
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_auth
from app.models import TariffVersion
from app.schemas import TariffVersionResponse, TariffVersionCreate
from app.services.billing import load_default_tariffs

router = APIRouter(prefix="/api/tariffs", tags=["tariffs"])


@router.get("/current")
def get_current_tariffs(
    _: bool = Depends(require_auth),
) -> Dict[str, Any]:
    """Retourne la configuration actuelle des tarifs (config/tarifs.json)."""
    return load_default_tariffs()


@router.put("/current")
def update_current_tariffs(
    payload: Dict[str, Any],
    _: bool = Depends(require_auth),
):
    """Met à jour le fichier config/tarifs.json."""
    path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "tarifs.json"
    if not path.exists():
        path = Path("config/tarifs.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return {"success": True, "message": "Tarifs mis à jour avec succès."}


@router.get("/versions", response_model=List[TariffVersionResponse])
def get_tariff_versions(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Historique des versions de tarifs stockées en base."""
    return db.query(TariffVersion).order_by(TariffVersion.valid_from.desc()).all()


@router.post("/versions", response_model=TariffVersionResponse)
def create_tariff_version(
    payload: TariffVersionCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Enregistre une nouvelle version tarifaire en base."""
    tv = TariffVersion(**payload.model_dump())
    db.add(tv)
    db.commit()
    db.refresh(tv)
    return tv
