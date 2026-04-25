"""
Maintenance Advisor — Actionable Recommendation Engine
Combines reasoning + prediction outputs to generate prioritized maintenance actions.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MaintenanceAdvisor:
    """
    Generates actionable, prioritized maintenance recommendations
    based on mechanical reasoning and failure predictions.
    """

    URGENCY_MAP = {
        "critical": {"label": "IMMEDIATE", "hours": 4, "color": "red"},
        "high": {"label": "URGENT", "hours": 24, "color": "orange"},
        "medium": {"label": "SCHEDULED", "hours": 72, "color": "yellow"},
        "low": {"label": "ROUTINE", "hours": 168, "color": "green"},
    }

    ACTION_TEMPLATES = {
        "bearing_wear": [
            {"action": "Inspect bearing assembly for wear marks and pitting", "skill": "Mechanic L2", "time_min": 30},
            {"action": "Check and replace lubricant (grease/oil)", "skill": "Mechanic L1", "time_min": 15},
            {"action": "Measure bearing clearance with dial indicator", "skill": "Mechanic L2", "time_min": 20},
            {"action": "If clearance exceeds spec, schedule bearing replacement", "skill": "Mechanic L3", "time_min": 120},
        ],
        "cooling_failure": [
            {"action": "Verify coolant level and top up if needed", "skill": "Operator", "time_min": 10},
            {"action": "Inspect radiator/heat exchanger for blockage", "skill": "Mechanic L1", "time_min": 30},
            {"action": "Check cooling fan operation and belts", "skill": "Mechanic L1", "time_min": 20},
            {"action": "Flush cooling system if contamination detected", "skill": "Mechanic L2", "time_min": 60},
        ],
        "misalignment": [
            {"action": "Perform laser shaft alignment measurement", "skill": "Mechanic L2", "time_min": 45},
            {"action": "Check and tighten foundation bolts", "skill": "Mechanic L1", "time_min": 20},
            {"action": "Inspect flexible coupling for wear", "skill": "Mechanic L2", "time_min": 30},
            {"action": "Correct alignment to within 0.05mm tolerance", "skill": "Mechanic L3", "time_min": 90},
        ],
        "overload": [
            {"action": "Reduce operating load to below 85% rated capacity", "skill": "Operator", "time_min": 5},
            {"action": "Check for mechanical binding or obstruction", "skill": "Mechanic L1", "time_min": 30},
            {"action": "Review and adjust production schedule", "skill": "Supervisor", "time_min": 15},
            {"action": "Inspect motor current draw under load", "skill": "Electrician", "time_min": 20},
        ],
        "efficiency_degradation": [
            {"action": "Perform comprehensive system energy audit", "skill": "Engineer", "time_min": 120},
            {"action": "Inspect all wear components (belts, chains, seals)", "skill": "Mechanic L2", "time_min": 60},
            {"action": "Check for air/fluid leaks in pneumatic/hydraulic lines", "skill": "Mechanic L1", "time_min": 30},
            {"action": "Calibrate sensors and control systems", "skill": "Technician", "time_min": 45},
        ],
        "default": [
            {"action": "Perform visual inspection of machine", "skill": "Operator", "time_min": 15},
            {"action": "Check all fluid levels and top up as needed", "skill": "Operator", "time_min": 10},
            {"action": "Monitor parameters closely for next 24 hours", "skill": "Operator", "time_min": 5},
            {"action": "Schedule detailed inspection if issues persist", "skill": "Mechanic L1", "time_min": 30},
        ],
    }

    @classmethod
    def generate_recommendations(cls, diagnoses: List[Dict], prediction: Dict, machine_name: str = "Machine") -> Dict[str, Any]:
        if not diagnoses and prediction.get("risk_level", "low") == "low":
            return {
                "machine": machine_name, "urgency": "routine", "urgency_label": "ROUTINE",
                "summary": f"{machine_name} is operating within normal parameters. Continue standard maintenance schedule.",
                "actions": [{"action": "Continue routine maintenance schedule", "priority": "low", "skill": "Operator", "time_min": 10}],
                "next_check_hours": 168, "estimated_downtime_min": 0
            }

        top_severity = "low"
        for d in diagnoses:
            s = d.get("severity", "low")
            if s == "critical": top_severity = "critical"; break
            elif s == "high" and top_severity not in ("critical",): top_severity = "high"
            elif s == "medium" and top_severity == "low": top_severity = "medium"

        if prediction.get("risk_level") == "critical" and top_severity != "critical":
            top_severity = "high"

        urgency_info = cls.URGENCY_MAP.get(top_severity, cls.URGENCY_MAP["low"])
        actions = []
        seen_issues = set()

        for d in diagnoses:
            issue_key = d.get("issue", "").lower().replace(" ", "_").replace("/", "_")
            if issue_key in seen_issues: continue
            seen_issues.add(issue_key)

            template_key = None
            for k in cls.ACTION_TEMPLATES:
                if k in issue_key: template_key = k; break
            template = cls.ACTION_TEMPLATES.get(template_key, cls.ACTION_TEMPLATES["default"])

            for step in template:
                actions.append({
                    "action": step["action"], "priority": d.get("severity", "medium"),
                    "related_issue": d.get("issue", "Unknown"), "skill": step["skill"], "time_min": step["time_min"]
                })

        if prediction.get("failure_probability", 0) > 0.5:
            actions.insert(0, {
                "action": f"HIGH FAILURE RISK ({prediction['failure_probability']*100:.0f}%) — prioritize inspection",
                "priority": "critical", "related_issue": "Failure Prediction", "skill": "Supervisor", "time_min": 5
            })

        summary_parts = []
        if diagnoses:
            issues = [d["issue"] for d in diagnoses[:3]]
            summary_parts.append(f"Detected issues: {', '.join(issues)}")
        if prediction.get("failure_probability", 0) > 0.3:
            rul = prediction.get("remaining_useful_life_hours", 999)
            summary_parts.append(f"Failure probability: {prediction['failure_probability']*100:.0f}%, estimated RUL: {rul}h")

        summary = f"{machine_name}: {'. '.join(summary_parts)}. {urgency_info['label']} action required within {urgency_info['hours']}h."
        total_downtime = sum(a.get("time_min", 0) for a in actions[:5])

        return {
            "machine": machine_name, "urgency": top_severity, "urgency_label": urgency_info["label"],
            "summary": summary, "actions": actions,
            "next_check_hours": urgency_info["hours"], "estimated_downtime_min": total_downtime,
            "prediction_summary": {
                "failure_probability": prediction.get("failure_probability", 0),
                "remaining_useful_life_hours": prediction.get("remaining_useful_life_hours", 999),
                "risk_level": prediction.get("risk_level", "low"),
                "trend": prediction.get("trend", "stable")
            }
        }
