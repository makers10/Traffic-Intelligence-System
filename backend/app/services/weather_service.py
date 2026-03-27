import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.config import settings
from app.models.weather import WeatherSnapshot

# Weather condition → traffic impact score
IMPACT_MAP = {
    "clear": 0.0, "clouds": 0.05, "drizzle": 0.25,
    "rain": 0.45, "thunderstorm": 0.75, "snow": 0.85,
    "fog": 0.60, "mist": 0.35, "haze": 0.20,
}

CACHE_TTL_MINUTES = 15


def _impact_score(condition: str, visibility_m: float, precipitation_mm: float) -> float:
    base = IMPACT_MAP.get(condition.lower(), 0.1)
    vis_penalty = max(0.0, (10000 - visibility_m) / 10000) * 0.3
    rain_penalty = min(precipitation_mm / 50.0, 0.3)
    return round(min(base + vis_penalty + rain_penalty, 1.0), 3)


async def fetch_weather(junction_id: str, lat: float, lon: float, db: Session) -> dict:
    """Fetch from OpenWeatherMap, cache in DB, return impact-enriched snapshot."""

    # Return cached if fresh enough
    since = datetime.utcnow() - timedelta(minutes=CACHE_TTL_MINUTES)
    cached = db.query(WeatherSnapshot).filter(
        WeatherSnapshot.junction_id == junction_id,
        WeatherSnapshot.fetched_at >= since,
    ).order_by(WeatherSnapshot.fetched_at.desc()).first()

    if cached:
        return _snapshot_to_dict(cached)

    if not settings.WEATHER_API_KEY:
        return _mock_weather(junction_id, db)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": settings.WEATHER_API_KEY, "units": "metric"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    condition = data["weather"][0]["main"]
    visibility_m = data.get("visibility", 10000)
    precipitation_mm = data.get("rain", {}).get("1h", 0.0)

    snap = WeatherSnapshot(
        junction_id=junction_id,
        condition=condition,
        temperature=data["main"]["temp"],
        humidity=data["main"]["humidity"],
        wind_speed=data["wind"]["speed"],
        visibility_m=visibility_m,
        precipitation_mm=precipitation_mm,
        impact_score=_impact_score(condition, visibility_m, precipitation_mm),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return _snapshot_to_dict(snap)


def _mock_weather(junction_id: str, db: Session) -> dict:
    snap = WeatherSnapshot(
        junction_id=junction_id,
        condition="clear", temperature=28.0,
        humidity=60.0, wind_speed=10.0,
        visibility_m=10000, precipitation_mm=0.0,
        impact_score=0.0,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return _snapshot_to_dict(snap)


def _snapshot_to_dict(snap: WeatherSnapshot) -> dict:
    return {
        "junction_id": snap.junction_id,
        "condition": snap.condition,
        "temperature": snap.temperature,
        "humidity": snap.humidity,
        "wind_speed": snap.wind_speed,
        "visibility_m": snap.visibility_m,
        "precipitation_mm": snap.precipitation_mm,
        "impact_score": snap.impact_score,
        "fetched_at": snap.fetched_at,
        "explanation": _explain(snap.condition, snap.impact_score),
    }


def _explain(condition: str, score: float) -> str:
    if score < 0.1:
        return "Clear conditions — no weather impact on traffic."
    elif score < 0.3:
        return f"{condition.title()} causing minor slowdowns. Expect slight delays."
    elif score < 0.6:
        return f"{condition.title()} reducing visibility and speed. Moderate impact."
    return f"Severe {condition.lower()} — significant traffic disruption expected."
