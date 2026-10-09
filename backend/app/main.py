import os
import datetime
from pathlib import Path
from decimal import Decimal
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Meter, Reading, BillingCycle, Setting, Invoice, TariffVersion
from app.services.billing import load_default_tariffs

# Importer les routeurs
from app.routers import (
    auth,
    meters,
    readings,
    events,
    tariffs,
    cycles,
    invoices,
    analytics,
    billing,
    settings as settings_router,
)


def init_db_data(custom_engine=None, custom_session_cls=None):
    """Initialise les tables et les données par défaut au premier démarrage."""
    tgt_engine = custom_engine or engine
    session_cls = custom_session_cls or SessionLocal
    Base.metadata.create_all(bind=tgt_engine)
    db = session_cls()
    try:
        # 1. Compteurs par défaut
        if db.query(Meter).count() == 0:
            m_elec = Meter(
                meter_type="electricity",
                name="Électricité (Sonelgaz 54M)",
                meter_number="022150601804",
                unit="kWh",
                is_active=True,
            )
            m_gas = Meter(
                meter_type="gas",
                name="Gaz Naturel (Sonelgaz 23M)",
                meter_number="230332101",
                unit="m3",
                is_active=True,
            )
            m_water = Meter(
                meter_type="water",
                name="Eau & Assainissement (SEAAL)",
                meter_number="122PA027035",
                unit="m3",
                is_active=True,
            )
            db.add_all([m_elec, m_gas, m_water])
            db.commit()

        # 2. Cycles de facturation par défaut
        if db.query(BillingCycle).count() == 0:
            # Cycle Sonelgaz T2 2026 (01/04 au 30/06)
            c_sonelgaz = BillingCycle(
                cycle_code="2026-Q2",
                energy_group="sonelgaz",
                quarter=2,
                year=2026,
                start_date=datetime.date(2026, 4, 1),
                end_date=datetime.date(2026, 6, 30),
            )
            # Cycle SEAAL T2 2025
            c_seaal = BillingCycle(
                cycle_code="2025-Q2",
                energy_group="water",
                quarter=2,
                year=2025,
                start_date=datetime.date(2025, 1, 13),
                end_date=datetime.date(2025, 4, 9),
            )
            db.add_all([c_sonelgaz, c_seaal])
            db.commit()

        # 3. Paramètres initiaux
        if db.query(Setting).count() == 0:
            initial_settings = [
                Setting(key="budget_electricity_quarterly", value="3500.00"),
                Setting(key="budget_gas_quarterly", value="3000.00"),
                Setting(key="budget_sonelgaz_quarterly", value="7000.00"),
                Setting(key="budget_water_quarterly", value="600.00"),
                Setting(key="reading_day_of_week", value="4"),  # Vendredi
                Setting(key="theme", value="auto"),
                Setting(key="pcs_factor_gas", value="9.7"),
                # Repères dernière facture Sonelgaz
                Setting(key="last_invoice_date_sonelgaz", value="2026-06-16"),
                Setting(key="last_invoice_index_electricity", value="7331.000"),
                Setting(key="last_invoice_index_gas", value="5611.000"),
                Setting(key="next_read_date_sonelgaz", value="2026-09-16"),
                Setting(key="next_cycle_code_sonelgaz", value="2026-Q3"),
                # Repères dernière facture Eau
                Setting(key="last_invoice_date_water", value="2025-04-09"),
                Setting(key="last_invoice_index_water", value="120.000"),
                Setting(key="next_read_date_water", value="2025-07-09"),
                Setting(key="next_cycle_code_water", value="2025-Q3"),
            ]
            db.add_all(initial_settings)
            db.commit()

        # 4. Tarifs par défaut
        if db.query(TariffVersion).count() == 0:
            tariffs_data = load_default_tariffs()
            tv = TariffVersion(
                meter_type="all",
                valid_from=datetime.date(2025, 1, 1),
                parameters=tariffs_data,
                source="factures_analysees",
                note="Tarifs extraits des factures réelles Sonelgaz et SEAAL",
            )
            db.add(tv)
            db.commit()

        # 5. Injection des points historiques réels issus des factures si la table est vide
        if db.query(Reading).count() == 0:
            m_elec = db.query(Meter).filter(Meter.meter_type == "electricity").first()
            m_gas = db.query(Meter).filter(Meter.meter_type == "gas").first()
            m_water = db.query(Meter).filter(Meter.meter_type == "water").first()

            historical_readings = [
                # Électricité : Ancien index (16-03-2026) et Nouvel index (16-06-2026)
                Reading(meter_id=m_elec.id, read_at=datetime.date(2026, 3, 16), index_value=Decimal("6639.000"), note="Index précédent facture T2"),
                Reading(meter_id=m_elec.id, read_at=datetime.date(2026, 6, 16), index_value=Decimal("7331.000"), note="Index relevé facture T2"),
                # Gaz : Ancien index (16-03-2026) et Nouvel index (16-06-2026)
                Reading(meter_id=m_gas.id, read_at=datetime.date(2026, 3, 16), index_value=Decimal("4850.000"), note="Index précédent facture T2"),
                Reading(meter_id=m_gas.id, read_at=datetime.date(2026, 6, 16), index_value=Decimal("5611.000"), note="Index relevé facture T2"),
                # Eau : Ancien index (13-01-2025) et Nouvel index (09-04-2025)
                Reading(meter_id=m_water.id, read_at=datetime.date(2025, 1, 13), index_value=Decimal("103.000"), note="Index précédent facture T2"),
                Reading(meter_id=m_water.id, read_at=datetime.date(2025, 4, 9), index_value=Decimal("120.000"), note="Index relevé facture T2"),
            ]
            db.add_all(historical_readings)

            # Factures réelles enregistrées
            historical_invoices = [
                Invoice(
                    energy_group="sonelgaz",
                    cycle_code="2026-Q2",
                    invoice_number="571260615440",
                    invoice_date=datetime.date(2026, 6, 16),
                    electricity_billed_kwh=Decimal("692.00"),
                    gas_billed_th=Decimal("7381.70"),
                    actual_amount=Decimal("6952.49"),
                    estimated_amount=Decimal("6952.49"),
                    variance_amount=Decimal("0.00"),
                    variance_pct=Decimal("0.00"),
                    note="Facture Sonelgaz T2 2026",
                ),
                Invoice(
                    energy_group="water",
                    cycle_code="2025-Q2",
                    invoice_number="F055154807",
                    invoice_date=datetime.date(2025, 4, 13),
                    water_billed_m3=Decimal("17.00"),
                    actual_amount=Decimal("546.85"),
                    estimated_amount=Decimal("546.85"),
                    variance_amount=Decimal("0.00"),
                    variance_pct=Decimal("0.00"),
                    note="Facture SEAAL T2 2025",
                ),
            ]
            db.add_all(historical_invoices)
            db.commit()

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_data()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="API de suivi de consommation d'électricité, de gaz et d'eau avec estimation de factures",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS pour le développement Vite (port 5173 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:5173", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routeurs d'API
app.include_router(auth.router)
app.include_router(meters.router)
app.include_router(readings.router)
app.include_router(events.router)
app.include_router(tariffs.router)
app.include_router(cycles.router)
app.include_router(invoices.router)
app.include_router(analytics.router)
app.include_router(billing.router)
app.include_router(settings_router.router)


@app.get("/health")
def healthcheck():
    """Healthcheck pour Docker et monitoring."""
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}


# Servir le frontend statique si le dossier dist existe
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
