import datetime
from decimal import Decimal
import pytest
from app.models import Reading, MeterEvent
from app.services.consumption import (
    calculate_intervals_consumption,
    allocate_consumption_to_daily_buckets,
    aggregate_by_period,
    validate_reading_input,
)


def test_consumption_simple_interval():
    r1 = Reading(id=1, meter_id=1, read_at=datetime.date(2026, 5, 1), index_value=Decimal("1000.000"))
    r2 = Reading(id=2, meter_id=1, read_at=datetime.date(2026, 5, 8), index_value=Decimal("1070.000"))

    intervals = calculate_intervals_consumption([r1, r2])
    assert len(intervals) == 1
    inv = intervals[0]
    assert inv["days_count"] == 7
    assert inv["consumption"] == Decimal("70.00")
    assert inv["daily_rate"] == Decimal("10.00")


def test_consumption_meter_replacement_event():
    """Vérifie qu'un remplacement de compteur ne fausse pas la différence d'index."""
    # Ancien compteur s'arrête à 1500, nouveau démarre à 0
    r1 = Reading(id=1, meter_id=1, read_at=datetime.date(2026, 5, 1), index_value=Decimal("1400.000"))
    r2 = Reading(id=2, meter_id=1, read_at=datetime.date(2026, 5, 8), index_value=Decimal("50.000"))

    event = MeterEvent(
        id=1,
        meter_id=1,
        event_type="replacement",
        event_date=datetime.date(2026, 5, 4),
        old_index_end=Decimal("1500.000"),
        new_index_start=Decimal("0.000"),
    )

    intervals = calculate_intervals_consumption([r1, r2], [event])
    assert len(intervals) == 1
    # Conso attendue = (1500 - 1400) + (50 - 0) = 100 + 50 = 150
    assert intervals[0]["consumption"] == Decimal("150.00")


def test_daily_allocation_and_period_aggregation():
    """Vérifie la répartition linéaire journalière au prorata des jours."""
    r1 = Reading(id=1, meter_id=1, read_at=datetime.date(2026, 5, 1), index_value=Decimal("100.000"))
    r2 = Reading(id=2, meter_id=1, read_at=datetime.date(2026, 5, 11), index_value=Decimal("200.000"))

    intervals = calculate_intervals_consumption([r1, r2])
    daily_map = allocate_consumption_to_daily_buckets(intervals)

    # 10 jours écoulés, 100 unités de consommation = 10 unités par jour
    assert len(daily_map) == 10
    for d, val in daily_map.items():
        assert val == Decimal("10.00")

    # Agrégation par mois
    months = aggregate_by_period(daily_map, period_type="month")
    assert len(months) == 1
    assert months[0]["consumption"] == Decimal("100.00")
