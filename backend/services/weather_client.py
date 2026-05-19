"""
Open-Meteo API client.

Fetches hourly weather variables needed for the solar and wind power models.
No API key required. Rate limit: 10,000 calls/day on the free tier.

Two endpoints:
  - /v1/forecast  (api.open-meteo.com)   — current + up to ~2 days past
  - /v1/archive   (archive-api.open-meteo.com) — historical, up to yesterday
"""

import asyncio
from datetime import date, timedelta

import httpx

from backend.config import settings


FORECAST_BASE = "https://api.open-meteo.com/v1"
ARCHIVE_BASE = "https://archive-api.open-meteo.com/v1"

# The forecast endpoint supports a small window of recent past days.
# Beyond that, use the archive endpoint.
FORECAST_LOOKBACK_DAYS = 2

HOURLY_VARIABLES = [
    "shortwave_radiation",
    "temperature_2m",
    "windspeed_10m",
    "surface_pressure",
    "cloud_cover",
]


async def _fetch(base_url: str, path: str, params: dict, timeout: float) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        for attempt in range(3):
            try:
                resp = await client.get(path, params=params)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                if attempt == 2:
                    raise RuntimeError(
                        f"Open-Meteo request failed after 3 attempts: {exc}"
                    ) from exc
                await asyncio.sleep(2 ** attempt)


async def fetch_hourly(
    start: date,
    end: date,
    lat: float = settings.site_latitude,
    lon: float = settings.site_longitude,
    tz: str = settings.site_timezone,
) -> dict:
    """Route to forecast or archive endpoint based on date recency."""
    cutoff = date.today() - timedelta(days=FORECAST_LOOKBACK_DAYS)
    use_archive = start <= cutoff

    base_url = ARCHIVE_BASE if use_archive else FORECAST_BASE
    path = "/archive" if use_archive else "/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": tz,
        "windspeed_unit": "ms",
    }

    return await _fetch(base_url, path, params, settings.openmeteo_timeout_s)


async def fetch_forecast() -> dict:
    """Next 24 hours from today."""
    today = date.today()
    return await fetch_hourly(today, today + timedelta(days=1))


async def fetch_historical(start: date, end: date) -> dict:
    return await fetch_hourly(start, end)


# Kept for backwards compatibility with code that does `async with WeatherClient()`
class WeatherClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def fetch_forecast(self) -> dict:
        return await fetch_forecast()

    async def fetch_historical(self, start: date, end: date) -> dict:
        return await fetch_historical(start, end)
