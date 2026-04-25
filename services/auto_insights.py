"""
Auto Insight Generation — Post-Query Mechanical Intelligence
Analyzes query results and sensor data to generate automatic insights.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoInsightGenerator:
    """
    Generates automatic insights after every query in mechanical mode.
    Detects trends, anomalies, and correlations in sensor/production data.
    """

    @classmethod
    def generate_from_data(cls, data: List[Dict], query: str = "") -> List[Dict[str, Any]]:
        """Generate insights from query result data."""
        if not data or not isinstance(data, list) or len(data) == 0:
            return []

        insights = []
        query_lower = query.lower()
        keys = set()
        for row in data:
            keys.update(row.keys())

        # Detect sensor data patterns
        if "vibration" in keys:
            insights.extend(cls._analyze_vibration(data))
        if "temperature" in keys:
            insights.extend(cls._analyze_temperature(data))
        if "efficiency" in keys:
            insights.extend(cls._analyze_efficiency(data))
        if "downtime_minutes" in keys:
            insights.extend(cls._analyze_downtime(data))
        if "defect_count" in keys:
            insights.extend(cls._analyze_defects(data))

        # Cross-correlation insights
        if "vibration" in keys and "temperature" in keys:
            insights.extend(cls._correlate_vib_temp(data))

        return insights[:5]  # Limit to top 5 insights

    @classmethod
    def generate_fleet_insights(cls, fleet_health: Dict) -> List[Dict[str, Any]]:
        """Generate fleet-wide insights from all machine health data."""
        insights = []
        machines = fleet_health.get("machines", [])

        critical_count = sum(1 for m in machines if m.get("health", {}).get("status") == "critical")
        warning_count = sum(1 for m in machines if m.get("health", {}).get("status") == "warning")

        if critical_count > 0:
            names = [m["name"] for m in machines if m.get("health", {}).get("status") == "critical"]
            insights.append({
                "text": f"⚠️ {critical_count} machine(s) in CRITICAL condition: {', '.join(names)}. Immediate attention required.",
                "severity": "critical", "type": "fleet_alert"
            })

        if warning_count > 0:
            insights.append({
                "text": f"🔶 {warning_count} machine(s) showing warning signs. Schedule preventive maintenance.",
                "severity": "medium", "type": "fleet_warning"
            })

        healthy = len(machines) - critical_count - warning_count
        if healthy > 0 and len(machines) > 0:
            pct = round(healthy / len(machines) * 100)
            insights.append({
                "text": f"✅ Fleet health: {pct}% of machines operating normally ({healthy}/{len(machines)}).",
                "severity": "low", "type": "fleet_summary"
            })

        return insights

    @classmethod
    def _analyze_vibration(cls, data):
        insights = []
        vibs = [float(r.get("vibration", 0)) for r in data if r.get("vibration") is not None]
        if not vibs: return insights

        avg_vib = sum(vibs) / len(vibs)
        max_vib = max(vibs)

        if avg_vib > 4.5:
            insights.append({
                "text": f"🔴 Average vibration is {avg_vib:.2f} mm/s — significantly above normal (< 2.5 mm/s). Indicates potential bearing degradation or misalignment.",
                "severity": "high", "type": "vibration_alert"
            })
        elif avg_vib > 3.0:
            insights.append({
                "text": f"🟡 Elevated vibration detected (avg: {avg_vib:.2f} mm/s). Monitor closely for progression.",
                "severity": "medium", "type": "vibration_warning"
            })

        # Trend detection
        if len(vibs) > 3:
            first_half = sum(vibs[:len(vibs)//2]) / (len(vibs)//2)
            second_half = sum(vibs[len(vibs)//2:]) / (len(vibs) - len(vibs)//2)
            pct_change = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            if pct_change > 15:
                insights.append({
                    "text": f"📈 Vibration trending upward: {pct_change:.0f}% increase detected over the measurement period.",
                    "severity": "medium", "type": "vibration_trend"
                })

        return insights

    @classmethod
    def _analyze_temperature(cls, data):
        insights = []
        temps = [float(r.get("temperature", 0)) for r in data if r.get("temperature") is not None]
        if not temps: return insights

        avg_temp = sum(temps) / len(temps)
        max_temp = max(temps)

        if max_temp > 100:
            insights.append({
                "text": f"🔴 Peak temperature reached {max_temp:.1f}°C — exceeding safe operating limits. Risk of thermal damage.",
                "severity": "high", "type": "temperature_alert"
            })
        elif avg_temp > 85:
            insights.append({
                "text": f"🟡 Average temperature is {avg_temp:.1f}°C — running hotter than optimal. Check cooling system.",
                "severity": "medium", "type": "temperature_warning"
            })

        return insights

    @classmethod
    def _analyze_efficiency(cls, data):
        insights = []
        effs = [float(r.get("efficiency", 0)) for r in data if r.get("efficiency") is not None]
        if not effs: return insights

        avg_eff = sum(effs) / len(effs)
        if avg_eff < 70:
            insights.append({
                "text": f"🔴 Average efficiency is {avg_eff:.1f}% — well below target (> 85%). Energy waste and potential component degradation.",
                "severity": "high", "type": "efficiency_alert"
            })
        elif avg_eff < 80:
            insights.append({
                "text": f"🟡 Efficiency averaging {avg_eff:.1f}% — below optimal. Recommend maintenance check.",
                "severity": "medium", "type": "efficiency_warning"
            })

        return insights

    @classmethod
    def _analyze_downtime(cls, data):
        insights = []
        downtimes = [int(r.get("downtime_minutes", 0)) for r in data if r.get("downtime_minutes") is not None]
        if not downtimes: return insights

        total = sum(downtimes)
        avg = total / len(downtimes) if downtimes else 0
        if avg > 30:
            insights.append({
                "text": f"⏱️ High downtime: averaging {avg:.0f} min/shift. Total: {total} min over {len(downtimes)} records.",
                "severity": "medium", "type": "downtime_alert"
            })

        return insights

    @classmethod
    def _analyze_defects(cls, data):
        insights = []
        defects = [int(r.get("defect_count", 0)) for r in data if r.get("defect_count") is not None]
        if not defects: return insights

        total = sum(defects)
        avg = total / len(defects) if defects else 0
        if avg > 5:
            insights.append({
                "text": f"🔧 Elevated defect rate: {avg:.1f} defects/record. Indicates process instability.",
                "severity": "high", "type": "quality_alert"
            })

        return insights

    @classmethod
    def _correlate_vib_temp(cls, data):
        insights = []
        pairs = [(float(r.get("vibration", 0)), float(r.get("temperature", 0))) 
                 for r in data if r.get("vibration") is not None and r.get("temperature") is not None]
        if len(pairs) < 3: return insights

        vibs, temps = zip(*pairs)
        avg_v, avg_t = sum(vibs)/len(vibs), sum(temps)/len(temps)
        if avg_v > 3.5 and avg_t > 80:
            insights.append({
                "text": f"🔗 Correlated anomaly: High vibration ({avg_v:.2f} mm/s) AND high temperature ({avg_t:.1f}°C) — classic bearing wear signature.",
                "severity": "high", "type": "correlation"
            })

        return insights
