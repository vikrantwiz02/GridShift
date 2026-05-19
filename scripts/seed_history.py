#!/usr/bin/env python3
"""
Backfill 30 days of Open-Meteo data into the database.

Usage:
    python scripts/seed_history.py
    python scripts/seed_history.py --days 7
    python scripts/seed_history.py --start 2025-03-01 --end 2025-03-31

JEPX price data:
    Download area price CSVs from https://www.jepx.jp/electricpower/market-data/spot/
    Place the raw CSV in data/jepx_raw/ and this script will parse and incorporate
    the actual spot prices instead of the diurnal profile approximation.
"""

import argparse
import asyncio
import csv
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.database import AsyncSessionLocal, Base, engine
from backend.models.energy import EnergySnapshot
from backend.services import energy_model
from backend.services.weather_client import WeatherClient
from backend.services.scheduler import JEPX_DIURNAL_PROFILE, CARBON_INTENSITY_PROFILE


def load_jepx_prices(csv_path: Path, target_date: date) -> list[float] | None:
    """
    Parse a JEPX area price CSV and return 24 hourly prices for the given date.

    JEPX exports 30-minute slots; we average adjacent pairs to get hourly values.
    The CSV format is messy (shift-jis encoding, Japanese headers) — this is the
    data wrangling reality of working with Japanese electricity market data.

    Returns None if the file doesn't cover the target date.
    """
    if not csv_path.exists():
        return None

    date_str = target_date.strftime("%Y/%m/%d")
    prices_30min = []
    try:
        with open(csv_path, encoding="shift_jis", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0] != date_str:
                    continue
                try:
                    # Kanto area price is typically column 5 (0-indexed)
                    prices_30min.append(float(row[5]))
                except (IndexError, ValueError):
                    continue
    except Exception:
        return None

    if len(prices_30min) < 48:
        return None

    # Average adjacent 30-min slots into hourly values
    return [
        (prices_30min[i * 2] + prices_30min[i * 2 + 1]) / 2.0
        for i in range(24)
    ]


async def seed_date(session, target_date: date, jepx_dir: Path | None) -> int:
    from sqlalchemy import select, delete

    # Remove existing rows for this date to allow re-seeding
    await session.execute(
        delete(EnergySnapshot).where(
            EnergySnapshot.timestamp >= datetime.combine(target_date, datetime.min.time()),
            EnergySnapshot.timestamp <= datetime.combine(target_date, datetime.max.time()),
        )
    )

    async with WeatherClient() as wc:
        raw = await wc.fetch_historical(target_date, target_date)

    parsed = energy_model.parse_openmeteo_response(raw)

    # Try to load real JEPX prices from local CSV
    jepx_prices = None
    if jepx_dir:
        for fname in jepx_dir.glob("*.csv"):
            jepx_prices = load_jepx_prices(fname, target_date)
            if jepx_prices:
                break

    inserted = 0
    for i, (ts_str, weather) in enumerate(parsed[:24]):
        power = energy_model.estimate_power(weather)
        price = jepx_prices[i] if jepx_prices else JEPX_DIURNAL_PROFILE[i % 24]
        snap = EnergySnapshot(
            timestamp=datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc),
            solar_kw=round(power.solar_kw, 3),
            wind_kw=round(power.wind_kw, 3),
            temperature_c=round(weather.temperature_c, 2),
            wind_speed_ms=round(weather.wind_speed_ms, 2),
            shortwave_radiation_wm2=round(weather.shortwave_radiation_wm2, 1),
            surface_pressure_hpa=round(weather.surface_pressure_hpa, 2),
            price_jpy_kwh=round(price, 4),
            carbon_g_kwh=float(CARBON_INTENSITY_PROFILE[i % 24]),
        )
        session.add(snap)
        inserted += 1

    await session.commit()
    return inserted


async def main():
    parser = argparse.ArgumentParser(description="Seed energy snapshot history")
    parser.add_argument("--days", type=int, default=30, help="Number of days to backfill")
    parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD (defaults to yesterday)")
    parser.add_argument("--jepx-dir", type=str, help="Directory containing JEPX CSV files")
    args = parser.parse_args()

    end_date = date.fromisoformat(args.end) if args.end else date.today() - timedelta(days=1)
    if args.start:
        start_date = date.fromisoformat(args.start)
    else:
        start_date = end_date - timedelta(days=args.days - 1)

    jepx_dir = Path(args.jepx_dir) if args.jepx_dir else None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    current = start_date
    total = 0
    async with AsyncSessionLocal() as session:
        while current <= end_date:
            try:
                count = await seed_date(session, current, jepx_dir)
                print(f"  {current.isoformat()}: {count} snapshots")
                total += count
            except Exception as exc:
                print(f"  {current.isoformat()}: FAILED — {exc}", file=sys.stderr)
            current += timedelta(days=1)

    print(f"\nDone. {total} total snapshots inserted.")


if __name__ == "__main__":
    asyncio.run(main())
