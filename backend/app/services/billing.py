import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Any, List, Optional


def round_cur(val: Decimal) -> Decimal:
    """Arrondi au centime (2 décimales) selon la norme commerciale."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def load_default_tariffs() -> Dict[str, Any]:
    """Charge le fichier de tarifs par défaut versionné."""
    path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "tarifs.json"
    if not path.exists():
        # Fallback si exécuté depuis un autre chemin
        path = Path("config/tarifs.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_bracket_breakdown(
    quantity: Decimal,
    brackets_config: List[Dict[str, Any]],
    prorate_factor: Decimal = Decimal("1.0"),
) -> Dict[str, Any]:
    """
    Ventile une quantité consommée dans les paliers successifs.
    Prend en compte un facteur de proratisation éventuel des bornes.
    """
    remaining = max(Decimal("0.00"), quantity)
    details = []
    total_ht_9 = Decimal("0.00")
    total_ht_19 = Decimal("0.00")
    total_ht = Decimal("0.00")
    current_bracket_index = 1

    for b in brackets_config:
        idx = int(b["index"])
        min_q = Decimal(str(b["min_qty"])) * prorate_factor
        max_q = (
            Decimal(str(b["max_qty"])) * prorate_factor
            if b.get("max_qty") is not None
            else None
        )
        capacity = (max_q - min_q) if max_q is not None else remaining

        if remaining <= Decimal("0.00"):
            consumed_in_bracket = Decimal("0.00")
        else:
            consumed_in_bracket = min(remaining, capacity)
            remaining -= consumed_in_bracket
            current_bracket_index = idx

        unit_p = Decimal(str(b["unit_price"]))
        cost_ht = round_cur(consumed_in_bracket * unit_p)
        vat_rate = Decimal(str(b.get("vat_rate", "0.09")))

        if vat_rate == Decimal("0.09"):
            total_ht_9 += cost_ht
        elif vat_rate == Decimal("0.19"):
            total_ht_19 += cost_ht

        total_ht += cost_ht
        remaining_in_bracket = (
            (capacity - consumed_in_bracket) if max_q is not None else None
        )

        details.append(
            {
                "bracket_index": idx,
                "bracket_name": b.get("name", f"Tranche {idx}"),
                "consumed_qty": round_cur(consumed_in_bracket),
                "max_qty": round_cur(max_q) if max_q is not None else None,
                "remaining_in_bracket": (
                    round_cur(remaining_in_bracket)
                    if remaining_in_bracket is not None
                    else None
                ),
                "unit_price": unit_p,
                "cost_ht": cost_ht,
                "vat_rate": vat_rate,
            }
        )

    return {
        "details": details,
        "current_bracket_index": current_bracket_index,
        "total_ht_9": total_ht_9,
        "total_ht_19": total_ht_19,
        "total_ht": total_ht,
    }


def calculate_electricity_bill(
    consumption_kwh: Decimal,
    tariff_cfg: Dict[str, Any],
    prorate_factor: Decimal = Decimal("1.0"),
) -> Dict[str, Any]:
    """Calcul de la part électricité selon les tranches 54M."""
    elec_cfg = tariff_cfg.get("electricity", {})
    breakdown = calculate_bracket_breakdown(
        consumption_kwh, elec_cfg.get("brackets", []), prorate_factor
    )
    return {
        "consumption_kwh": consumption_kwh,
        "breakdown": breakdown["details"],
        "current_bracket_index": breakdown["current_bracket_index"],
        "cost_ht_9": breakdown["total_ht_9"],
        "cost_ht_19": breakdown["total_ht_19"],
        "total_ht": breakdown["total_ht"],
    }


def calculate_gas_bill(
    consumption_m3: Decimal,
    tariff_cfg: Dict[str, Any],
    prorate_factor: Decimal = Decimal("1.0"),
) -> Dict[str, Any]:
    """Calcul de la part gaz avec conversion en thermies selon les tranches 23M."""
    gas_cfg = tariff_cfg.get("gas", {})
    pcs_factor = Decimal(str(gas_cfg.get("pcs_factor", "9.7")))
    consumption_th = round_cur(consumption_m3 * pcs_factor)

    breakdown = calculate_bracket_breakdown(
        consumption_th, gas_cfg.get("brackets", []), prorate_factor
    )
    return {
        "consumption_m3": consumption_m3,
        "pcs_factor": pcs_factor,
        "consumption_th": consumption_th,
        "breakdown": breakdown["details"],
        "current_bracket_index": breakdown["current_bracket_index"],
        "cost_ht_9": breakdown["total_ht_9"],
        "cost_ht_19": breakdown["total_ht_19"],
        "total_ht": breakdown["total_ht"],
    }


def calculate_sonelgaz_joint_bill(
    elec_kwh: Decimal,
    gas_m3: Decimal,
    tariff_cfg: Dict[str, Any],
    include_duty_stamp: bool = False,
    prorate_factor: Decimal = Decimal("1.0"),
) -> Dict[str, Any]:
    """
    Calcule la facture conjointe Sonelgaz Électricité + Gaz
    avec regroupement des parts fixes et de la TVA.
    """
    elec_res = calculate_electricity_bill(elec_kwh, tariff_cfg, prorate_factor)
    gas_res = calculate_gas_bill(gas_m3, tariff_cfg, prorate_factor)

    joint_cfg = tariff_cfg.get("energy_joint_sonelgaz", {})
    fixed_fee_ht = Decimal(str(joint_cfg.get("fixed_fee_total", "164.16")))
    fixed_fee_vat_rate = Decimal(str(joint_cfg.get("fixed_fee_vat_rate", "0.09")))

    total_ht = elec_res["total_ht"] + gas_res["total_ht"] + fixed_fee_ht

    # Assiette TVA 9% : Élec T1+T2 + Gaz T1+T2 + Redevance fixe
    base_vat_9 = elec_res["cost_ht_9"] + gas_res["cost_ht_9"] + fixed_fee_ht
    vat_9 = round_cur(base_vat_9 * fixed_fee_vat_rate)

    # Assiette TVA 19% : Élec T3+T4 + Gaz T3+T4
    base_vat_19 = elec_res["cost_ht_19"] + gas_res["cost_ht_19"]
    vat_19 = round_cur(base_vat_19 * Decimal("0.19"))

    total_vat = vat_9 + vat_19

    droit_fixe = Decimal(str(joint_cfg.get("fixed_duty_total", "200.00")))
    taxe_habitation = Decimal(str(joint_cfg.get("housing_tax_total", "200.00")))

    net_ttc = total_ht + total_vat + droit_fixe + taxe_habitation

    duty_stamp = Decimal("0.00")
    if include_duty_stamp:
        duty_stamp = Decimal(str(joint_cfg.get("cash_duty_stamp", "70.00")))

    total_due = net_ttc + duty_stamp

    return {
        "electricity": elec_res,
        "gas": gas_res,
        "fixed_fee_ht": fixed_fee_ht,
        "total_ht": total_ht,
        "base_vat_9": base_vat_9,
        "vat_9": vat_9,
        "base_vat_19": base_vat_19,
        "vat_19": vat_19,
        "total_vat": total_vat,
        "droit_fixe": droit_fixe,
        "taxe_habitation": taxe_habitation,
        "net_ttc": net_ttc,
        "duty_stamp": duty_stamp,
        "total_due": total_due,
    }


def calculate_water_bill(
    consumption_m3: Decimal,
    tariff_cfg: Dict[str, Any],
    include_duty_stamp: bool = False,
    prorate_factor: Decimal = Decimal("1.0"),
) -> Dict[str, Any]:
    """
    Calcule la facture SEAAL Eau potable + Assainissement + Taxes.
    """
    w_cfg = tariff_cfg.get("water", {})

    # 1. Eau potable (AEP)
    pot_cfg = w_cfg.get("potable_water", {})
    pot_fixed_ht = Decimal(str(pot_cfg.get("fixed_fee_trimestrial", "240.00")))
    pot_breakdown = calculate_bracket_breakdown(
        consumption_m3, pot_cfg.get("brackets", []), prorate_factor
    )
    pot_vol_ht = pot_breakdown["total_ht"]
    pot_subtotal_ht = pot_fixed_ht + pot_vol_ht

    # 2. Assainissement
    san_cfg = w_cfg.get("sanitation", {})
    san_fixed_ht = Decimal(str(san_cfg.get("fixed_fee_trimestrial", "60.00")))
    san_breakdown = calculate_bracket_breakdown(
        consumption_m3, san_cfg.get("brackets", []), prorate_factor
    )
    san_vol_ht = san_breakdown["total_ht"]
    san_subtotal_ht = san_fixed_ht + san_vol_ht

    total_ht = pot_subtotal_ht + san_subtotal_ht

    # 3. TVA 9% par sous-total
    vat_pot = round_cur(pot_subtotal_ht * Decimal(str(pot_cfg.get("vat_rate", "0.09"))))
    vat_san = round_cur(san_subtotal_ht * Decimal(str(san_cfg.get("vat_rate", "0.09"))))
    total_vat = vat_pot + vat_san

    # 4. Redevances spécifiques
    # M.F (Redevance d'assainissement / gestion au m3)
    mf_rate = Decimal("3.00")
    for f in w_cfg.get("fees_and_taxes", []):
        if f.get("code") == "MF":
            mf_rate = Decimal(str(f.get("rate_per_unit", "3.00")))
    mf_fee = round_cur(consumption_m3 * mf_rate)

    # W.Q.F (Redevance qualité) = 4% de la consommation d'eau variable
    wqf_rate = Decimal("0.04")
    for f in w_cfg.get("fees_and_taxes", []):
        if f.get("code") == "WQF":
            wqf_rate = Decimal(str(f.get("rate_percentage", "0.04")))
    wqf_fee = round_cur(pot_vol_ht * wqf_rate)

    # W.S.F (Redevance économie) = 4% de la consommation d'eau variable
    wsf_rate = Decimal("0.04")
    for f in w_cfg.get("fees_and_taxes", []):
        if f.get("code") == "WSF":
            wsf_rate = Decimal(str(f.get("rate_percentage", "0.04")))
    wsf_fee = round_cur(pot_vol_ht * wsf_rate)

    total_taxes = total_vat + mf_fee + wqf_fee + wsf_fee
    net_ttc = total_ht + total_taxes

    duty_stamp = Decimal("0.00")
    if include_duty_stamp:
        duty_stamp = Decimal(str(w_cfg.get("cash_duty_stamp", "6.00")))

    total_due = net_ttc + duty_stamp

    return {
        "consumption_m3": consumption_m3,
        "potable_water": {
            "fixed_ht": pot_fixed_ht,
            "consumption_ht": pot_vol_ht,
            "subtotal_ht": pot_subtotal_ht,
            "vat": vat_pot,
            "breakdown": pot_breakdown["details"],
            "current_bracket_index": pot_breakdown["current_bracket_index"],
        },
        "sanitation": {
            "fixed_ht": san_fixed_ht,
            "consumption_ht": san_vol_ht,
            "subtotal_ht": san_subtotal_ht,
            "vat": vat_san,
            "breakdown": san_breakdown["details"],
            "current_bracket_index": san_breakdown["current_bracket_index"],
        },
        "total_ht": total_ht,
        "total_vat": total_vat,
        "mf_fee": mf_fee,
        "wqf_fee": wqf_fee,
        "wsf_fee": wsf_fee,
        "total_taxes": total_taxes,
        "net_ttc": net_ttc,
        "duty_stamp": duty_stamp,
        "total_due": total_due,
    }
