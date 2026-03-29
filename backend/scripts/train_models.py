"""
One-shot model training script.
Run after simulate_data.py to train models on generated data.

Usage:
    python scripts/train_models.py --days 7
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
from app.db import SessionLocal
from app.ml.trainer import train_all_junctions

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print(f"Training models on last {args.days} days of data...")
        results = train_all_junctions(db, days=args.days)
        for r in results:
            status = r.get("status")
            jid = r.get("junction_id")
            if status == "trained":
                print(f"  ✓ {jid}: trained on {r['samples']} samples")
            else:
                print(f"  ✗ {jid}: {r.get('reason')}")
    finally:
        db.close()
