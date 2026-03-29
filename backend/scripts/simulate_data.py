"""
Traffic data simulator.
Generates realistic historical + live readings for testing.

Usage:
    python scripts/simulate_data.py --days 7 --junctions J001 J002 J003
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import random
import math
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models.traffic import TrafficReading
from app.models.transport import TransportReading


JUNCTION_IDS = ["J001", "J002", "J003", "J004", "J005"]

WEATHER_CONDITIONS = ["clear", "clear", "clear", "clouds", "rain", "fog", "drizzle"]

# Peak hour speed degradation profile (hour → speed multiplier)
def speed_multiplier(hour: int) -> float:
    if 7 <= hour <= 9:   return 0.45   # morning peak
    if 17 <= hour <= 19: return 0.40   # evening peak
    if 22 <= hour <= 5:  return 0.95   # night
    return 0.75                         # off-peak


def density_for_hour(hour: int) -> int:
    if 7 <= hour <= 9:   return random.randint(140, 190)
    if 17 <= hour <= 19: return random.randint(150, 200)
    if 22 <= hour or hour <= 5: return random.randint(10, 40)
    return random.randint(60, 120)


def generate_reading(junction_id: str, ts: datetime) -> dict:
    hour = ts.hour
    base_speed = 70.0
    weather = random.choice(WEATHER_CONDITIONS)
    weather_penalty = {"rain": 0.75, "fog": 0.70, "drizzle": 0.85}.get(weather, 1.0)

    speed = round(base_speed * speed_multiplier(hour) * weather_penalty + random.gauss(0, 3), 1)
    speed = max(5.0, min(speed, 90.0))
    density = density_for_hour(hour) + random.randint(-10, 10)
    occupancy = min(density / 2.0, 100.0)

    return {
        "junction_id": junction_id,
        "timestamp": ts,
        "speed_kmh": speed,
        "vehicle_density": max(0, density),
        "occupancy_pct": round(occupancy, 1),
        "weather_condition": weather,
        "temperature": round(28 + random.gauss(0, 4), 1),
        "visibility_m": 10000 if weather == "clear" else random.randint(2000, 8000),
    }


def generate_transport_reading(junction_id: str, ts: datetime) -> dict:
    hour = ts.hour
    is_peak = 7 <= hour <= 9 or 17 <= hour <= 19
    rideshare = random.randint(80, 200) if is_peak else random.randint(20, 80)
    metro = random.randint(300, 600) if is_peak else random.randint(50, 200)
    bus = random.randint(100, 300) if is_peak else random.randint(30, 100)
    return {
        "junction_id": junction_id,
        "timestamp": ts,
        "rideshare_trips": rideshare,
        "rideshare_avg_wait_min": round(random.uniform(3, 15), 1),
        "metro_boardings": metro,
        "bus_boardings": bus,
        "road_pressure_index": round(rideshare / (rideshare + metro + bus), 3),
        "transit_shift_score": round((metro + bus) / (rideshare + metro + bus), 3),
    }


def simulate(days: int, junction_ids: list, interval_minutes: int = 15):
    db = SessionLocal()
    try:
        start = datetime.utcnow() - timedelta(days=days)
        total = 0

        for jid in junction_ids:
            ts = start
            while ts <= datetime.utcnow():
                # Traffic reading
                r = generate_reading(jid, ts)
                db.add(TrafficReading(**r))

                # Transport reading every hour
                if ts.minute == 0:
                    t = generate_transport_reading(jid, ts)
                    db.add(TransportReading(**t))

                ts += timedelta(minutes=interval_minutes)
                total += 1

            db.commit()
            print(f"  ✓ {jid}: readings inserted")

        print(f"\nDone. {total} traffic readings across {len(junction_ids)} junctions.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate traffic data")
    parser.add_argument("--days", type=int, default=7, help="Days of history to generate")
    parser.add_argument("--junctions", nargs="+", default=JUNCTION_IDS)
    parser.add_argument("--interval", type=int, default=15, help="Reading interval in minutes")
    args = parser.parse_args()

    print(f"Simulating {args.days} days of data for {args.junctions}...")
    simulate(args.days, args.junctions, args.interval)
