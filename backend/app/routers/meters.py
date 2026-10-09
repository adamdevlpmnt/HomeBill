from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_auth
from app.models import Meter, Reading
from app.schemas import MeterResponse, MeterCreate

router = APIRouter(prefix="/api/meters", tags=["meters"])


@router.get("", response_model=List[MeterResponse])
def get_meters(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Liste tous les compteurs avec leur dernier index et date."""
    meters = db.query(Meter).all()
    result = []
    for m in meters:
        last_reading = (
            db.query(Reading)
            .filter(Reading.meter_id == m.id)
            .order_by(Reading.read_at.desc())
            .first()
        )
        result.append(
            MeterResponse(
                id=m.id,
                meter_type=m.meter_type,
                name=m.name,
                meter_number=m.meter_number,
                unit=m.unit,
                is_active=m.is_active,
                last_reading_date=last_reading.read_at if last_reading else None,
                last_index_value=(
                    Decimal(str(last_reading.index_value)) if last_reading else None
                ),
            )
        )
    return result


@router.post("", response_model=MeterResponse)
def create_meter(
    payload: MeterCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Crée un compteur."""
    existing = db.query(Meter).filter(Meter.meter_type == payload.meter_type).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un compteur de type {payload.meter_type} existe déjà.",
        )
    meter = Meter(**payload.model_dump())
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter
