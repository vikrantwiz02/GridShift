from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.energy import EnergySnapshot
from backend.schemas.energy import EnergySnapshotOut, ForecastPoint
from backend.services import energy_model
from backend.services.weather_client import WeatherClient

router = APIRouter()


@router.get("/forecast", response_model=list[ForecastPoint])
async def get_forecast(db: AsyncSession = Depends(get_db)):
    """Next 24-hour renewable power forecast based on Open-Meteo data."""
    try:
        async with WeatherClient() as wc:
            raw = await wc.fetch_forecast()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    parsed = energy_model.parse_openmeteo_response(raw)
    result = []
    for i, (ts_str, weather) in enumerate(parsed[:24]):
        power = energy_model.estimate_power(weather)
        result.append(
            ForecastPoint(
                timestamp=datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc),
                solar_kw=round(power.solar_kw, 3),
                wind_kw=round(power.wind_kw, 3),
                total_renewable_kw=round(power.solar_kw + power.wind_kw, 3),
                price_jpy_kwh=0.0,   # forecast prices not available via Open-Meteo
                carbon_g_kwh=480.0,
            )
        )
    return result


@router.get("/actuals", response_model=list[EnergySnapshotOut])
async def get_actuals(
    start_date: date = date.today(),
    end_date: date = date.today(),
    db: AsyncSession = Depends(get_db),
):
    """Historical energy snapshots from DB."""
    if (end_date - start_date).days > 31:
        raise HTTPException(status_code=400, detail="Date range exceeds 31 days")

    stmt = (
        select(EnergySnapshot)
        .where(
            EnergySnapshot.timestamp >= datetime.combine(start_date, datetime.min.time()),
            EnergySnapshot.timestamp <= datetime.combine(end_date, datetime.max.time()),
        )
        .order_by(EnergySnapshot.timestamp)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows
