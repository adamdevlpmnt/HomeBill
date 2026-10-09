import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==================== AUTH ====================
class LoginRequest(BaseModel):
    password: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    app_name: str
    currency_code: str
    currency_symbol: str


# ==================== METERS ====================
class MeterBase(BaseModel):
    meter_type: str
    name: str
    meter_number: Optional[str] = None
    unit: str
    is_active: bool = True


class MeterCreate(MeterBase):
    pass


class MeterResponse(MeterBase):
    id: int
    last_reading_date: Optional[datetime.date] = None
    last_index_value: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)


# ==================== READINGS ====================
class ReadingBase(BaseModel):
    meter_id: int
    read_at: datetime.date
    index_value: Decimal = Field(..., ge=0)
    note: Optional[str] = None


class ReadingCreate(ReadingBase):
    pass


class ReadingUpdate(BaseModel):
    index_value: Optional[Decimal] = Field(None, ge=0)
    read_at: Optional[datetime.date] = None
    note: Optional[str] = None


class ReadingResponse(ReadingBase):
    id: int
    created_at: datetime.datetime
    meter_type: Optional[str] = None
    consumption_since_previous: Optional[Decimal] = None
    days_since_previous: Optional[int] = None
    daily_rate: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)


class BulkReadingItem(BaseModel):
    meter_id: int
    index_value: Decimal = Field(..., ge=0)


class BulkReadingCreate(BaseModel):
    read_at: datetime.date
    readings: List[BulkReadingItem]
    note: Optional[str] = None


class ReadingPreviewRequest(BaseModel):
    meter_id: int
    read_at: datetime.date
    index_value: Decimal


class ReadingPreviewResponse(BaseModel):
    meter_id: int
    meter_type: str
    unit: str
    previous_index: Optional[Decimal] = None
    previous_read_at: Optional[datetime.date] = None
    consumption: Decimal
    days_count: int
    daily_rate: Decimal
    estimated_incremental_cost: Decimal
    is_anomaly: bool = False
    warning_message: Optional[str] = None


# ==================== METER EVENTS ====================
class MeterEventBase(BaseModel):
    meter_id: int
    event_type: str  # replacement, reset
    event_date: datetime.date
    old_index_end: Decimal
    new_index_start: Decimal = Decimal("0.000")
    note: Optional[str] = None


class MeterEventCreate(MeterEventBase):
    pass


class MeterEventResponse(MeterEventBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# ==================== TARIFFS ====================
class TariffVersionBase(BaseModel):
    meter_type: str
    valid_from: datetime.date
    parameters: Dict[str, Any]
    source: str = "facture"
    note: Optional[str] = None


class TariffVersionCreate(TariffVersionBase):
    pass


class TariffVersionResponse(TariffVersionBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# ==================== BILLING CYCLES ====================
class BillingCycleBase(BaseModel):
    cycle_code: str
    energy_group: str  # sonelgaz, water
    quarter: int
    year: int
    start_date: datetime.date
    end_date: datetime.date
    is_closed: bool = False


class BillingCycleCreate(BillingCycleBase):
    pass


class BillingCycleResponse(BillingCycleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==================== INVOICES ====================
class InvoiceBase(BaseModel):
    energy_group: str  # sonelgaz, water
    cycle_code: str
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime.date] = None
    electricity_billed_kwh: Optional[Decimal] = None
    gas_billed_th: Optional[Decimal] = None
    water_billed_m3: Optional[Decimal] = None
    actual_amount: Decimal
    estimated_amount: Optional[Decimal] = None
    note: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceResponse(InvoiceBase):
    id: int
    billing_cycle_id: Optional[int] = None
    variance_amount: Optional[Decimal] = None
    variance_pct: Optional[Decimal] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class SettingsDict(BaseModel):
    budget_electricity_quarterly: Decimal = Decimal("3500.00")
    budget_gas_quarterly: Decimal = Decimal("3000.00")
    budget_sonelgaz_quarterly: Decimal = Decimal("7000.00")
    budget_water_quarterly: Decimal = Decimal("600.00")
    reading_day_of_week: int = 4  # 4 = Vendredi (0=Lundi)
    theme: str = "auto"
    pcs_factor_gas: Decimal = Decimal("9.7")

    # Repères dernière facture reçue pour calcul de delta exact de la prochaine facture
    last_invoice_date_sonelgaz: datetime.date = datetime.date(2026, 6, 16)
    last_invoice_index_electricity: Decimal = Decimal("7331.000")
    last_invoice_index_gas: Decimal = Decimal("5611.000")
    next_read_date_sonelgaz: datetime.date = datetime.date(2026, 9, 16)
    next_cycle_code_sonelgaz: str = "2026-Q3"

    last_invoice_date_water: datetime.date = datetime.date(2025, 4, 9)
    last_invoice_index_water: Decimal = Decimal("120.000")
    next_read_date_water: datetime.date = datetime.date(2025, 7, 9)
    next_cycle_code_water: str = "2025-Q3"


# ==================== ANALYTICS & BILLING ESTIMATES ====================
class BracketDetail(BaseModel):
    bracket_index: int
    bracket_name: str
    consumed_qty: Decimal
    max_qty: Optional[Decimal] = None
    remaining_in_bracket: Optional[Decimal] = None
    unit_price: Decimal
    cost_ht: Decimal
    vat_rate: Decimal


class EnergyQuarterForecast(BaseModel):
    meter_type: str
    name: str
    unit: str
    current_cycle_consumption: Decimal
    projected_cycle_consumption: Decimal
    daily_rate_recent: Decimal
    brackets: List[BracketDetail]
    current_bracket_index: int
    cost_ht_9: Decimal
    cost_ht_19: Decimal
    total_cost_ht: Decimal


class QuarterForecastSummary(BaseModel):
    cycle_code: str
    start_date: datetime.date
    end_date: datetime.date
    days_elapsed: int
    total_days: int
    progress_pct: Decimal
    confidence_index: int  # 0 to 100
    readings_count: int

    # Sonelgaz (Électricité + Gaz conjoint)
    sonelgaz_elec_forecast: EnergyQuarterForecast
    sonelgaz_gas_forecast: EnergyQuarterForecast
    sonelgaz_fixed_fee_ht: Decimal
    sonelgaz_vat_9: Decimal
    sonelgaz_vat_19: Decimal
    sonelgaz_total_vat: Decimal
    sonelgaz_droit_fixe: Decimal
    sonelgaz_taxe_habitation: Decimal
    sonelgaz_net_ttc_low: Decimal
    sonelgaz_net_ttc_central: Decimal
    sonelgaz_net_ttc_high: Decimal
    sonelgaz_budget_target: Decimal
    sonelgaz_target_variance: Decimal

    # Eau (SEAAL)
    water_forecast: EnergyQuarterForecast
    water_sanitation_forecast: EnergyQuarterForecast
    water_fixed_fee_potable: Decimal
    water_fixed_fee_sanitation: Decimal
    water_vat: Decimal
    water_mf_fee: Decimal
    water_wqf_fee: Decimal
    water_wsf_fee: Decimal
    water_total_taxes: Decimal
    water_net_ttc_low: Decimal
    water_net_ttc_central: Decimal
    water_net_ttc_high: Decimal
    water_budget_target: Decimal
    water_target_variance: Decimal

    # Total Global
    total_net_ttc_low: Decimal
    total_net_ttc_central: Decimal
    total_net_ttc_high: Decimal
    total_budget_target: Decimal


class TimeSeriesDataPoint(BaseModel):
    period_key: str  # ex: "2026-W24", "2026-06", "2026-Q2"
    label: str
    start_date: datetime.date
    end_date: datetime.date
    electricity_kwh: Decimal
    gas_th: Decimal
    gas_m3: Decimal
    water_m3: Decimal
    electricity_cost: Decimal
    gas_cost: Decimal
    water_cost: Decimal
    sonelgaz_total_cost: Decimal
    total_cost: Decimal
    daily_rate_elec: Decimal
    daily_rate_gas: Decimal
    daily_rate_water: Decimal
