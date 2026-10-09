import json
import csv
import io
import datetime
from decimal import Decimal
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.auth import require_auth
from app.models import Setting, Meter, Reading, MeterEvent, BillingCycle, Invoice
from app.schemas import SettingsDict
from app.config import settings as app_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsDict)
def get_settings(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Récupère les paramètres de l'application."""
    def parse_d(val: str, default: str) -> datetime.date:
        try:
            return datetime.date.fromisoformat(val)
        except Exception:
            return datetime.date.fromisoformat(default)

    db_items = {s.key: s.value for s in db.query(Setting).all()}

    return SettingsDict(
        budget_electricity_quarterly=Decimal(
            db_items.get("budget_electricity_quarterly", "3500.00")
        ),
        budget_gas_quarterly=Decimal(
            db_items.get("budget_gas_quarterly", "3000.00")
        ),
        budget_sonelgaz_quarterly=Decimal(
            db_items.get("budget_sonelgaz_quarterly", "7000.00")
        ),
        budget_water_quarterly=Decimal(
            db_items.get("budget_water_quarterly", "600.00")
        ),
        reading_day_of_week=int(db_items.get("reading_day_of_week", "4")),
        theme=db_items.get("theme", "auto"),
        pcs_factor_gas=Decimal(db_items.get("pcs_factor_gas", "9.7")),
        last_invoice_date_sonelgaz=parse_d(
            db_items.get("last_invoice_date_sonelgaz", "2026-06-16"), "2026-06-16"
        ),
        last_invoice_index_electricity=Decimal(
            db_items.get("last_invoice_index_electricity", "7331.000")
        ),
        last_invoice_index_gas=Decimal(
            db_items.get("last_invoice_index_gas", "5611.000")
        ),
        next_read_date_sonelgaz=parse_d(
            db_items.get("next_read_date_sonelgaz", "2026-09-16"), "2026-09-16"
        ),
        next_cycle_code_sonelgaz=db_items.get(
            "next_cycle_code_sonelgaz", "2026-Q3"
        ),
        last_invoice_date_water=parse_d(
            db_items.get("last_invoice_date_water", "2025-04-09"), "2025-04-09"
        ),
        last_invoice_index_water=Decimal(
            db_items.get("last_invoice_index_water", "120.000")
        ),
        next_read_date_water=parse_d(
            db_items.get("next_read_date_water", "2025-07-09"), "2025-07-09"
        ),
        next_cycle_code_water=db_items.get(
            "next_cycle_code_water", "2025-Q3"
        ),
    )


@router.put("", response_model=SettingsDict)
def update_settings(
    payload: SettingsDict,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Met à jour les paramètres de l'application."""
    data = payload.model_dump()
    for k, v in data.items():
        s = db.query(Setting).filter(Setting.key == k).first()
        val_str = str(v)
        if s:
            s.value = val_str
        else:
            s = Setting(key=k, value=val_str)
            db.add(s)
    db.commit()
    return payload


@router.get("/export/json")
def export_database_json(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Exporte l'ensemble des données au format JSON."""
    meters = [
        {
            "id": m.id,
            "meter_type": m.meter_type,
            "name": m.name,
            "meter_number": m.meter_number,
            "unit": m.unit,
        }
        for m in db.query(Meter).all()
    ]
    readings = [
        {
            "id": r.id,
            "meter_id": r.meter_id,
            "read_at": r.read_at.isoformat(),
            "index_value": str(r.index_value),
            "note": r.note,
        }
        for r in db.query(Reading).order_by(Reading.read_at.asc()).all()
    ]
    events = [
        {
            "id": ev.id,
            "meter_id": ev.meter_id,
            "event_type": ev.event_type,
            "event_date": ev.event_date.isoformat(),
            "old_index_end": str(ev.old_index_end),
            "new_index_start": str(ev.new_index_start),
            "note": ev.note,
        }
        for ev in db.query(MeterEvent).all()
    ]
    cycles = [
        {
            "id": c.id,
            "cycle_code": c.cycle_code,
            "energy_group": c.energy_group,
            "quarter": c.quarter,
            "year": c.year,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "is_closed": c.is_closed,
        }
        for c in db.query(BillingCycle).all()
    ]
    invoices = [
        {
            "id": inv.id,
            "energy_group": inv.energy_group,
            "cycle_code": inv.cycle_code,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
            "actual_amount": str(inv.actual_amount),
            "estimated_amount": str(inv.estimated_amount) if inv.estimated_amount else None,
            "variance_amount": str(inv.variance_amount) if inv.variance_amount else None,
            "variance_pct": str(inv.variance_pct) if inv.variance_pct else None,
            "note": inv.note,
        }
        for inv in db.query(Invoice).all()
    ]

    export_obj = {
        "export_date": datetime.datetime.utcnow().isoformat(),
        "meters": meters,
        "readings": readings,
        "events": events,
        "cycles": cycles,
        "invoices": invoices,
    }

    content = json.dumps(export_obj, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=conso_maison_export.json"},
    )


@router.get("/export/csv")
def export_readings_csv(
    meter_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Exporte les relevés de compteurs au format CSV."""
    q = db.query(Reading, Meter).join(Meter, Reading.meter_id == Meter.id)
    if meter_id:
        q = q.filter(Reading.meter_id == meter_id)
    records = q.order_by(Reading.meter_id.asc(), Reading.read_at.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Compteur", "Type", "Unité", "Date_Relevé", "Index", "Note"])

    for r, m in records:
        writer.writerow([
            r.id,
            m.name,
            m.meter_type,
            m.unit,
            r.read_at.isoformat(),
            str(r.index_value),
            r.note or "",
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=releves_compteurs.csv"},
    )


@router.post("/import/json")
def import_database_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Importe des données à partir d'un fichier JSON."""
    content = file.file.read()
    data = json.loads(content.decode("utf-8"))

    # Importer les relevés
    imported_count = 0
    for r_data in data.get("readings", []):
        m_id = int(r_data["meter_id"])
        r_date = datetime.date.fromisoformat(r_data["read_at"])
        val = Decimal(str(r_data["index_value"]))

        existing = (
            db.query(Reading)
            .filter(Reading.meter_id == m_id, Reading.read_at == r_date)
            .first()
        )
        if existing:
            existing.index_value = val
            existing.note = r_data.get("note")
        else:
            r = Reading(
                meter_id=m_id,
                read_at=r_date,
                index_value=val,
                note=r_data.get("note"),
            )
            db.add(r)
        imported_count += 1

    db.commit()
    return {"success": True, "imported_readings": imported_count}
