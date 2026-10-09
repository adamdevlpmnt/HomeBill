from decimal import Decimal
import pytest
from app.services.billing import (
    load_default_tariffs,
    calculate_electricity_bill,
    calculate_gas_bill,
    calculate_sonelgaz_joint_bill,
    calculate_water_bill,
    calculate_bracket_breakdown,
)


@pytest.fixture
def tariffs():
    return load_default_tariffs()


def test_electricity_bracket_breakdown_matches_invoice(tariffs):
    """Vérifie que la consommation de 692 kWh reproduit exactement la facture Sonelgaz."""
    res = calculate_electricity_bill(Decimal("692.00"), tariffs)
    assert res["cost_ht_9"] == Decimal("744.70")
    assert res["cost_ht_19"] == Decimal("2126.90")
    assert res["total_ht"] == Decimal("2871.60")
    assert res["current_bracket_index"] == 3


def test_gas_bracket_breakdown_matches_invoice(tariffs):
    """Vérifie que 761 m3 de gaz (7381.70 Th) reproduisent exactement la facture Sonelgaz."""
    res = calculate_gas_bill(Decimal("761.00"), tariffs)
    assert res["consumption_th"] == Decimal("7381.70")
    assert res["cost_ht_9"] == Decimal("635.42")
    assert res["cost_ht_19"] == Decimal("1964.88")
    assert res["total_ht"] == Decimal("2600.30")
    assert res["current_bracket_index"] == 3


def test_sonelgaz_joint_bill_exact_centime(tariffs):
    """Vérifie la facture conjointe Sonelgaz au centime près."""
    res = calculate_sonelgaz_joint_bill(
        Decimal("692.00"), Decimal("761.00"), tariffs, include_duty_stamp=False
    )
    assert res["total_ht"] == Decimal("5636.06")
    assert res["vat_9"] == Decimal("138.99")
    assert res["vat_19"] == Decimal("777.44")
    assert res["total_vat"] == Decimal("916.43")
    assert res["droit_fixe"] == Decimal("200.00")
    assert res["taxe_habitation"] == Decimal("200.00")
    assert res["net_ttc"] == Decimal("6952.49")

    # Avec timbre espèces
    res_cash = calculate_sonelgaz_joint_bill(
        Decimal("692.00"), Decimal("761.00"), tariffs, include_duty_stamp=True
    )
    assert res_cash["duty_stamp"] == Decimal("70.00")
    assert res_cash["total_due"] == Decimal("7022.49")


def test_water_seaal_bill_exact_centime(tariffs):
    """Vérifie la facture SEAAL de 17 m3 au centime près."""
    res = calculate_water_bill(Decimal("17.00"), tariffs, include_duty_stamp=False)
    assert res["potable_water"]["subtotal_ht"] == Decimal("347.10")
    assert res["sanitation"]["subtotal_ht"] == Decimal("99.95")
    assert res["total_ht"] == Decimal("447.05")
    assert res["total_vat"] == Decimal("40.24")
    assert res["mf_fee"] == Decimal("51.00")
    assert res["wqf_fee"] == Decimal("4.28")
    assert res["wsf_fee"] == Decimal("4.28")
    assert res["total_taxes"] == Decimal("99.80")
    assert res["net_ttc"] == Decimal("546.85")

    # Avec timbre espèces
    res_cash = calculate_water_bill(Decimal("17.00"), tariffs, include_duty_stamp=True)
    assert res_cash["duty_stamp"] == Decimal("6.00")
    assert res_cash["total_due"] == Decimal("552.85")


def test_edge_case_zero_consumption(tariffs):
    """Cas limite : consommation nulle = seules les parts fixes et taxes fixes s'appliquent."""
    res_sg = calculate_sonelgaz_joint_bill(
        Decimal("0.00"), Decimal("0.00"), tariffs, include_duty_stamp=False
    )
    assert res_sg["total_ht"] == Decimal("164.16")
    assert res_sg["total_vat"] == Decimal("14.77")  # 164.16 * 0.09 = 14.7744 -> 14.77
    assert res_sg["net_ttc"] == Decimal("164.16") + Decimal("14.77") + Decimal("200.00") + Decimal("200.00")

    res_w = calculate_water_bill(Decimal("0.00"), tariffs, include_duty_stamp=False)
    # Eau : part fixe eau 240 + part fixe assainissement 60 = 300 HT
    assert res_w["total_ht"] == Decimal("300.00")
    # TVA 9% : 240 * 0.09 = 21.60, 60 * 0.09 = 5.40 -> total 27.00
    assert res_w["total_vat"] == Decimal("27.00")
    assert res_w["net_ttc"] == Decimal("327.00")
