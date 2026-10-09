import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_auth
from app.models import BillingCycle
from app.schemas import BillingCycleResponse, BillingCycleCreate

router = APIRouter(prefix="/api/cycles", tags=["cycles"])


@router.get("", response_model=List[BillingCycleResponse])
def get_cycles(
    energy_group: str = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Liste tous les cycles de facturation."""
    q = db.query(BillingCycle)
    if energy_group:
        q = q.filter(BillingCycle.energy_group == energy_group)
    return q.order_by(BillingCycle.start_date.desc()).all()


@router.post("", response_model=BillingCycleResponse)
def create_cycle(
    payload: BillingCycleCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Crée un nouveau cycle de facturation trimestriel."""
    existing = (
        db.query(BillingCycle)
        .filter(
            BillingCycle.energy_group == payload.energy_group,
            BillingCycle.cycle_code == payload.cycle_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Ce cycle existe déjà.")
    cycle = BillingCycle(**payload.model_dump())
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle
