import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Reading, Meter, MeterEvent


def round_cur(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_meter_readings_sorted(
    db: Session, meter_id: int
) -> List[Reading]:
    """Récupère tous les relevés d'un compteur triés par date croissante."""
    return (
        db.query(Reading)
        .filter(Reading.meter_id == meter_id)
        .order_by(Reading.read_at.asc())
        .all()
    )


def calculate_intervals_consumption(
    readings: List[Reading],
    events: Optional[List[MeterEvent]] = None,
) -> List[Dict[str, Any]]:
    """
    Calcule la consommation pour chaque intervalle entre deux relevés successifs.
    Gère les remplacements de compteurs (MeterEvent).
    Retourne une liste d'intervalles avec :
    - start_date, end_date, days_count
    - start_index, end_index, consumption, daily_rate
    """
    if len(readings) < 2:
        return []

    events_by_date = {}
    if events:
        for ev in events:
            events_by_date[ev.event_date] = ev

    intervals = []
    for i in range(len(readings) - 1):
        r_start = readings[i]
        r_end = readings[i + 1]

        days = (r_end.read_at - r_start.read_at).days
        if days <= 0:
            continue

        # Vérifier si un événement de remplacement a eu lieu entre r_start.read_at et r_end.read_at
        replacement_event = None
        for ev_date, ev in events_by_date.items():
            if r_start.read_at <= ev_date <= r_end.read_at:
                replacement_event = ev
                break

        if replacement_event:
            # Consommation = (ancien index final - index début) + (index fin - nouvel index début)
            part1 = max(Decimal("0.00"), Decimal(str(replacement_event.old_index_end)) - Decimal(str(r_start.index_value)))
            part2 = max(Decimal("0.00"), Decimal(str(r_end.index_value)) - Decimal(str(replacement_event.new_index_start)))
            consumption = part1 + part2
        else:
            consumption = max(Decimal("0.00"), Decimal(str(r_end.index_value)) - Decimal(str(r_start.index_value)))

        daily_rate = consumption / Decimal(str(days))

        intervals.append({
            "start_date": r_start.read_at,
            "end_date": r_end.read_at,
            "days_count": days,
            "start_index": Decimal(str(r_start.index_value)),
            "end_index": Decimal(str(r_end.index_value)),
            "consumption": round_cur(consumption),
            "daily_rate": daily_rate,
        })

    return intervals


def allocate_consumption_to_daily_buckets(
    intervals: List[Dict[str, Any]]
) -> Dict[datetime.date, Decimal]:
    """
    Répartit linéairement la consommation de chaque intervalle sur chacun de ses jours.
    Exemple : un relevé du vendredi au vendredi répartit exactement 1/7ème de la consommation
    sur chaque jour de la semaine.
    """
    daily_consumption: Dict[datetime.date, Decimal] = {}

    for interval in intervals:
        start_d = interval["start_date"]
        end_d = interval["end_date"]
        days = interval["days_count"]
        daily_rate = interval["daily_rate"]

        curr = start_d
        while curr < end_d:
            # On attribue le daily_rate à la date curr
            daily_consumption[curr] = daily_consumption.get(curr, Decimal("0.00")) + daily_rate
            curr += datetime.timedelta(days=1)

    return daily_consumption


def aggregate_by_period(
    daily_map: Dict[datetime.date, Decimal],
    period_type: str = "week",  # week, month, quarter, year
) -> List[Dict[str, Any]]:
    """
    Agrège les consommations journalières par période calendaire :
    - week : ISO Year + Week (ex: 2026-W24)
    - month : YYYY-MM (ex: 2026-06)
    - quarter : YYYY-QX (ex: 2026-Q2)
    - year : YYYY (ex: 2026)
    """
    if not daily_map:
        return []

    sorted_dates = sorted(daily_map.keys())
    periods: Dict[str, Dict[str, Any]] = {}

    for d in sorted_dates:
        val = daily_map[d]
        if period_type == "week":
            iso_year, iso_week, _ = d.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            label = f"S{iso_week:02d}"
        elif period_type == "month":
            key = d.strftime("%Y-%m")
            label = d.strftime("%b %Y")
        elif period_type == "quarter":
            q = (d.month - 1) // 3 + 1
            key = f"{d.year}-Q{q}"
            label = f"T{q} {d.year}"
        elif period_type == "year":
            key = str(d.year)
            label = str(d.year)
        else:
            key = d.strftime("%Y-%m-%d")
            label = key

        if key not in periods:
            periods[key] = {
                "period_key": key,
                "label": label,
                "start_date": d,
                "end_date": d,
                "days_count": 0,
                "consumption": Decimal("0.00"),
            }

        p = periods[key]
        p["consumption"] += val
        p["days_count"] += 1
        if d > p["end_date"]:
            p["end_date"] = d

    result = []
    for k in sorted(periods.keys()):
        p = periods[k]
        p["consumption"] = round_cur(p["consumption"])
        p["daily_rate"] = (
            round_cur(p["consumption"] / Decimal(str(p["days_count"])))
            if p["days_count"] > 0
            else Decimal("0.00")
        )
        result.append(p)

    return result


def validate_reading_input(
    db: Session,
    meter_id: int,
    read_at: datetime.date,
    index_value: Decimal,
    exclude_reading_id: Optional[int] = None,
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Valide un nouvel index :
    - Refuse si index < index précédent (sauf remplacement).
    - Alerte non bloquante si > 3x médiane ou écart de jours anormal.
    """
    query = db.query(Reading).filter(Reading.meter_id == meter_id)
    if exclude_reading_id:
        query = query.filter(Reading.id != exclude_reading_id)
    readings = query.order_by(Reading.read_at.asc()).all()

    events = db.query(MeterEvent).filter(MeterEvent.meter_id == meter_id).all()
    events_dates = {ev.event_date: ev for ev in events}

    # Trouver le relevé le plus proche avant read_at
    prev_reading = None
    next_reading = None
    for r in readings:
        if r.read_at < read_at:
            if prev_reading is None or r.read_at > prev_reading.read_at:
                prev_reading = r
        elif r.read_at > read_at:
            if next_reading is None or r.read_at < next_reading.read_at:
                next_reading = r

    # Règle stricte : refus si index < précédent (sans remplacement)
    if prev_reading is not None:
        has_event = any(prev_reading.read_at <= ed <= read_at for ed in events_dates)
        if not has_event and index_value < Decimal(str(prev_reading.index_value)):
            return False, f"L'index ({index_value}) ne peut pas être inférieur à l'index précédent ({prev_reading.index_value}) du {prev_reading.read_at}.", {}

    if next_reading is not None:
        has_event = any(read_at <= ed <= next_reading.read_at for ed in events_dates)
        if not has_event and index_value > Decimal(str(next_reading.index_value)):
            return False, f"L'index ({index_value}) ne peut pas être supérieur à l'index suivant ({next_reading.index_value}) du {next_reading.read_at}.", {}

    # Détection d'anomalie
    is_anomaly = False
    warning_msg = None
    consumption = Decimal("0.00")
    days_count = 1
    daily_rate = Decimal("0.00")

    if prev_reading is not None:
        days_count = max(1, (read_at - prev_reading.read_at).days)
        consumption = index_value - Decimal(str(prev_reading.index_value))
        daily_rate = consumption / Decimal(str(days_count))

        # Calculer la médiane des consommations journalières habituelles
        intervals = calculate_intervals_consumption(readings, events)
        if len(intervals) >= 2:
            rates = sorted([inv["daily_rate"] for inv in intervals])
            median_rate = rates[len(rates) // 2]
            if median_rate > Decimal("0.00") and daily_rate > (median_rate * Decimal("3.0")):
                is_anomaly = True
                warning_msg = (
                    f"Consommation anormalement élevée : {round_cur(daily_rate)}/jour vs médiane {round_cur(median_rate)}/jour."
                )

        if days_count > 14:
            is_anomaly = True
            msg = f"Écart de temps important ({days_count} jours depuis le dernier relevé)."
            warning_msg = f"{warning_msg} {msg}" if warning_msg else msg

    meta = {
        "consumption": round_cur(consumption),
        "days_count": days_count,
        "daily_rate": round_cur(daily_rate),
        "is_anomaly": is_anomaly,
        "warning_message": warning_msg,
        "previous_index": Decimal(str(prev_reading.index_value)) if prev_reading else None,
        "previous_read_at": prev_reading.read_at if prev_reading else None,
    }

    return True, None, meta
