"""
Mechanical Reasoning Engine — Physics-Aware Pattern Detection
Analyzes sensor data to detect mechanical failure patterns using rule-based reasoning.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MechanicalDiagnosis:
    issue: str
    cause: str
    severity: str  # low, medium, high, critical
    confidence: int  # 0-100
    affected_component: str
    physics_explanation: str
    recommended_action: str


class MechanicalReasoningEngine:
    """
    Physics-aware reasoning engine that interprets sensor data 
    in a mechanical engineering context.
    """
    
    # Threshold definitions for mechanical parameters
    THRESHOLDS = {
        "temperature": {"normal": 75, "warning": 90, "critical": 105},
        "vibration": {"normal": 2.5, "warning": 4.5, "critical": 6.5},
        "pressure": {"normal_range": (80, 160), "warning_low": 60, "warning_high": 180},
        "rpm_variance": {"normal": 0.05, "warning": 0.15, "critical": 0.25},
        "efficiency": {"normal": 85, "warning": 70, "critical": 55},
    }
    
    # Physics-based failure pattern rules
    FAILURE_PATTERNS = [
        {
            "id": "bearing_wear",
            "name": "Bearing Wear / Degradation",
            "conditions": lambda d: d["avg_vibration"] > 4.0 and d["avg_temperature"] > 80,
            "severity_fn": lambda d: "critical" if d["avg_vibration"] > 6.0 else ("high" if d["avg_vibration"] > 5.0 else "medium"),
            "confidence_fn": lambda d: min(95, int(50 + (d["avg_vibration"] - 4.0) * 15 + (d["avg_temperature"] - 80) * 0.5)),
            "component": "Bearings",
            "cause": "Excessive friction in bearing assembly due to lubricant degradation or contamination",
            "physics": "Increased friction coefficient leads to energy dissipation as heat (Q = μ·F·v). "
                      "Vibration amplitude grows as bearing clearance increases from wear, "
                      "creating harmonic resonance at bearing defect frequencies.",
            "action": "Immediate bearing inspection. Check lubricant condition. Replace if vibration exceeds 7.0 mm/s."
        },
        {
            "id": "cooling_failure",
            "name": "Cooling System Inefficiency",
            "conditions": lambda d: d["avg_temperature"] > 90 and d["avg_load"] < 50,
            "severity_fn": lambda d: "critical" if d["avg_temperature"] > 110 else ("high" if d["avg_temperature"] > 100 else "medium"),
            "confidence_fn": lambda d: min(92, int(60 + (d["avg_temperature"] - 90) * 2 - d["avg_load"] * 0.3)),
            "component": "Cooling System",
            "cause": "Cooling system failure — high thermal output despite low mechanical load indicates heat dissipation breakdown",
            "physics": "Newton's law of cooling: dT/dt = -h·A·(T-T_env). When cooling coefficient h drops "
                      "(blocked coolant, failed fan, degraded thermal paste), steady-state temperature rises "
                      "independent of load. Thermal runaway risk if T exceeds material limits.",
            "action": "Inspect coolant levels and flow rate. Check radiator/fan operation. Clean heat exchangers."
        },
        {
            "id": "misalignment",
            "name": "Shaft Misalignment / Instability",
            "conditions": lambda d: d["rpm_cv"] > 0.12 and d["avg_vibration"] > 3.0,
            "severity_fn": lambda d: "high" if d["rpm_cv"] > 0.20 else "medium",
            "confidence_fn": lambda d: min(90, int(55 + d["rpm_cv"] * 200)),
            "component": "Drive Shaft / Coupling",
            "cause": "Angular or parallel misalignment between connected shafts causing rotational instability",
            "physics": "Misaligned shafts create radial forces F = k·δ (stiffness × offset). "
                      "This generates 1X and 2X vibration harmonics. RPM fluctuation occurs as "
                      "the motor compensates for variable torque load from the misaligned coupling.",
            "action": "Perform laser alignment check. Inspect coupling condition. Verify foundation bolts."
        },
        {
            "id": "seal_degradation",
            "name": "Seal / Gasket Degradation",
            "conditions": lambda d: d["avg_pressure"] < 75 and d["avg_temperature"] > 85,
            "severity_fn": lambda d: "high" if d["avg_pressure"] < 60 else "medium",
            "confidence_fn": lambda d: min(85, int(45 + (85 - d["avg_pressure"]) * 0.8)),
            "component": "Seals / Gaskets",
            "cause": "Pressure loss combined with elevated temperature indicates seal material degradation",
            "physics": "Elastomer seals degrade above their continuous service temperature (typically 80-120°C). "
                      "Thermal expansion coefficient mismatch causes gap formation. "
                      "Pressure drop follows Poiseuille's law through the leak path.",
            "action": "Inspect all seals and gaskets. Check for visible leaks. Replace aged seals preventively."
        },
        {
            "id": "overload",
            "name": "Mechanical Overload",
            "conditions": lambda d: d["avg_load"] > 85 and d["avg_temperature"] > 85,
            "severity_fn": lambda d: "critical" if d["avg_load"] > 95 else "high",
            "confidence_fn": lambda d: min(93, int(60 + d["avg_load"] * 0.3)),
            "component": "Drive Motor / Gearbox",
            "cause": "Sustained operation beyond rated capacity causing thermal and mechanical stress",
            "physics": "Power dissipated as heat: P_loss = I²R (electrical) + friction losses. "
                      "Operating above rated load increases current draw, accelerating insulation degradation "
                      "(Arrhenius equation: life halves for every 10°C rise).",
            "action": "Reduce load immediately. Review production schedule. Check for binding or obstruction."
        },
        {
            "id": "efficiency_degradation",
            "name": "Progressive Efficiency Loss",
            "conditions": lambda d: d["avg_efficiency"] < 72 and d["efficiency_trend"] < -0.3,
            "severity_fn": lambda d: "high" if d["avg_efficiency"] < 60 else "medium",
            "confidence_fn": lambda d: min(88, int(50 + abs(d["efficiency_trend"]) * 30)),
            "component": "Overall System",
            "cause": "Gradual component degradation causing increasing energy losses",
            "physics": "System efficiency η = P_out/P_in decreases as internal losses grow. "
                      "Wear increases clearances, friction surfaces degrade, and thermal losses mount. "
                      "This is a leading indicator of impending component failure.",
            "action": "Schedule comprehensive maintenance. Check all wear components. Perform energy audit."
        },
        {
            "id": "vibration_resonance",
            "name": "Structural Resonance",
            "conditions": lambda d: d["max_vibration"] > 7.0 and d["avg_vibration"] < 3.5,
            "severity_fn": lambda d: "high",
            "confidence_fn": lambda d: min(80, int(50 + (d["max_vibration"] - 7.0) * 10)),
            "component": "Foundation / Mounting",
            "cause": "Intermittent vibration spikes suggest structural resonance at certain operating speeds",
            "physics": "When operating frequency approaches natural frequency (f_n = √(k/m)/2π), "
                      "vibration amplifies dramatically (resonance). Small damping ratio means "
                      "large amplification factor Q = 1/(2ζ).",
            "action": "Map vibration vs RPM to identify resonance points. Add damping or change operating speed."
        },
        {
            "id": "lubrication_failure",
            "name": "Lubrication System Failure",
            "conditions": lambda d: d["avg_vibration"] > 3.5 and d["avg_temperature"] > 80 and d["avg_efficiency"] < 80,
            "severity_fn": lambda d: "high" if d["avg_vibration"] > 5.0 else "medium",
            "confidence_fn": lambda d: min(87, int(45 + d["avg_vibration"] * 8)),
            "component": "Lubrication System",
            "cause": "Insufficient or degraded lubrication causing increased friction across moving parts",
            "physics": "Stribeck curve transition: as lubricant film thickness decreases, "
                      "contact transitions from hydrodynamic to boundary lubrication. "
                      "Friction coefficient can increase 10-100x, generating heat and vibration.",
            "action": "Check oil level and condition. Inspect oil filters. Verify lubrication pump operation."
        },
    ]
    
    @classmethod
    def analyze_machine(cls, sensor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sensor data for a single machine and return detected issues.
        
        Args:
            sensor_data: List of sensor readings (dicts with temp, vibration, pressure, rpm, etc.)
            
        Returns:
            List of MechanicalDiagnosis as dicts
        """
        if not sensor_data or len(sensor_data) < 2:
            return []
        
        # Compute aggregated metrics
        metrics = cls._compute_metrics(sensor_data)
        
        # Match against failure patterns
        diagnoses = []
        for pattern in cls.FAILURE_PATTERNS:
            try:
                if pattern["conditions"](metrics):
                    diagnosis = MechanicalDiagnosis(
                        issue=pattern["name"],
                        cause=pattern["cause"],
                        severity=pattern["severity_fn"](metrics),
                        confidence=pattern["confidence_fn"](metrics),
                        affected_component=pattern["component"],
                        physics_explanation=pattern["physics"],
                        recommended_action=pattern["action"]
                    )
                    diagnoses.append(asdict(diagnosis))
            except Exception as e:
                logger.warning(f"Pattern {pattern['id']} evaluation failed: {e}")
        
        # Sort by severity (critical > high > medium > low) then by confidence
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        diagnoses.sort(key=lambda d: (severity_order.get(d["severity"], 4), -d["confidence"]))
        
        return diagnoses
    
    @classmethod
    def analyze_fleet(cls, fleet_data: Dict[int, List[Dict[str, Any]]]) -> Dict[int, List[Dict[str, Any]]]:
        """Analyze all machines and return per-machine diagnoses."""
        results = {}
        for machine_id, data in fleet_data.items():
            results[machine_id] = cls.analyze_machine(data)
        return results
    
    @classmethod
    def get_machine_health_status(cls, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a health summary for a machine."""
        diagnoses = cls.analyze_machine(sensor_data)
        metrics = cls._compute_metrics(sensor_data) if sensor_data else {}
        
        if not diagnoses:
            status = "healthy"
            color = "green"
        elif any(d["severity"] in ("critical", "high") for d in diagnoses):
            status = "critical"
            color = "red"
        else:
            status = "warning"
            color = "yellow"
        
        return {
            "status": status,
            "color": color,
            "issues_count": len(diagnoses),
            "top_issue": diagnoses[0] if diagnoses else None,
            "metrics": metrics,
            "diagnoses": diagnoses
        }
    
    @classmethod
    def _get_load(cls, row: Dict[str, Any]) -> float:
        """Get load from either load_percent or load_percentage field."""
        return float(row.get("load_percent", row.get("load_percentage", 0)))

    @classmethod
    def _get_efficiency(cls, row: Dict[str, Any]) -> float:
        """Get efficiency or estimate it from temperature and load."""
        eff = row.get("efficiency")
        if eff is not None:
            return float(eff)
        # Estimate: lower temp + moderate load = higher efficiency
        temp = float(row.get("temperature", 65))
        load = cls._get_load(row)
        estimated = 95 - (temp - 60) * 0.3 - max(0, load - 70) * 0.2
        return max(30, min(99, estimated))

    @classmethod
    def _compute_metrics(cls, sensor_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute aggregated metrics from raw sensor data."""
        temps = [float(r.get("temperature", 0)) for r in sensor_data]
        vibs = [float(r.get("vibration", 0)) for r in sensor_data]
        pressures = [float(r.get("pressure", 0)) for r in sensor_data]
        rpms = [float(r.get("rpm", 0)) for r in sensor_data]
        loads = [cls._get_load(r) for r in sensor_data]
        efficiencies = [cls._get_efficiency(r) for r in sensor_data]
        
        avg_rpm = sum(rpms) / len(rpms) if rpms else 0
        rpm_std = (sum((r - avg_rpm) ** 2 for r in rpms) / len(rpms)) ** 0.5 if rpms else 0
        
        # Efficiency trend (linear regression slope over recent data)
        recent_eff = efficiencies[-50:] if len(efficiencies) > 50 else efficiencies
        eff_trend = 0
        if len(recent_eff) > 3:
            n = len(recent_eff)
            x_mean = (n - 1) / 2.0
            y_mean = sum(recent_eff) / n
            numerator = sum((i - x_mean) * (recent_eff[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            eff_trend = numerator / denominator if denominator != 0 else 0
        
        return {
            "avg_temperature": round(sum(temps) / len(temps), 1) if temps else 0,
            "max_temperature": round(max(temps), 1) if temps else 0,
            "avg_vibration": round(sum(vibs) / len(vibs), 2) if vibs else 0,
            "max_vibration": round(max(vibs), 2) if vibs else 0,
            "avg_pressure": round(sum(pressures) / len(pressures), 1) if pressures else 0,
            "avg_rpm": round(avg_rpm, 0),
            "rpm_cv": round(rpm_std / avg_rpm, 3) if avg_rpm > 0 else 0,
            "avg_load": round(sum(loads) / len(loads), 1) if loads else 0,
            "avg_efficiency": round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else 0,
            "efficiency_trend": round(eff_trend, 3),
            "reading_count": len(sensor_data)
        }
