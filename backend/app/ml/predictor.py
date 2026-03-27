import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODEL_PATH, exist_ok=True)


def _congestion_label(level: float) -> str:
    if level < 0.25:
        return "free"
    elif level < 0.5:
        return "moderate"
    elif level < 0.75:
        return "heavy"
    return "standstill"


def _extract_time_features(dt: datetime) -> dict:
    """Extract cyclical time features from a datetime."""
    return {
        "hour_sin": np.sin(2 * np.pi * dt.hour / 24),
        "hour_cos": np.cos(2 * np.pi * dt.hour / 24),
        "dow_sin": np.sin(2 * np.pi * dt.weekday() / 7),
        "dow_cos": np.cos(2 * np.pi * dt.weekday() / 7),
        "is_weekend": int(dt.weekday() >= 5),
        "is_peak": int(dt.hour in range(7, 10) or dt.hour in range(17, 20)),
    }


def _weather_features(condition: Optional[str], visibility_m: Optional[float]) -> dict:
    """Encode weather into numeric impact features."""
    weather_impact = {
        "clear": 0.0, "cloudy": 0.1, "rain": 0.4,
        "heavy_rain": 0.7, "fog": 0.6, "snow": 0.9,
    }
    impact = weather_impact.get((condition or "clear").lower(), 0.0)
    vis_norm = min((visibility_m or 10000) / 10000, 1.0)
    return {
        "weather_impact": impact,
        "visibility_norm": vis_norm,
    }


def build_feature_vector(
    speed_kmh: float,
    vehicle_density: int,
    occupancy_pct: Optional[float],
    weather_condition: Optional[str],
    visibility_m: Optional[float],
    forecast_dt: datetime,
) -> np.ndarray:
    """Assemble all features into a single vector for inference."""
    feats = {}
    feats["speed_kmh"] = speed_kmh
    feats["vehicle_density"] = vehicle_density
    feats["occupancy_pct"] = occupancy_pct or 0.0
    feats.update(_extract_time_features(forecast_dt))
    feats.update(_weather_features(weather_condition, visibility_m))
    return np.array(list(feats.values())).reshape(1, -1)


class TrafficPredictor:
    """
    Wraps a GradientBoostingRegressor to predict congestion level (0-1).
    Falls back to a heuristic model when no trained model exists.
    """

    def __init__(self, junction_id: str):
        self.junction_id = junction_id
        self.model: Optional[GradientBoostingRegressor] = None
        self.scaler = StandardScaler()
        self._load()

    def _model_file(self) -> str:
        return os.path.join(MODEL_PATH, f"{self.junction_id}_model.pkl")

    def _load(self):
        path = self._model_file()
        if os.path.exists(path):
            with open(path, "rb") as f:
                saved = pickle.load(f)
                self.model = saved["model"]
                self.scaler = saved["scaler"]

    def save(self):
        with open(self._model_file(), "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

    def train(self, readings: List[dict]):
        """
        Train on a list of reading dicts with keys:
        speed_kmh, vehicle_density, occupancy_pct,
        weather_condition, visibility_m, timestamp, congestion_level
        """
        rows = []
        labels = []
        for r in readings:
            vec = build_feature_vector(
                r["speed_kmh"], r["vehicle_density"],
                r.get("occupancy_pct"), r.get("weather_condition"),
                r.get("visibility_m"), r["timestamp"],
            )
            rows.append(vec.flatten())
            labels.append(r["congestion_level"])

        X = np.array(rows)
        y = np.array(labels)
        X_scaled = self.scaler.fit_transform(X)
        self.model = GradientBoostingRegressor(n_estimators=100, max_depth=4)
        self.model.fit(X_scaled, y)
        self.save()


    def _heuristic_predict(self, speed_kmh: float, vehicle_density: int, forecast_dt: datetime) -> float:
        """Rule-based fallback when no trained model is available."""
        # Normalize speed: assume free-flow ~80 km/h
        speed_score = max(0.0, 1.0 - (speed_kmh / 80.0))
        # Normalize density: assume jam ~200 vehicles/km
        density_score = min(vehicle_density / 200.0, 1.0)
        # Peak hour boost
        peak_boost = 0.15 if forecast_dt.hour in range(7, 10) or forecast_dt.hour in range(17, 20) else 0.0
        level = (speed_score * 0.5) + (density_score * 0.35) + peak_boost
        return round(min(max(level, 0.0), 1.0), 3)

    def predict(
        self,
        speed_kmh: float,
        vehicle_density: int,
        occupancy_pct: Optional[float],
        weather_condition: Optional[str],
        visibility_m: Optional[float],
        horizon_minutes: int = 30,
    ) -> dict:
        forecast_dt = datetime.utcnow() + timedelta(minutes=horizon_minutes)

        if self.model is None:
            level = self._heuristic_predict(speed_kmh, vehicle_density, forecast_dt)
            confidence = 0.55
        else:
            vec = build_feature_vector(
                speed_kmh, vehicle_density, occupancy_pct,
                weather_condition, visibility_m, forecast_dt,
            )
            vec_scaled = self.scaler.transform(vec)
            level = float(np.clip(self.model.predict(vec_scaled)[0], 0.0, 1.0))
            confidence = 0.85

        predicted_speed = speed_kmh * (1.0 - level * 0.6)

        return {
            "junction_id": self.junction_id,
            "forecast_time": forecast_dt,
            "congestion_level": round(level, 3),
            "predicted_speed": round(predicted_speed, 1),
            "confidence": confidence,
            "label": _congestion_label(level),
        }
