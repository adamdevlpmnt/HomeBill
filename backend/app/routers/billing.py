from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_auth
from app.services.forecast import get_quarterly_forecast

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/estimate")
def get_billing_estimate(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
) -> Dict[str, Any]:
    """
    Retourne l'estimation détaillée de la facture du trimestre en cours :
    - Sonelgaz (facture conjointe Électricité + Gaz) avec décomposition par palier et scénarios bas/central/haut
    - SEAAL (Eau & Assainissement) avec décomposition et scénarios
    - Comparaison aux budgets cibles et indice de confiance.
    """
    return get_quarterly_forecast(db)
