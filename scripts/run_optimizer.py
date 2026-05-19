#!/usr/bin/env python3
"""
Run the LP optimizer for a given date and print the result to stdout.

Usage:
    python scripts/run_optimizer.py
    python scripts/run_optimizer.py --date 2025-03-14
    python scripts/run_optimizer.py --date 2025-03-14 --json
"""

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import AsyncSessionLocal, Base, engine
from backend.services import scheduler


async def main():
    parser = argparse.ArgumentParser(description="GridShift LP optimizer CLI")
    parser.add_argument(
        "--date",
        type=str,
        default=date.today().isoformat(),
        help="Target date (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output result as JSON",
    )
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result, blocks = await scheduler.run_optimization(session, target_date)

    if args.as_json:
        print(json.dumps({
            "date": args.date,
            "total_cost_jpy": result.total_cost_jpy,
            "counterfactual_cost_jpy": result.counterfactual_cost_jpy,
            "savings_jpy": result.savings_jpy,
            "renewable_fraction": result.renewable_fraction,
            "total_co2_kg": result.total_co2_kg,
            "schedule": result.schedule,
        }, indent=2))
        return

    savings_pct = (result.savings_jpy / result.counterfactual_cost_jpy * 100
                   if result.counterfactual_cost_jpy > 0 else 0)
    ren_pct = result.renewable_fraction * 100

    print(f"\nGridShift optimizer — {args.date}")
    print("=" * 50)
    print(f"  Grid import cost:      ¥{result.total_cost_jpy:>10,.2f}")
    print(f"  Counterfactual cost:   ¥{result.counterfactual_cost_jpy:>10,.2f}")
    print(f"  Savings:               ¥{result.savings_jpy:>10,.2f}  ({savings_pct:.1f}%)")
    print(f"  Renewable fraction:    {ren_pct:>9.1f}%")
    print(f"  Total CO₂:             {result.total_co2_kg:>9.3f} kg")
    print()
    print("  Hourly schedule (rigs on / renewable kW available):")
    for i, x in enumerate(result.schedule):
        bar_len = int(x / 40 * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {i:02d}:00  [{bar}]  {x:5.1f} rigs")


if __name__ == "__main__":
    asyncio.run(main())
