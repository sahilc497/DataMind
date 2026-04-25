"""
What-If Simulation Engine — Physics-Based Scenario Modeling
"""
import re, math, logging
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

class SimulationEngine:
    SCENARIO_PATTERNS = [
        {"keywords": ["increase load", "more load", "higher load"], "param": "load", "dir": "increase"},
        {"keywords": ["decrease load", "less load", "reduce load"], "param": "load", "dir": "decrease"},
        {"keywords": ["increase rpm", "faster", "speed up", "higher speed"], "param": "rpm", "dir": "increase"},
        {"keywords": ["decrease rpm", "slower", "reduce rpm", "lower speed"], "param": "rpm", "dir": "decrease"},
        {"keywords": ["reduce cooling", "less cooling", "disable cooling"], "param": "cooling", "dir": "decrease"},
        {"keywords": ["increase cooling", "more cooling", "boost cooling"], "param": "cooling", "dir": "increase"},
        {"keywords": ["increase pressure", "more pressure"], "param": "pressure", "dir": "increase"},
        {"keywords": ["decrease pressure", "reduce pressure"], "param": "pressure", "dir": "decrease"},
    ]

    @classmethod
    def simulate(cls, scenario: str, current_state: Dict[str, float]) -> Dict[str, Any]:
        param, direction, magnitude = cls._parse_scenario(scenario)
        if not param:
            return {"predicted_effects": {}, "risk_change": "unchanged", "risk_delta": 0.0,
                    "explanation": f"Could not parse scenario: '{scenario}'. Try: 'increase load by 20%'",
                    "recommendations": ["Please specify a clear parameter change"],
                    "before_state": current_state, "after_state": current_state}

        after = dict(current_state)
        effects = {}

        if param == "load":
            delta = magnitude if direction == "increase" else -magnitude
            after["load_percent"] = max(0, min(100, current_state.get("load_percent", 60) + delta))
            tc = delta * 0.35; ec = delta * -0.12; vc = delta * 0.02
            after["temperature"] = round(current_state.get("temperature", 65) + tc, 1)
            after["efficiency"] = round(max(30, min(99, current_state.get("efficiency", 85) + ec)), 1)
            after["vibration"] = round(max(0.3, current_state.get("vibration", 2.0) + vc), 2)
            effects = {"temperature": f"{tc:+.1f}°C", "efficiency": f"{ec:+.1f}%", "vibration": f"{vc:+.2f} mm/s", "load": f"{delta:+.0f}%"}

        elif param == "rpm":
            delta = magnitude * 30 if direction == "increase" else -magnitude * 30
            after["rpm"] = max(100, current_state.get("rpm", 2000) + delta)
            tc = abs(delta) * 0.015 * (1 if direction == "increase" else -0.5)
            vc = (abs(delta) ** 1.3) * 0.002 * (1 if direction == "increase" else -0.7)
            ec = -(abs(delta) ** 0.5) * 0.005
            after["temperature"] = round(current_state.get("temperature", 65) + tc, 1)
            after["vibration"] = round(max(0.3, current_state.get("vibration", 2.0) + vc), 2)
            after["efficiency"] = round(max(30, min(99, current_state.get("efficiency", 85) + ec)), 1)
            effects = {"temperature": f"{tc:+.1f}°C", "vibration": f"{vc:+.2f} mm/s", "efficiency": f"{ec:+.1f}%", "rpm": f"{delta:+.0f}"}

        elif param == "cooling":
            delta = magnitude if direction == "increase" else -magnitude
            tc = -delta * 0.5; ec = delta * 0.15
            after["temperature"] = round(max(25, current_state.get("temperature", 65) + tc), 1)
            after["efficiency"] = round(max(30, min(99, current_state.get("efficiency", 85) + ec)), 1)
            effects = {"temperature": f"{tc:+.1f}°C", "efficiency": f"{ec:+.1f}%"}

        elif param == "pressure":
            delta = magnitude * 1.5 if direction == "increase" else -magnitude * 1.5
            after["pressure"] = round(max(20, current_state.get("pressure", 120) + delta), 1)
            ec = min(5, delta * 0.08) if direction == "increase" else delta * 0.08
            after["efficiency"] = round(max(30, min(99, current_state.get("efficiency", 85) + ec)), 1)
            effects = {"pressure": f"{delta:+.1f} PSI", "efficiency": f"{ec:+.1f}%"}

        br = cls._risk_score(current_state); ar = cls._risk_score(after)
        rd = round(ar - br, 3)
        rc = "significantly_increased" if rd > 0.1 else ("increased" if rd > 0.02 else ("significantly_decreased" if rd < -0.1 else ("decreased" if rd < -0.02 else "unchanged")))

        pn = {"load": "load", "rpm": "speed (RPM)", "cooling": "cooling capacity", "pressure": "pressure"}
        dw = "Increasing" if direction == "increase" else "Decreasing"
        ep = [f"{k}: {v}" for k, v in effects.items() if k not in ("load", "cooling_change", "rpm")]
        expl = f"{dw} {pn.get(param, param)} by {magnitude}% would result in: {', '.join(ep)}. "
        expl += "⚠️ This increases failure risk." if "increased" in rc else ("✅ This reduces failure risk." if "decreased" in rc else "Risk level remains approximately the same.")

        recs = []
        if after.get("temperature", 0) > 95: recs.append("Monitor temperature — approaching thermal limits")
        if after.get("vibration", 0) > 5.0: recs.append("Vibration elevated — schedule inspection")
        if after.get("efficiency", 100) < 70: recs.append("Efficiency will drop significantly")
        if after.get("load_percent", 0) > 90: recs.append("Load approaching maximum capacity")
        if "increased" in rc: recs.append("Consider gradual implementation with monitoring")
        if not recs: recs.append("Change is within safe operating parameters")

        return {"predicted_effects": effects, "risk_change": rc, "risk_delta": rd,
                "explanation": expl, "recommendations": recs,
                "before_state": {k: round(v, 2) if isinstance(v, float) else v for k, v in current_state.items()},
                "after_state": {k: round(v, 2) if isinstance(v, float) else v for k, v in after.items()}}

    @classmethod
    def _parse_scenario(cls, scenario):
        sl = scenario.lower()
        param = direction = None
        for p in cls.SCENARIO_PATTERNS:
            if any(kw in sl for kw in p["keywords"]):
                param, direction = p["param"], p["dir"]; break
        magnitude = 10
        m = re.search(r'(\d+)\s*%', scenario)
        if m: magnitude = int(m.group(1))
        else:
            m = re.search(r'by\s+(\d+)', scenario)
            if m: magnitude = int(m.group(1))
        return param, direction, magnitude

    @classmethod
    def _risk_score(cls, s):
        r = 0.0
        t = s.get("temperature", 65)
        r += 0.3 if t > 105 else (0.15 if t > 90 else (0.05 if t > 80 else 0))
        v = s.get("vibration", 2.0)
        r += 0.3 if v > 6.0 else (0.15 if v > 4.5 else (0.05 if v > 3.0 else 0))
        e = s.get("efficiency", 85)
        r += 0.2 if e < 55 else (0.1 if e < 70 else (0.05 if e < 80 else 0))
        l = s.get("load_percent", 60)
        r += 0.2 if l > 95 else (0.1 if l > 85 else 0)
        return min(1.0, r)
