"""Moteur quantitatif : scénarios de taux, crédit et actions."""

from __future__ import annotations

import math
from typing import Any

from .corpus import load_portfolio, load_scenarios


class QuantEngine:
    def __init__(self, portfolio: dict | None = None, scenarios: list[dict] | None = None):
        self.portfolio = portfolio or load_portfolio()
        self.scenarios = {s["id"]: s for s in (scenarios or load_scenarios())}
        self.positions = self.portfolio["positions"]
        self.nav = float(self.portfolio["nav_eur"])

    # ------------------------------------------------------------------
    def scenario(self, scenario_id: str) -> dict:
        if scenario_id not in self.scenarios:
            raise KeyError(f"Scénario inconnu: {scenario_id}")
        return self.scenarios[scenario_id]

    def _position_impact(self, position: dict, scenario: dict, market_value: float) -> float:
        factor = scenario["factor_id"]
        if factor == "FACTOR-EUR-RATES":
            shock = float(scenario["shock_bps"] or 0.0)
            if position["asset_class"] == "Obligation":
                return -market_value * float(position["modified_duration"]) * shock / 10_000.0
            if position["asset_class"] == "Action":
                return market_value * float(position["rate_beta_pct_per_bp"]) / 100.0 * shock
            return 0.0
        if factor == "FACTOR-CREDIT-SPREAD":
            shock = float(scenario["shock_bps"] or 0.0)
            return float(position.get("credit_dv01_eur", 0.0)) * shock
        if factor == "FACTOR-EQUITY":
            shock_pct = float(scenario["shock_pct"] or 0.0)
            if position["asset_class"] == "Action":
                return market_value * float(position.get("equity_beta", 1.0)) * shock_pct / 100.0
            return 0.0
        return 0.0

    def _driver(self, position: dict, scenario: dict) -> str:
        factor = scenario["factor_id"]
        if factor == "FACTOR-EUR-RATES":
            if position["asset_class"] == "Obligation":
                return f"duration modifiée {position['modified_duration']:.1f}"
            return f"bêta taux {position['rate_beta_pct_per_bp']:+.3f} %/bp"
        if factor == "FACTOR-CREDIT-SPREAD":
            return f"DV01 crédit {position.get('credit_dv01_eur', 0):,.0f} €/bp"
        if factor == "FACTOR-EQUITY":
            return f"bêta actions {position.get('equity_beta', 1.0):.2f}"
        return "—"

    def run_scenario(
        self,
        scenario_id: str,
        bond_reduction_pct: float = 0.0,
        swap_notional_eur: float = 0.0,
    ) -> dict[str, Any]:
        scenario = self.scenario(scenario_id)
        bond_reduction_pct = max(0.0, min(100.0, float(bond_reduction_pct)))
        rows = []
        for position in self.positions:
            market_value = float(position["market_value_eur"])
            if position["asset_class"] == "Obligation" and bond_reduction_pct:
                market_value *= 1.0 - bond_reduction_pct / 100.0
            impact = self._position_impact(position, scenario, market_value)
            rows.append({
                "position_id": position["id"],
                "name": position["name"],
                "asset_class": position["asset_class"],
                "sector_id": position["sector_id"],
                "weight_pct": position["weight_pct"],
                "market_value_eur": round(market_value, 2),
                "impact_eur": round(impact, 2),
                "impact_pct_nav": round(100.0 * impact / self.nav, 4),
                "driver": self._driver(position, scenario),
            })

        hedge_impact = 0.0
        if swap_notional_eur and scenario["factor_id"] == "FACTOR-EUR-RATES":
            # Un swap payeur de taux gagne approximativement 1 bp de notionnel par bp de hausse.
            hedge_impact = float(swap_notional_eur) * float(scenario["shock_bps"] or 0.0) / 10_000.0
            rows.append({
                "position_id": "HEDGE-SWAP",
                "name": "Couverture swap payeur",
                "asset_class": "Dérivé",
                "sector_id": "SEC-CASH",
                "weight_pct": 0.0,
                "market_value_eur": float(swap_notional_eur),
                "impact_eur": round(hedge_impact, 2),
                "impact_pct_nav": round(100.0 * hedge_impact / self.nav, 4),
                "driver": "notionnel du swap",
            })

        impact = sum(row["impact_eur"] for row in rows)
        impact_pct = 100.0 * impact / self.nav
        nav_after = self.nav + impact
        contributors = sorted(rows, key=lambda row: row["impact_eur"])
        limit_checks = self._limit_checks(impact, impact_pct, bond_reduction_pct)
        bond_loss = sum(abs(row["impact_eur"]) for row in rows if row["asset_class"] == "Obligation")
        needed = max(0.0, abs(impact) - abs(float(scenario["limit_loss_pct"])) / 100.0 * self.nav)
        required_reduction = 100.0 * needed / bond_loss if bond_loss > 0 else 0.0
        recommended_reduction = math.ceil((required_reduction + 1.0) * 2) / 2 if required_reduction > 0 else 0.0

        return {
            "scenario": {
                "id": scenario["id"],
                "name": scenario["name"],
                "factor_id": scenario["factor_id"],
                "shock_bps": scenario["shock_bps"],
                "shock_pct": scenario["shock_pct"],
                "description": scenario["description"],
                "limit_loss_pct": scenario["limit_loss_pct"],
                "method": scenario["method"],
            },
            "portfolio": {
                "id": self.portfolio["id"],
                "name": self.portfolio["name"],
                "nav_eur": self.nav,
                "nav_after_eur": round(nav_after, 2),
                "as_of": self.portfolio["as_of"],
            },
            "impact_eur": round(impact, 2),
            "impact_pct_nav": round(impact_pct, 3),
            "nav_after_eur": round(nav_after, 2),
            "hedge_impact_eur": round(hedge_impact, 2),
            "bond_reduction_pct": round(bond_reduction_pct, 2),
            "required_bond_reduction_pct": round(required_reduction, 1),
            "recommended_bond_reduction_pct": recommended_reduction,
            "contributors": contributors,
            "top_contributors": [row for row in contributors if row["impact_eur"] < 0][:6],
            "positive_contributors": [row for row in contributors if row["impact_eur"] > 0][:4],
            "limit_checks": limit_checks,
            "breaches": [check for check in limit_checks if check["status"] == "BREACH"],
            "summary": self._summary(scenario, impact, impact_pct, contributors),
        }

    def _limit_checks(self, impact: float, impact_pct: float, bond_reduction_pct: float) -> list[dict]:
        constraints = self.portfolio["constraints"]
        metrics = self.portfolio["metrics"]
        issuer_weights: dict[str, float] = {}
        sector_weights: dict[str, float] = {}
        for position in self.positions:
            if position["asset_class"] == "Cash":
                continue
            issuer_weights[position["issuer_id"]] = issuer_weights.get(position["issuer_id"], 0.0) + position["weight_pct"]
            sector_weights[position["sector_id"]] = sector_weights.get(position["sector_id"], 0.0) + position["weight_pct"]
        max_issuer = max(issuer_weights.values())
        max_sector = max(sector_weights.values())
        liquidity = sum(p["weight_pct"] for p in self.positions if p["sector_id"] in {"SEC-CASH", "SEC-SOVEREIGN"})

        def check(name, metric, value, limit, unit, direction, control):
            if direction == "max":
                status = "BREACH" if value > limit else ("WATCH" if value >= limit * 0.9 else "OK")
                headroom = limit - value
            else:
                status = "BREACH" if value < limit else ("WATCH" if value <= limit * 1.1 else "OK")
                headroom = value - limit
            return {
                "control": control,
                "name": name,
                "metric": metric,
                "value": round(value, 2),
                "limit": round(limit, 2),
                "unit": unit,
                "direction": direction,
                "status": status,
                "headroom": round(headroom, 2),
            }

        return [
            check("Perte scénario", "scenario_loss_pct", abs(impact_pct), abs(constraints["max_scenario_loss_pct"]), "% NAV", "max", "CTL-SCENARIO-LOSS"),
            check("Concentration émetteur", "max_issuer_pct", max_issuer, constraints["max_issuer_pct"], "% NAV", "max", "CTL-ISSUER-CAP"),
            check("Concentration secteur", "max_sector_pct", max_sector, constraints["max_sector_pct"], "% NAV", "max", "CTL-SECTOR-CAP"),
            check("Liquidité T+1", "liquidity_t1_pct", liquidity, constraints["min_liquidity_t1_pct"], "% NAV", "min", "CTL-LIQUIDITY"),
            check("Duration", "duration_years", metrics["duration_years"], constraints["max_duration_years"], "ans", "max", "CTL-DURATION"),
            check("VaR 99% 1 jour", "var_99_1d_pct", metrics["var_99_1d_pct"], constraints["max_var_99_1d_pct"], "% NAV", "max", "CTL-VAR"),
        ]

    def _summary(self, scenario: dict, impact: float, impact_pct: float, contributors: list[dict]) -> str:
        top = contributors[0] if contributors else None
        if top:
            return (
                f"Le scénario {scenario['name']} produit un impact de {impact/1e6:+.2f} M€ "
                f"({impact_pct:+.2f} % NAV). Premier contributeur: {top['name']} "
                f"({top['impact_eur']/1e6:+.2f} M€)."
            )
        return f"Le scénario {scenario['name']} produit un impact de {impact/1e6:+.2f} M€."

    def sector_allocation(self) -> list[dict]:
        rows: dict[str, dict] = {}
        for position in self.positions:
            key = position["sector_id"]
            row = rows.setdefault(key, {"sector_id": key, "value_eur": 0.0, "weight_pct": 0.0, "positions": 0})
            row["value_eur"] += position["market_value_eur"]
            row["weight_pct"] += position["weight_pct"]
            row["positions"] += 1
        return sorted(rows.values(), key=lambda row: row["value_eur"], reverse=True)

    def base_metrics(self) -> dict:
        return {
            "nav_eur": self.nav,
            "duration_years": self.portfolio["metrics"]["duration_years"],
            "var_99_1d_pct": self.portfolio["metrics"]["var_99_1d_pct"],
            "liquidity_t1_pct": self.portfolio["metrics"]["liquidity_t1_pct"],
            "scenario_loss_pct": self.portfolio["metrics"]["scenario_loss_pct"],
            "constraints": self.portfolio["constraints"],
        }
