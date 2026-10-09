import datetime
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import Meter, Reading, MeterEvent, BillingCycle, Setting, Invoice
from app.services.consumption import (
    get_meter_readings_sorted,
    calculate_intervals_consumption,
)
from app.services.billing import (
    load_default_tariffs,
    calculate_sonelgaz_joint_bill,
    calculate_water_bill,
    calculate_bracket_breakdown,
    round_cur,
)


def get_current_or_latest_cycle(
    db: Session, energy_group: str
) -> Optional[BillingCycle]:
    """Trouve le cycle en cours ou le dernier cycle défini."""
    today = datetime.date.today()
    cycle = (
        db.query(BillingCycle)
        .filter(
            BillingCycle.energy_group == energy_group,
            BillingCycle.start_date <= today,
            BillingCycle.end_date >= today,
        )
        .first()
    )
    if not cycle:
        cycle = (
            db.query(BillingCycle)
            .filter(BillingCycle.energy_group == energy_group)
            .order_by(BillingCycle.end_date.desc())
            .first()
        )
    return cycle


def get_active_tariffs(db: Session) -> Dict[str, Any]:
    """Retourne les tarifs par défaut ou depuis la base."""
    return load_default_tariffs()


def calculate_weighted_daily_rate(
    intervals: List[Dict[str, Any]],
    cycle_start: datetime.date,
    cycle_end: datetime.date,
) -> Tuple[Decimal, Decimal]:
    """
    Calcule le taux journalier pondéré :
    - Plus fort poids sur les 4 dernières semaines (28 derniers jours).
    - Renvoie (taux_central, ecart_type).
    """
    relevant_intervals = [
        inv
        for inv in intervals
        if inv["end_date"] >= cycle_start and inv["start_date"] <= cycle_end
    ]

    if not relevant_intervals:
        return Decimal("0.00"), Decimal("0.00")

    if len(relevant_intervals) == 1:
        rate = relevant_intervals[0]["daily_rate"]
        return rate, rate * Decimal("0.15")

    total_weight = Decimal("0.00")
    weighted_sum = Decimal("0.00")
    rates = []

    last_date = relevant_intervals[-1]["end_date"]

    for inv in relevant_intervals:
        rate = inv["daily_rate"]
        rates.append(rate)
        days_from_last = max(0, (last_date - inv["end_date"]).days)
        if days_from_last <= 28:
            weight = Decimal("3.0")
        elif days_from_last <= 56:
            weight = Decimal("1.5")
        else:
            weight = Decimal("1.0")

        weighted_sum += rate * weight
        total_weight += weight

    central_rate = weighted_sum / total_weight if total_weight > 0 else Decimal("0.00")

    if len(rates) > 1:
        mean_rate = sum(rates) / Decimal(str(len(rates)))
        variance = sum((r - mean_rate) ** 2 for r in rates) / Decimal(str(len(rates)))
        std_dev = Decimal(str(math.sqrt(float(variance))))
    else:
        std_dev = central_rate * Decimal("0.15")

    return central_rate, std_dev


def estimate_energy_consumption_with_baseline(
    db: Session,
    meter: Meter,
    baseline_date: datetime.date,
    baseline_index: Decimal,
    next_read_date: datetime.date,
) -> Dict[str, Any]:
    """
    Calcule la consommation cumulée réelle depuis le repère de la dernière facture (date + index)
    et projette la consommation jusqu'à la date de la prochaine relève.
    """
    readings = get_meter_readings_sorted(db, meter.id)
    events = (
        db.query(MeterEvent)
        .filter(MeterEvent.meter_id == meter.id)
        .order_by(MeterEvent.event_date.asc())
        .all()
    )
    intervals = calculate_intervals_consumption(readings, events)

    total_period_days = max(1, (next_read_date - baseline_date).days)

    # Relevés postérieurs à la date de début de la dernière facture
    subsequent_readings = [r for r in readings if r.read_at > baseline_date]

    if not subsequent_readings:
        # Aucun relevé postérieur à la facture précédente
        today = datetime.date.today()
        days_elapsed = max(0, min(total_period_days, (today - baseline_date).days))
        remaining_days = max(0, (next_read_date - today).days)
        return {
            "meter_type": meter.meter_type,
            "name": meter.name,
            "unit": meter.unit,
            "baseline_date": baseline_date,
            "baseline_index": baseline_index,
            "current_index": baseline_index,
            "current_consumption": Decimal("0.00"),
            "projected_consumption_low": Decimal("0.00"),
            "projected_consumption_central": Decimal("0.00"),
            "projected_consumption_high": Decimal("0.00"),
            "daily_rate": Decimal("0.00"),
            "days_elapsed": days_elapsed,
            "total_days": total_period_days,
            "readings_count": 0,
            "confidence_index": 10,
        }

    latest_reading = subsequent_readings[-1]
    current_index = Decimal(str(latest_reading.index_value))

    # Gestion des événements de compteur (remplacement) entre baseline_date et latest_reading.read_at
    events_in_period = [
        e for e in events if baseline_date <= e.event_date <= latest_reading.read_at
    ]
    if events_in_period:
        ev = events_in_period[0]
        consumption_before_event = max(Decimal("0.00"), ev.old_index_end - baseline_index)
        consumption_after_event = max(Decimal("0.00"), current_index - ev.new_index_start)
        realized_consumption = consumption_before_event + consumption_after_event
    else:
        realized_consumption = max(Decimal("0.00"), current_index - baseline_index)

    days_elapsed = max(1, (latest_reading.read_at - baseline_date).days)
    remaining_days = max(0, (next_read_date - latest_reading.read_at).days)

    if remaining_days == 0:
        # Période complète atteinte (ex: relève à la date prévue de la nouvelle facture)
        proj_central = realized_consumption
        proj_low = realized_consumption
        proj_high = realized_consumption
        central_rate = realized_consumption / Decimal(str(days_elapsed))
        confidence = 100
    else:
        central_rate, std_dev = calculate_weighted_daily_rate(
            intervals, baseline_date, next_read_date
        )
        if central_rate == Decimal("0.00") and days_elapsed > 0:
            central_rate = realized_consumption / Decimal(str(days_elapsed))
            std_dev = central_rate * Decimal("0.15")

        proj_central = round_cur(
            realized_consumption + (central_rate * Decimal(str(remaining_days)))
        )
        rate_low = max(Decimal("0.00"), central_rate - std_dev)
        proj_low = round_cur(
            realized_consumption + (rate_low * Decimal(str(remaining_days)))
        )
        rate_high = central_rate + std_dev
        proj_high = round_cur(
            realized_consumption + (rate_high * Decimal(str(remaining_days)))
        )
        confidence = min(
            99,
            int(
                (days_elapsed / total_period_days) * 70
                + min(len(subsequent_readings) * 5, 30)
            ),
        )

    return {
        "meter_type": meter.meter_type,
        "name": meter.name,
        "unit": meter.unit,
        "baseline_date": baseline_date,
        "baseline_index": baseline_index,
        "current_index": current_index,
        "current_consumption": realized_consumption,
        "projected_consumption_low": proj_low,
        "projected_consumption_central": proj_central,
        "projected_consumption_high": proj_high,
        "daily_rate": round_cur(central_rate),
        "days_elapsed": days_elapsed,
        "total_days": total_period_days,
        "readings_count": len(subsequent_readings),
        "confidence_index": confidence,
    }


def get_quarterly_forecast(db: Session) -> Dict[str, Any]:
    """
    Génère l'estimation complète de la prochaine facture trimestrielle à partir des repères
    de la dernière facture reçue (date et index de clôture) :
    - Sonelgaz conjoint (Électricité + Gaz) avec décomposition tarifaire et scénarios bas/central/haut
    - SEAAL (Eau & Assainissement)
    - Totaux, comparaisons aux budgets cibles et indices de confiance
    """
    tariffs = get_active_tariffs(db)

    # Récupérer les compteurs
    elec_meter = db.query(Meter).filter(Meter.meter_type == "electricity").first()
    gas_meter = db.query(Meter).filter(Meter.meter_type == "gas").first()
    water_meter = db.query(Meter).filter(Meter.meter_type == "water").first()

    db_items = {s.key: s.value for s in db.query(Setting).all()}

    def parse_d(val: Optional[str], default: datetime.date) -> datetime.date:
        if not val:
            return default
        try:
            return datetime.date.fromisoformat(val)
        except Exception:
            return default

    def parse_dec(val: Optional[str], default: Decimal) -> Decimal:
        if not val:
            return default
        try:
            return Decimal(val)
        except Exception:
            return default

    # Repères Sonelgaz
    sonelgaz_baseline_date = parse_d(
        db_items.get("last_invoice_date_sonelgaz"), datetime.date(2026, 6, 16)
    )
    sonelgaz_elec_base_index = parse_dec(
        db_items.get("last_invoice_index_electricity"), Decimal("7331.000")
    )
    sonelgaz_gas_base_index = parse_dec(
        db_items.get("last_invoice_index_gas"), Decimal("5611.000")
    )
    sonelgaz_next_read_date = parse_d(
        db_items.get("next_read_date_sonelgaz"), datetime.date(2026, 9, 16)
    )
    sonelgaz_cycle_code = db_items.get("next_cycle_code_sonelgaz", "2026-Q3")

    # Repères Eau
    water_baseline_date = parse_d(
        db_items.get("last_invoice_date_water"), datetime.date(2025, 4, 9)
    )
    water_base_index = parse_dec(
        db_items.get("last_invoice_index_water"), Decimal("120.000")
    )
    water_next_read_date = parse_d(
        db_items.get("next_read_date_water"), datetime.date(2025, 7, 9)
    )
    water_cycle_code = db_items.get("next_cycle_code_water", "2025-Q3")

    # 1. Électricité
    elec_fc = (
        estimate_energy_consumption_with_baseline(
            db,
            elec_meter,
            sonelgaz_baseline_date,
            sonelgaz_elec_base_index,
            sonelgaz_next_read_date,
        )
        if elec_meter
        else {}
    )

    # 2. Gaz
    gas_fc = (
        estimate_energy_consumption_with_baseline(
            db,
            gas_meter,
            sonelgaz_baseline_date,
            sonelgaz_gas_base_index,
            sonelgaz_next_read_date,
        )
        if gas_meter
        else {}
    )

    # 3. Eau
    water_fc = (
        estimate_energy_consumption_with_baseline(
            db,
            water_meter,
            water_baseline_date,
            water_base_index,
            water_next_read_date,
        )
        if water_meter
        else {}
    )

    # Calculs Sonelgaz
    elec_kwh_cen = elec_fc.get("projected_consumption_central", Decimal("0.00"))
    gas_m3_cen = gas_fc.get("projected_consumption_central", Decimal("0.00"))

    elec_kwh_low = elec_fc.get("projected_consumption_low", Decimal("0.00"))
    gas_m3_low = gas_fc.get("projected_consumption_low", Decimal("0.00"))

    elec_kwh_high = elec_fc.get("projected_consumption_high", Decimal("0.00"))
    gas_m3_high = gas_fc.get("projected_consumption_high", Decimal("0.00"))

    sonelgaz_bill_cen = calculate_sonelgaz_joint_bill(
        elec_kwh_cen, gas_m3_cen, tariffs, include_duty_stamp=False
    )
    sonelgaz_bill_low = calculate_sonelgaz_joint_bill(
        elec_kwh_low, gas_m3_low, tariffs, include_duty_stamp=False
    )
    sonelgaz_bill_high = calculate_sonelgaz_joint_bill(
        elec_kwh_high, gas_m3_high, tariffs, include_duty_stamp=False
    )

    # Calculs Eau
    water_m3_cen = water_fc.get("projected_consumption_central", Decimal("0.00"))
    water_m3_low = water_fc.get("projected_consumption_low", Decimal("0.00"))
    water_m3_high = water_fc.get("projected_consumption_high", Decimal("0.00"))

    water_bill_cen = calculate_water_bill(
        water_m3_cen, tariffs, include_duty_stamp=False
    )
    water_bill_low = calculate_water_bill(
        water_m3_low, tariffs, include_duty_stamp=False
    )
    water_bill_high = calculate_water_bill(
        water_m3_high, tariffs, include_duty_stamp=False
    )

    # Paramètres de budget
    budget_sonelgaz = parse_dec(
        db_items.get("budget_sonelgaz_quarterly"), Decimal("7000.00")
    )
    budget_water = parse_dec(
        db_items.get("budget_water_quarterly"), Decimal("600.00")
    )

    total_net_ttc_low = sonelgaz_bill_low["net_ttc"] + water_bill_low["net_ttc"]
    total_net_ttc_central = sonelgaz_bill_cen["net_ttc"] + water_bill_cen["net_ttc"]
    total_net_ttc_high = sonelgaz_bill_high["net_ttc"] + water_bill_high["net_ttc"]
    total_budget = budget_sonelgaz + budget_water

    days_elapsed = max(elec_fc.get("days_elapsed", 1), gas_fc.get("days_elapsed", 1))
    total_days = max(elec_fc.get("total_days", 92), gas_fc.get("total_days", 92))
    progress_pct = round_cur(
        Decimal(str(days_elapsed)) / Decimal(str(total_days)) * Decimal("100.0")
    )

    confidence = min(
        100,
        int(
            (
                elec_fc.get("confidence_index", 50)
                + gas_fc.get("confidence_index", 50)
                + water_fc.get("confidence_index", 50)
            )
            / 3
        ),
    )

    return {
        "cycle_code": sonelgaz_cycle_code,
        "start_date": sonelgaz_baseline_date,
        "end_date": sonelgaz_next_read_date,
        "days_elapsed": days_elapsed,
        "total_days": total_days,
        "progress_pct": min(Decimal("100.00"), progress_pct),
        "confidence_index": confidence,
        "readings_count": (
            elec_fc.get("readings_count", 0)
            + gas_fc.get("readings_count", 0)
            + water_fc.get("readings_count", 0)
        ),
        "sonelgaz": {
            "bill_central": sonelgaz_bill_cen,
            "net_ttc_low": sonelgaz_bill_low["net_ttc"],
            "net_ttc_central": sonelgaz_bill_cen["net_ttc"],
            "net_ttc_high": sonelgaz_bill_high["net_ttc"],
            "budget_target": budget_sonelgaz,
            "target_variance": round_cur(
                sonelgaz_bill_cen["net_ttc"] - budget_sonelgaz
            ),
            "electricity_realized": elec_fc.get(
                "current_consumption", Decimal("0.00")
            ),
            "electricity_projected": elec_kwh_cen,
            "gas_realized_m3": gas_fc.get("current_consumption", Decimal("0.00")),
            "gas_projected_m3": gas_m3_cen,
            "baseline_date": sonelgaz_baseline_date,
            "baseline_index_elec": sonelgaz_elec_base_index,
            "baseline_index_gas": sonelgaz_gas_base_index,
            "next_read_date": sonelgaz_next_read_date,
        },
        "water": {
            "bill_central": water_bill_cen,
            "net_ttc_low": water_bill_low["net_ttc"],
            "net_ttc_central": water_bill_cen["net_ttc"],
            "net_ttc_high": water_bill_high["net_ttc"],
            "budget_target": budget_water,
            "target_variance": round_cur(water_bill_cen["net_ttc"] - budget_water),
            "water_realized_m3": water_fc.get("current_consumption", Decimal("0.00")),
            "water_projected_m3": water_m3_cen,
            "baseline_date": water_baseline_date,
            "baseline_index": water_base_index,
            "next_read_date": water_next_read_date,
        },
        "totals": {
            "net_ttc_low": total_net_ttc_low,
            "net_ttc_central": total_net_ttc_central,
            "net_ttc_high": total_net_ttc_high,
            "budget_target": total_budget,
            "target_variance": round_cur(total_net_ttc_central - total_budget),
        },
    }
