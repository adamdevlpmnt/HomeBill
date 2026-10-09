import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_auth
from app.models import Reading, Meter, MeterEvent
from app.schemas import (
    ReadingResponse,
    ReadingCreate,
    ReadingUpdate,
    BulkReadingCreate,
    ReadingPreviewRequest,
    ReadingPreviewResponse,
)
from app.services.consumption import (
    validate_reading_input,
    get_meter_readings_sorted,
    calculate_intervals_consumption,
    round_cur,
)
from app.services.billing import load_default_tariffs

router = APIRouter(prefix="/api/readings", tags=["readings"])


@router.post("/preview", response_model=ReadingPreviewResponse)
def preview_reading(
    payload: ReadingPreviewRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """
    Prévisualisation instantanée pendant la frappe d'un index :
    calcule la consommation implicite, le coût approximatif et détecte les anomalies.
    """
    meter = db.query(Meter).filter(Meter.id == payload.meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compteur introuvable."
        )

    valid, err_msg, meta = validate_reading_input(
        db, payload.meter_id, payload.read_at, payload.index_value
    )

    if not valid:
        return ReadingPreviewResponse(
            meter_id=meter.id,
            meter_type=meter.meter_type,
            unit=meter.unit,
            previous_index=meta.get("previous_index"),
            previous_read_at=meta.get("previous_read_at"),
            consumption=Decimal("0.00"),
            days_count=meta.get("days_count", 1),
            daily_rate=Decimal("0.00"),
            estimated_incremental_cost=Decimal("0.00"),
            is_anomaly=True,
            warning_message=err_msg,
        )

    consumption = meta.get("consumption", Decimal("0.00"))
    days_count = meta.get("days_count", 1)
    daily_rate = meta.get("daily_rate", Decimal("0.00"))

    # Estimation rapide du coût marginal
    tariffs = load_default_tariffs()
    cost = Decimal("0.00")
    if meter.meter_type == "electricity":
        # Prix moyen ~ 4.18 DA/kWh
        cost = round_cur(consumption * Decimal("4.1789") * Decimal("1.09"))
    elif meter.meter_type == "gas":
        # Conversion m3 -> Th puis prix moyen
        pcs = Decimal(str(tariffs["gas"].get("pcs_factor", "9.7")))
        th = consumption * pcs
        cost = round_cur(th * Decimal("0.3245") * Decimal("1.09"))
    elif meter.meter_type == "water":
        # Prix moyen m3 eau + assainissement + redevances ~ 12 DA/m3
        cost = round_cur(consumption * Decimal("12.00"))

    return ReadingPreviewResponse(
        meter_id=meter.id,
        meter_type=meter.meter_type,
        unit=meter.unit,
        previous_index=meta.get("previous_index"),
        previous_read_at=meta.get("previous_read_at"),
        consumption=consumption,
        days_count=days_count,
        daily_rate=daily_rate,
        estimated_incremental_cost=cost,
        is_anomaly=meta.get("is_anomaly", False),
        warning_message=meta.get("warning_message"),
    )


@router.post("/bulk", response_model=List[ReadingResponse])
def create_bulk_readings(
    payload: BulkReadingCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """
    Saisie groupée des index (ex: les 3 compteurs relevés le vendredi).
    Exécute les validations et enregistre en une transaction atomique.
    """
    created_readings = []

    for item in payload.readings:
        meter = db.query(Meter).filter(Meter.id == item.meter_id).first()
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compteur ID {item.meter_id} non trouvé.",
            )

        # Vérifier si un relevé existe déjà à cette date
        existing = (
            db.query(Reading)
            .filter(
                Reading.meter_id == item.meter_id,
                Reading.read_at == payload.read_at,
            )
            .first()
        )
        if existing:
            # Mise à jour
            valid, err_msg, _ = validate_reading_input(
                db, item.meter_id, payload.read_at, item.index_value, exclude_reading_id=existing.id
            )
            if not valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{meter.name} : {err_msg}",
                )
            existing.index_value = item.index_value
            existing.note = payload.note
            created_readings.append(existing)
        else:
            valid, err_msg, _ = validate_reading_input(
                db, item.meter_id, payload.read_at, item.index_value
            )
            if not valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{meter.name} : {err_msg}",
                )
            reading = Reading(
                meter_id=item.meter_id,
                read_at=payload.read_at,
                index_value=item.index_value,
                note=payload.note,
            )
            db.add(reading)
            created_readings.append(reading)

    db.commit()
    for r in created_readings:
        db.refresh(r)

    # Construire la réponse enrichie
    result = []
    for r in created_readings:
        m = db.query(Meter).filter(Meter.id == r.meter_id).first()
        result.append(
            ReadingResponse(
                id=r.id,
                meter_id=r.meter_id,
                read_at=r.read_at,
                index_value=Decimal(str(r.index_value)),
                note=r.note,
                created_at=r.created_at,
                meter_type=m.meter_type if m else None,
            )
        )
    return result


@router.get("", response_model=List[ReadingResponse])
def get_readings(
    meter_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Récupère l'historique des relevés (du plus récent au plus ancien)."""
    query = db.query(Reading)
    if meter_id:
        query = query.filter(Reading.meter_id == meter_id)
    readings = query.order_by(Reading.read_at.desc(), Reading.id.desc()).limit(limit).all()

    # Enrichir avec la consommation précédente
    result = []
    for r in readings:
        m = db.query(Meter).filter(Meter.id == r.meter_id).first()
        prev = (
            db.query(Reading)
            .filter(
                Reading.meter_id == r.meter_id,
                Reading.read_at < r.read_at,
            )
            .order_by(Reading.read_at.desc())
            .first()
        )
        delta = None
        days = None
        daily = None
        if prev:
            delta = Decimal(str(r.index_value)) - Decimal(str(prev.index_value))
            days = max(1, (r.read_at - prev.read_at).days)
            daily = round_cur(delta / Decimal(str(days)))

        result.append(
            ReadingResponse(
                id=r.id,
                meter_id=r.meter_id,
                read_at=r.read_at,
                index_value=Decimal(str(r.index_value)),
                note=r.note,
                created_at=r.created_at,
                meter_type=m.meter_type if m else None,
                consumption_since_previous=delta,
                days_since_previous=days,
                daily_rate=daily,
            )
        )
    return result


@router.put("/{reading_id}", response_model=ReadingResponse)
def update_reading(
    reading_id: int,
    payload: ReadingUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Modifie un relevé existant."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Relevé introuvable.")

    new_index = payload.index_value if payload.index_value is not None else Decimal(str(reading.index_value))
    new_date = payload.read_at if payload.read_at is not None else reading.read_at

    valid, err_msg, _ = validate_reading_input(
        db, reading.meter_id, new_date, new_index, exclude_reading_id=reading.id
    )
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    reading.index_value = new_index
    reading.read_at = new_date
    if payload.note is not None:
        reading.note = payload.note

    db.commit()
    db.refresh(reading)

    m = db.query(Meter).filter(Meter.id == reading.meter_id).first()
    return ReadingResponse(
        id=reading.id,
        meter_id=reading.meter_id,
        read_at=reading.read_at,
        index_value=Decimal(str(reading.index_value)),
        note=reading.note,
        created_at=reading.created_at,
        meter_type=m.meter_type if m else None,
    )


@router.delete("/{reading_id}")
def delete_reading(
    reading_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Supprime un relevé."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Relevé introuvable.")
    db.delete(reading)
    db.commit()
    return {"success": True, "deleted_id": reading_id}
