from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_auth
from app.models import Invoice, BillingCycle
from app.schemas import InvoiceResponse, InvoiceCreate
from app.services.billing import round_cur

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=List[InvoiceResponse])
def get_invoices(
    energy_group: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Liste des factures réelles enregistrées."""
    q = db.query(Invoice)
    if energy_group:
        q = q.filter(Invoice.energy_group == energy_group)
    return q.order_by(Invoice.cycle_code.desc(), Invoice.id.desc()).all()


@router.post("", response_model=InvoiceResponse)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Enregistre une vraie facture reçue et calcule l'écart avec l'estimation."""
    cycle = (
        db.query(BillingCycle)
        .filter(
            BillingCycle.energy_group == payload.energy_group,
            BillingCycle.cycle_code == payload.cycle_code,
        )
        .first()
    )

    actual = payload.actual_amount
    estimated = payload.estimated_amount

    variance_amt = None
    variance_pct = None
    if estimated is not None and estimated > 0:
        variance_amt = round_cur(actual - estimated)
        variance_pct = round_cur(((actual - estimated) / estimated) * Decimal("100.0"))

    inv_data = payload.model_dump()
    invoice = Invoice(
        **inv_data,
        billing_cycle_id=cycle.id if cycle else None,
        variance_amount=variance_amt,
        variance_pct=variance_pct,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Mise à jour automatique des repères de la dernière facture
    import datetime
    from app.models import Setting, Meter, Reading

    def set_or_update_setting(k: str, val: str):
        st = db.query(Setting).filter(Setting.key == k).first()
        if st:
            st.value = val
        else:
            db.add(Setting(key=k, value=val))

    if payload.energy_group == "sonelgaz":
        set_or_update_setting("last_invoice_date_sonelgaz", payload.invoice_date.isoformat())
        elec_m = db.query(Meter).filter(Meter.meter_type == "electricity").first()
        if elec_m:
            r = (
                db.query(Reading)
                .filter(Reading.meter_id == elec_m.id, Reading.read_at <= payload.invoice_date)
                .order_by(Reading.read_at.desc())
                .first()
            )
            if r:
                set_or_update_setting("last_invoice_index_electricity", str(r.index_value))
        gas_m = db.query(Meter).filter(Meter.meter_type == "gas").first()
        if gas_m:
            r = (
                db.query(Reading)
                .filter(Reading.meter_id == gas_m.id, Reading.read_at <= payload.invoice_date)
                .order_by(Reading.read_at.desc())
                .first()
            )
            if r:
                set_or_update_setting("last_invoice_index_gas", str(r.index_value))

        next_d = payload.invoice_date + datetime.timedelta(days=92)
        set_or_update_setting("next_read_date_sonelgaz", next_d.isoformat())
        if "-Q" in payload.cycle_code:
            try:
                y, q = payload.cycle_code.split("-Q")
                y, q = int(y), int(q)
                next_q = q + 1 if q < 4 else 1
                next_y = y if q < 4 else y + 1
                set_or_update_setting("next_cycle_code_sonelgaz", f"{next_y}-Q{next_q}")
            except Exception:
                pass

    elif payload.energy_group == "water":
        set_or_update_setting("last_invoice_date_water", payload.invoice_date.isoformat())
        water_m = db.query(Meter).filter(Meter.meter_type == "water").first()
        if water_m:
            r = (
                db.query(Reading)
                .filter(Reading.meter_id == water_m.id, Reading.read_at <= payload.invoice_date)
                .order_by(Reading.read_at.desc())
                .first()
            )
            if r:
                set_or_update_setting("last_invoice_index_water", str(r.index_value))

        next_d = payload.invoice_date + datetime.timedelta(days=92)
        set_or_update_setting("next_read_date_water", next_d.isoformat())
        if "-Q" in payload.cycle_code:
            try:
                y, q = payload.cycle_code.split("-Q")
                y, q = int(y), int(q)
                next_q = q + 1 if q < 4 else 1
                next_y = y if q < 4 else y + 1
                set_or_update_setting("next_cycle_code_water", f"{next_y}-Q{next_q}")
            except Exception:
                pass

    db.commit()
    return invoice


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
):
    """Supprime une facture enregistrée."""
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    db.delete(inv)
    db.commit()
    return {"success": True, "deleted_id": invoice_id}
