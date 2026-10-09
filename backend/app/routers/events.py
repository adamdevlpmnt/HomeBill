from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_auth
from app.models import MeterEvent, Meter
from app.schemas import MeterEventResponse, MeterEventCreate

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=List[MeterEventResponse])
def get_events(
    meter_id: int = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Liste des événements compteurs (remplacements)."""
    q = db.query(MeterEvent)
    if meter_id:
        q = q.filter(MeterEvent.meter_id == meter_id)
    return q.order_by(MeterEvent.event_date.desc()).all()


@router.post("", response_model=MeterEventResponse)
def create_event(
    payload: MeterEventCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Enregistre un événement de remplacement ou réinitialisation d'un compteur."""
    meter = db.query(Meter).filter(Meter.id == payload.meter_id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Compteur introuvable.")

    event = MeterEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Supprime un événement."""
    event = db.query(MeterEvent).filter(MeterEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable.")
    db.delete(event)
    db.commit()
    return {"success": True, "deleted_id": event_id}
