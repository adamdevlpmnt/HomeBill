import datetime
from decimal import Decimal

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Meter(Base):
    __tablename__ = "meters"

    id = Column(Integer, primary_key=True, index=True)
    meter_type = Column(String(32), unique=True, nullable=False)  # electricity, gas, water
    name = Column(String(128), nullable=False)
    meter_number = Column(String(64), nullable=True)
    unit = Column(String(16), nullable=False)  # kWh, m3
    is_active = Column(Boolean, default=True, nullable=False)

    readings = relationship(
        "Reading", back_populates="meter", cascade="all, delete-orphan", order_by="Reading.read_at"
    )
    events = relationship(
        "MeterEvent", back_populates="meter", cascade="all, delete-orphan", order_by="MeterEvent.event_date"
    )


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id", ondelete="CASCADE"), nullable=False, index=True)
    read_at = Column(Date, nullable=False, index=True)
    index_value = Column(Numeric(14, 3), nullable=False)
    note = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)

    meter = relationship("Meter", back_populates="readings")

    __table_args__ = (
        UniqueConstraint("meter_id", "read_at", name="uq_meter_read_at"),
    )


class MeterEvent(Base):
    __tablename__ = "meter_events"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(32), nullable=False)  # replacement, reset
    event_date = Column(Date, nullable=False)
    old_index_end = Column(Numeric(14, 3), nullable=False)
    new_index_start = Column(Numeric(14, 3), default=Decimal("0.000"), nullable=False)
    note = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)

    meter = relationship("Meter", back_populates="events")


class TariffVersion(Base):
    __tablename__ = "tariff_versions"

    id = Column(Integer, primary_key=True, index=True)
    meter_type = Column(String(32), nullable=False, index=True)  # electricity, gas, water, sonelgaz_joint
    valid_from = Column(Date, nullable=False, index=True)
    parameters = Column(JSON, nullable=False)  # JSON structuré contenant paliers, parts fixes, taxes
    source = Column(String(128), default="facture", nullable=False)  # facture, decret, manuel
    note = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class BillingCycle(Base):
    __tablename__ = "billing_cycles"

    id = Column(Integer, primary_key=True, index=True)
    cycle_code = Column(String(32), nullable=False)  # Ex: "2026-Q2"
    energy_group = Column(String(32), nullable=False)  # sonelgaz, water
    quarter = Column(Integer, nullable=False)  # 1, 2, 3, 4
    year = Column(Integer, nullable=False)  # 2025, 2026
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)

    invoices = relationship("Invoice", back_populates="billing_cycle")

    __table_args__ = (
        UniqueConstraint("energy_group", "cycle_code", name="uq_cycle_energy_code"),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    billing_cycle_id = Column(Integer, ForeignKey("billing_cycles.id", ondelete="SET NULL"), nullable=True)
    energy_group = Column(String(32), nullable=False, index=True)  # sonelgaz, water
    cycle_code = Column(String(32), nullable=False)  # Ex: "2026-Q2"
    invoice_number = Column(String(64), nullable=True)
    invoice_date = Column(Date, nullable=True)
    
    # Consommations réelles facturées
    electricity_billed_kwh = Column(Numeric(14, 2), nullable=True)
    gas_billed_th = Column(Numeric(14, 2), nullable=True)
    water_billed_m3 = Column(Numeric(14, 2), nullable=True)

    # Montants
    actual_amount = Column(Numeric(14, 2), nullable=False)  # Montant réel TTC de la facture
    estimated_amount = Column(Numeric(14, 2), nullable=True)  # Dernière estimation de l'app
    variance_amount = Column(Numeric(14, 2), nullable=True)  # actual - estimated
    variance_pct = Column(Numeric(6, 2), nullable=True)  # en %
    
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)

    billing_cycle = relationship("BillingCycle", back_populates="invoices")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(256), nullable=True)
