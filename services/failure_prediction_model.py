"""
Failure Prediction Model — XGBoost-based Failure Forecasting
Lightweight ML model for predicting machine failures from sensor time-series data.
"""
import logging
import numpy as np
import warnings
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

warnings.filterwarnings("ignore", category=UserWarning)
logger = logging.getLogger(__name__)


@dataclass
class FailurePrediction:
    failure_probability: float  # 0.0 - 1.0
    remaining_useful_life_hours: int
    risk_level: str  # low, medium, high, critical
    contributing_factors: List[Dict[str, Any]]
    trend: str  # improving, stable, degrading


class FailurePredictionModel:
    """
    XGBoost-based failure prediction model.
    Trains on synthetic/real sensor data and predicts failure probability.
    """
    
    _model = None
    _is_trained = False
    
    @classmethod
    def ensure_trained(cls):
        """Train the model if not already trained (lazy initialization)."""
        if cls._is_trained:
            return
        try:
            from xgboost import XGBClassifier
            cls._train_on_synthetic_data()
        except ImportError:
            logger.warning("XGBoost not available, using rule-based fallback")
            cls._model = None
            cls._is_trained = True
    
    @classmethod
    def _train_on_synthetic_data(cls):
        """Generate synthetic training data and fit the model."""
        from xgboost import XGBClassifier
        from sklearn.model_selection import train_test_split
        
        np.random.seed(42)
        n_samples = 3000
        
        # Generate features
        temp = np.random.normal(65, 15, n_samples)
        vibration = np.random.normal(2.0, 1.2, n_samples)
        pressure = np.random.normal(120, 25, n_samples)
        rpm = np.random.normal(2000, 500, n_samples)
        load = np.random.normal(60, 18, n_samples)
        efficiency = np.random.normal(85, 10, n_samples)
        
        # Derived features
        temp_rate = np.random.normal(0, 2, n_samples)  # Rate of change
        vib_rate = np.random.normal(0, 0.5, n_samples)
        temp_rolling_avg = temp + np.random.normal(0, 3, n_samples)
        vib_rolling_avg = vibration + np.random.normal(0, 0.3, n_samples)
        
        X = np.column_stack([
            temp, vibration, pressure, rpm, load, efficiency,
            temp_rate, vib_rate, temp_rolling_avg, vib_rolling_avg
        ])
        
        # Generate labels: failure = 1 based on physics rules
        failure_score = (
            np.where(temp > 90, 0.3, 0) +
            np.where(vibration > 4.5, 0.3, 0) +
            np.where(efficiency < 65, 0.2, 0) +
            np.where(load > 90, 0.15, 0) +
            np.where(np.abs(temp_rate) > 3, 0.1, 0) +
            np.where(np.abs(vib_rate) > 1.0, 0.1, 0) +
            np.random.normal(0, 0.05, n_samples)  # noise
        )
        y = (failure_score > 0.4).astype(int)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        cls._model = XGBClassifier(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric='logloss',
            verbosity=0
        )
        cls._model.fit(X_train, y_train)
        
        accuracy = cls._model.score(X_test, y_test)
        logger.info(f"Failure prediction model trained. Accuracy: {accuracy:.3f}")
        cls._is_trained = True
    
    @classmethod
    def predict(cls, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict failure probability for a machine based on its recent sensor data.
        
        Args:
            sensor_data: Recent sensor readings (last 24-48h recommended)
            
        Returns:
            FailurePrediction as dict
        """
        cls.ensure_trained()
        
        if not sensor_data or len(sensor_data) < 3:
            return asdict(FailurePrediction(
                failure_probability=0.0,
                remaining_useful_life_hours=999,
                risk_level="unknown",
                contributing_factors=[],
                trend="unknown"
            ))
        
        features = cls._extract_features(sensor_data)
        
        if cls._model is not None:
            X = np.array([features])
            prob = float(cls._model.predict_proba(X)[0][1])
        else:
            # Rule-based fallback if XGBoost not available
            prob = cls._rule_based_probability(sensor_data)
        
        # Calculate RUL (Remaining Useful Life) estimate
        rul = cls._estimate_rul(prob, sensor_data)
        
        # Determine risk level
        if prob >= 0.75:
            risk = "critical"
        elif prob >= 0.50:
            risk = "high"
        elif prob >= 0.25:
            risk = "medium"
        else:
            risk = "low"
        
        # Identify contributing factors
        factors = cls._identify_factors(sensor_data)
        
        # Determine trend
        trend = cls._determine_trend(sensor_data)
        
        prediction = FailurePrediction(
            failure_probability=round(prob, 3),
            remaining_useful_life_hours=rul,
            risk_level=risk,
            contributing_factors=factors,
            trend=trend
        )
        
        return asdict(prediction)
    
    @classmethod
    def _get_load(cls, r):
        return float(r.get("load_percent", r.get("load_percentage", 0)))

    @classmethod
    def _get_efficiency(cls, r):
        eff = r.get("efficiency")
        if eff is not None: return float(eff)
        temp = float(r.get("temperature", 65))
        load = cls._get_load(r)
        return max(30, min(99, 95 - (temp - 60) * 0.3 - max(0, load - 70) * 0.2))

    @classmethod
    def _extract_features(cls, sensor_data):
        """Extract ML features from sensor data."""
        temps = [float(r.get("temperature", 0)) for r in sensor_data]
        vibs = [float(r.get("vibration", 0)) for r in sensor_data]
        pressures = [float(r.get("pressure", 0)) for r in sensor_data]
        rpms = [float(r.get("rpm", 0)) for r in sensor_data]
        loads = [cls._get_load(r) for r in sensor_data]
        effs = [cls._get_efficiency(r) for r in sensor_data]
        
        mid = len(temps) // 2
        temp_rate = np.mean(temps[mid:]) - np.mean(temps[:mid]) if mid > 0 else 0
        vib_rate = np.mean(vibs[mid:]) - np.mean(vibs[:mid]) if mid > 0 else 0
        recent = min(20, len(temps))
        
        return [
            np.mean(temps), np.mean(vibs), np.mean(pressures), np.mean(rpms), np.mean(loads), np.mean(effs),
            temp_rate, vib_rate, np.mean(temps[-recent:]), np.mean(vibs[-recent:])
        ]
    
    @classmethod
    def _rule_based_probability(cls, sensor_data: List[Dict[str, Any]]) -> float:
        """Fallback probability calculation without ML model."""
        recent = sensor_data[-20:] if len(sensor_data) > 20 else sensor_data
        
        avg_temp = np.mean([float(r.get("temperature", 0)) for r in recent])
        avg_vib = np.mean([float(r.get("vibration", 0)) for r in recent])
        avg_eff = np.mean([float(r.get("efficiency", 0)) for r in recent])
        avg_load = np.mean([float(r.get("load_percent", 0)) for r in recent])
        
        prob = 0.0
        if avg_temp > 90: prob += 0.25
        elif avg_temp > 80: prob += 0.10
        if avg_vib > 5.0: prob += 0.30
        elif avg_vib > 3.5: prob += 0.15
        if avg_eff < 65: prob += 0.20
        elif avg_eff < 75: prob += 0.10
        if avg_load > 90: prob += 0.15
        
        return min(0.95, prob)
    
    @classmethod
    def _estimate_rul(cls, failure_prob: float, sensor_data: List[Dict[str, Any]]) -> int:
        """Estimate remaining useful life in hours."""
        if failure_prob < 0.1:
            return 720  # ~30 days
        elif failure_prob < 0.25:
            return 336  # ~14 days
        elif failure_prob < 0.5:
            return 120  # ~5 days
        elif failure_prob < 0.75:
            return 48   # ~2 days
        else:
            return 12   # ~12 hours
    
    @classmethod
    def _identify_factors(cls, sensor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key contributing factors to failure risk."""
        recent = sensor_data[-30:] if len(sensor_data) > 30 else sensor_data
        factors = []
        
        avg_temp = np.mean([float(r.get("temperature", 0)) for r in recent])
        avg_vib = np.mean([float(r.get("vibration", 0)) for r in recent])
        avg_eff = np.mean([cls._get_efficiency(r) for r in recent])
        avg_load = np.mean([cls._get_load(r) for r in recent])
        
        if avg_temp > 85:
            factors.append({"factor": "High Temperature", "value": f"{avg_temp:.1f}°C", "impact": "high"})
        if avg_vib > 3.5:
            factors.append({"factor": "Elevated Vibration", "value": f"{avg_vib:.2f} mm/s", "impact": "high"})
        if avg_eff < 75:
            factors.append({"factor": "Low Efficiency", "value": f"{avg_eff:.1f}%", "impact": "medium"})
        if avg_load > 85:
            factors.append({"factor": "High Load", "value": f"{avg_load:.1f}%", "impact": "medium"})
        
        return factors
    
    @classmethod
    def _determine_trend(cls, sensor_data):
        """Determine if conditions are improving, stable, or degrading."""
        if len(sensor_data) < 3:
            return "stable"
        mid = len(sensor_data) // 2
        # Use temperature trend as proxy when efficiency is not available
        early_temp = np.mean([float(r.get("temperature", 65)) for r in sensor_data[:mid]])
        late_temp = np.mean([float(r.get("temperature", 65)) for r in sensor_data[mid:]])
        early_vib = np.mean([float(r.get("vibration", 2)) for r in sensor_data[:mid]])
        late_vib = np.mean([float(r.get("vibration", 2)) for r in sensor_data[mid:]])
        
        temp_diff = late_temp - early_temp
        vib_diff = late_vib - early_vib
        if temp_diff > 5 or vib_diff > 1.0:
            return "degrading"
        elif temp_diff < -3 and vib_diff < -0.5:
            return "improving"
        return "stable"
