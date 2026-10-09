import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_auth
from app.models import Meter, Reading, MeterEvent
from app.services.consumption import (
    get_meter_readings_sorted,
    calculate_intervals_consumption,
    allocate_consumption_to_daily_buckets,
    aggregate_by_period,
    round_cur,
)
from app.services.billing import load_default_tariffs

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/timeseries")
def get_timeseries_analytics(
    period: str = Query("week", pattern="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
) -> List[Dict[str, Any]]:
    """
    Retourne les consommations agrégées par période (semaine ISO, mois, trimestre, année)
    avec interpolation journalière linéaire.
    """
    tariffs = load_default_tariffs()
    pcs_gas = Decimal(str(tariffs["gas"].get("pcs_factor", "9.7")))

    meters = {m.meter_type: m for m in db.query(Meter).all()}

    # Récupérer les maps journalières pour chaque énergie
    daily_maps: Dict[str, Dict[datetime.date, Decimal]] = {}
    for m_type, m in meters.items():
        readings = get_meter_readings_sorted(db, m.id)
        events = db.query(MeterEvent).filter(MeterEvent.meter_id == m.id).all()
        intervals = calculate_intervals_consumption(readings, events)
        daily_maps[m_type] = allocate_consumption_to_daily_buckets(intervals)

    # Obtenir toutes les dates couvertes
    all_dates = set()
    for d_map in daily_maps.values():
        all_dates.update(d_map.keys())

    if not all_dates:
        return []

    # Agréger chaque énergie
    elec_periods = {
        p["period_key"]: p
        for p in aggregate_by_period(daily_maps.get("electricity", {}), period)
    }
    gas_periods = {
        p["period_key"]: p
        for p in aggregate_by_period(daily_maps.get("gas", {}), period)
    }
    water_periods = {
        p["period_key"]: p
        for p in aggregate_by_period(daily_maps.get("water", {}), period)
    }

    all_keys = sorted(
        set(elec_periods.keys())
        | set(gas_periods.keys())
        | set(water_periods.keys())
    )

    result = []
    for k in all_keys:
        p_elec = elec_periods.get(k, {})
        p_gas = gas_periods.get(k, {})
        p_water = water_periods.get(k, {})

        conso_elec = p_elec.get("consumption", Decimal("0.00"))
        conso_gas_m3 = p_gas.get("consumption", Decimal("0.00"))
        conso_gas_th = round_cur(conso_gas_m3 * pcs_gas)
        conso_water = p_water.get("consumption", Decimal("0.00"))

        label = (
            p_elec.get("label")
            or p_gas.get("label")
            or p_water.get("label")
            or k
        )
        start_d = (
            p_elec.get("start_date")
            or p_gas.get("start_date")
            or p_water.get("start_date")
        )
        end_d = (
            p_elec.get("end_date")
            or p_gas.get("end_date")
            or p_water.get("end_date")
        )
        days = max(
            p_elec.get("days_count", 0),
            p_gas.get("days_count", 0),
            p_water.get("days_count", 0),
            1,
        )

        # Calcul des coûts approximatifs HT + TVA pour les graphiques
        cost_elec = round_cur(conso_elec * Decimal("4.1789") * Decimal("1.09"))
        cost_gas = round_cur(conso_gas_th * Decimal("0.3245") * Decimal("1.09"))
        cost_water = round_cur(conso_water * Decimal("12.00"))

        result.append(
            {
                "period_key": k,
                "label": label,
                "start_date": start_d.isoformat() if start_d else None,
                "end_date": end_d.isoformat() if end_d else None,
                "days_count": days,
                "electricity_kwh": conso_elec,
                "gas_th": conso_gas_th,
                "gas_m3": conso_gas_m3,
                "water_m3": conso_water,
                "electricity_cost": cost_elec,
                "gas_cost": cost_gas,
                "water_cost": cost_water,
                "sonelgaz_total_cost": round_cur(cost_elec + cost_gas),
                "total_cost": round_cur(cost_elec + cost_gas + cost_water),
                "daily_rate_elec": round_cur(conso_elec / Decimal(str(days))),
                "daily_rate_gas_th": round_cur(conso_gas_th / Decimal(str(days))),
                "daily_rate_gas_m3": round_cur(conso_gas_m3 / Decimal(str(days))),
                "daily_rate_water": round_cur(conso_water / Decimal(str(days))),
            }
        )

    return result


@router.get("/sparklines")
def get_sparklines(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth),
) -> Dict[str, Any]:
    """
    Retourne les 12 dernières semaines de consommation pour chaque énergie (mini-courbes d'accueil)
    avec pourcentage de variation par rapport aux 12 semaines précédentes.
    """
    weeks_data = get_timeseries_analytics(period="week", db=db, _=True)
    last_12 = weeks_data[-12:] if len(weeks_data) >= 12 else weeks_data
    prev_12 = weeks_data[-24:-12] if len(weeks_data) >= 24 else []

    def make_summary(field_key: str):
        vals = [float(w[field_key]) for w in last_12]
        sum_last = sum(vals)
        sum_prev = sum([float(w[field_key]) for w in prev_12]) if prev_12 else 0.0

        diff_pct = 0.0
        if sum_prev > 0:
            diff_pct = round(((sum_last - sum_prev) / sum_prev) * 100.0, 1)

        return {
            "values": vals,
            "current_period_sum": round(sum_last, 2),
            "previous_period_sum": round(sum_prev, 2),
            "variation_pct": diff_pct,
        }

    return {
        "electricity": make_summary("electricity_kwh"),
        "gas": make_summary("gas_m3"),
        "water": make_summary("water_m3"),
    }
