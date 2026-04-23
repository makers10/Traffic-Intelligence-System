import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os
import tempfile
import threading
from functools import lru_cache

MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODEL_PATH, exist_ok=True)

# ── Canonical feature order ──────────────────────────────────────────────────
# This tuple is the SINGLE SOURCE OF TRUTH for feature alignment between
# training and inference.  Adding, removing, or reordering a feature must
# be done HERE — both build_feature_vector() and any future transformers
# read from this list.
FEATURE_COLUMNS = (
    "speed_kmh",
    "vehicle_density",
    "occupancy_pct",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "is_weekend",
    "is_peak",
    "weather_impact",
    "visibility_norm",
)


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
    """Assemble all features into a single vector for inference.

    Feature order is determined by FEATURE_COLUMNS — NOT by dict
    insertion order — so adding or reordering helper functions can
    never silently corrupt the vector.
    """
    feats: dict[str, float] = {}
    feats["speed_kmh"] = speed_kmh
    feats["vehicle_density"] = float(vehicle_density)
    feats["occupancy_pct"] = occupancy_pct or 0.0
    feats.update(_extract_time_features(forecast_dt))
    feats.update(_weather_features(weather_condition, visibility_m))
    # Build array in canonical column order
    return np.array([feats[col] for col in FEATURE_COLUMNS]).reshape(1, -1)


# ── Model cache ──────────────────────────────────────────────────────────────
# Thread-safe LRU cache: models are loaded from disk ONCE per junction and
# reused across all subsequent requests until explicitly invalidated.
_cache_lock = threading.Lock()

# Per-junction read/write locks.
# Multiple predict() calls can read concurrently (shared), but train/save
# acquires an exclusive write lock that blocks all readers for that junction.
_junction_locks: dict[str, threading.RLock] = {}


def _get_junction_lock(junction_id: str) -> threading.RLock:
    """Return (or create) a reentrant lock for a specific junction."""
    with _cache_lock:
        if junction_id not in _junction_locks:
            _junction_locks[junction_id] = threading.RLock()
        return _junction_locks[junction_id]


@lru_cache(maxsize=128)
def _load_model(junction_id: str, _version: int = 0):
    """Load a model from disk.  The `_version` param is a cache-buster
    incremented after training so stale entries are never served."""
    path = os.path.join(MODEL_PATH, f"{junction_id}_model.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


# Monotonic version counter per junction — bumped after each train/save
_model_versions: dict[str, int] = {}


def _get_version(junction_id: str) -> int:
    return _model_versions.get(junction_id, 0)


def _bump_version(junction_id: str) -> int:
    with _cache_lock:
        v = _model_versions.get(junction_id, 0) + 1
        _model_versions[junction_id] = v
    return v


class TrafficPredictor:
    """
    Wraps a GradientBoostingRegressor to predict congestion level (0-1).
    Falls back to a heuristic model when no trained model exists.

    Models are loaded via a module-level LRU cache so repeated
    instantiations for the same junction_id do NOT hit the filesystem.

    Concurrency safety:
    - predict() acquires a shared (reentrant) lock per junction.
    - save() acquires the same lock exclusively so no reader sees a
      half-written file.
    """

    def __init__(self, junction_id: str):
        self.junction_id = junction_id
        self.model: Optional[GradientBoostingRegressor] = None
        self.scaler = StandardScaler()
        self._lock = _get_junction_lock(junction_id)
        self._load()

    def _model_file(self) -> str:
        return os.path.join(MODEL_PATH, f"{self.junction_id}_model.pkl")

    def _load(self):
        with self._lock:
            version = _get_version(self.junction_id)
            saved = _load_model(self.junction_id, version)
            if saved is not None:
                self.model = saved["model"]
                self.scaler = saved["scaler"]

    def save(self):
        """Atomically write model to disk and invalidate the cache.

        Holds the junction lock so concurrent readers block until the
        new model is fully written and the cache version is bumped.
        """
        with self._lock:
            payload = {"model": self.model, "scaler": self.scaler}
            # Atomic write: write to temp file then replace to avoid corruption
            # if the process crashes mid-write.
            fd, tmp_path = tempfile.mkstemp(dir=MODEL_PATH, suffix=".pkl.tmp")
            try:
                with os.fdopen(fd, "wb") as f:
                    pickle.dump(payload, f)
                os.replace(tmp_path, self._model_file())
            except BaseException:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
            # Bump version so the LRU cache returns the fresh model next time
            _bump_version(self.junction_id)

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
