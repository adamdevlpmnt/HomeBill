import datetime
from decimal import Decimal
import pytest
from app.config import settings


def test_auth_flow(client):
    """Teste la connexion, la vérification du statut et la déconnexion."""
    # 1. Vérification état initial
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    assert res.json()["authenticated"] is False

    # 2. Login avec mauvais mot de passe
    res = client.post("/api/auth/login", json={"password": "wrongpassword"})
    assert res.status_code == 401

    # 3. Login avec bon mot de passe
    res = client.post("/api/auth/login", json={"password": settings.APP_PASSWORD})
    assert res.status_code == 200
    assert "token" in res.json()

    # 4. Statut authentifié (cookie de session)
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    assert res.json()["authenticated"] is True

    # 5. Logout
    res = client.post("/api/auth/logout")
    assert res.status_code == 200


def test_get_meters_and_initial_data(client):
    """Teste la récupération des 3 compteurs créés au démarrage."""
    client.post("/api/auth/login", json={"password": settings.APP_PASSWORD})
    res = client.get("/api/meters")
    assert res.status_code == 200
    meters = res.json()
    assert len(meters) == 3
    types = [m["meter_type"] for m in meters]
    assert "electricity" in types
    assert "gas" in types
    assert "water" in types


def test_preview_and_bulk_reading(client):
    """Teste la prévisualisation instantanée et la saisie groupée."""
    client.post("/api/auth/login", json={"password": settings.APP_PASSWORD})
    meters = client.get("/api/meters").json()
    m_elec = next(m for m in meters if m["meter_type"] == "electricity")

    # Preview
    preview_res = client.post(
        "/api/readings/preview",
        json={
            "meter_id": m_elec["id"],
            "read_at": "2026-06-23",
            "index_value": "7390.000",
        },
    )
    assert preview_res.status_code == 200
    p_data = preview_res.json()
    # Ancien index = 7331.000 -> consommation = 59.00
    assert Decimal(str(p_data["consumption"])) == Decimal("59.00")
    assert p_data["days_count"] == 7

    # Bulk create
    m_gas = next(m for m in meters if m["meter_type"] == "gas")
    m_water = next(m for m in meters if m["meter_type"] == "water")

    bulk_res = client.post(
        "/api/readings/bulk",
        json={
            "read_at": "2026-06-23",
            "readings": [
                {"meter_id": m_elec["id"], "index_value": "7390.000"},
                {"meter_id": m_gas["id"], "index_value": "5620.000"},
                {"meter_id": m_water["id"], "index_value": "122.000"},
            ],
            "note": "Relevé du vendredi",
        },
    )
    assert bulk_res.status_code == 200
    readings = bulk_res.json()
    assert len(readings) == 3


def test_billing_estimate_endpoint(client):
    """Teste l'endpoint de projection de la facture du trimestre en cours."""
    client.post("/api/auth/login", json={"password": settings.APP_PASSWORD})
    res = client.get("/api/billing/estimate")
    assert res.status_code == 200
    data = res.json()
    assert "sonelgaz" in data
    assert "water" in data
    assert "totals" in data
    assert Decimal(str(data["totals"]["net_ttc_central"])) > 0


def test_analytics_timeseries_endpoint(client):
    """Teste l'endpoint des séries temporelles."""
    client.post("/api/auth/login", json={"password": settings.APP_PASSWORD})
    res = client.get("/api/analytics/timeseries?period=week")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_baseline_anchors_and_forecast(client):
    """Teste le calcul de delta exact à partir des repères de la dernière facture."""
    client.post("/api/auth/login", json={"password": settings.APP_PASSWORD})

    # 1. Vérifier la récupération des paramètres avec les repères de facture
    res = client.get("/api/settings")
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["last_invoice_date_sonelgaz"] == "2026-06-16"
    assert Decimal(str(cfg["last_invoice_index_electricity"])) == Decimal("7331.000")
    assert Decimal(str(cfg["last_invoice_index_gas"])) == Decimal("5611.000")
    assert cfg["next_read_date_sonelgaz"] == "2026-09-16"

    # 2. Saisir la relève simulée du 2026-09-16 (Elec: 9414, Gaz: 5648)
    meters = client.get("/api/meters").json()
    m_elec = next(m for m in meters if m["meter_type"] == "electricity")
    m_gas = next(m for m in meters if m["meter_type"] == "gas")

    client.post(
        "/api/readings/bulk",
        json={
            "read_at": "2026-09-16",
            "readings": [
                {"meter_id": m_elec["id"], "index_value": "9414.000"},
                {"meter_id": m_gas["id"], "index_value": "5648.000"},
            ],
        },
    )

    # 3. Vérifier l'estimation de la facture Sonelgaz
    # Delta Élec = 9414 - 7331 = 2083 kWh
    # Delta Gaz = 5648 - 5611 = 37 m³
    # Net TTC attendu = 12 813.63 DA
    est_res = client.get("/api/billing/estimate")
    assert est_res.status_code == 200
    est = est_res.json()
    assert Decimal(str(est["sonelgaz"]["electricity_realized"])) == Decimal("2083")
    assert Decimal(str(est["sonelgaz"]["gas_realized_m3"])) == Decimal("37")
    assert Decimal(str(est["sonelgaz"]["net_ttc_central"])) == Decimal("12813.63")

