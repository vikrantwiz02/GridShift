"""
Orchestrates the full optimization pipeline for a given date:
  1. Fetch weather forecast from Open-Meteo
  2. Estimate renewable power via energy_model
  3. Build OptimizerInput from energy + price data
  4. Run LP solver
  5. Persist WorkloadBlocks to DB
  6. Issue an audit certificate

Price data: in production, pull from the JEPX API. For the prototype we use
a static diurnal price profile derived from 2024 JEPX spot averages.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.energy import EnergySnapshot
from backend.models.schedule import WorkloadBlock
from backend.services import cert_chain, energy_model, optimizer
from backend.services.weather_client import WeatherClient


# 2024 JEPX hourly average spot prices (JPY/kWh), offset 0 = midnight JST.
# Source: JEPX area price data, Kanto area, annual average.
JEPX_DIURNAL_PROFILE = [
    8.2, 7.8, 7.4, 7.1, 7.3, 8.5,
    11.2, 14.7, 16.3, 15.8, 14.1, 13.2,
    12.9, 13.1, 13.8, 14.5, 16.0, 18.7,
    19.4, 17.3, 15.1, 13.2, 11.0, 9.3,
]

# Kanto grid carbon intensity by hour (g CO2/kWh), derived from IGES 2023 data.
# Drops slightly during midday when solar penetration is highest on the grid.
CARBON_INTENSITY_PROFILE = [
    495, 498, 502, 505, 503, 497,
    488, 475, 462, 450, 445, 442,
    440, 443, 448, 455, 462, 470,
    478, 482, 487, 490, 493, 496,
]


async def _get_or_fetch_snapshots(
    session: AsyncSession,
    target_date: date,
) -> list[EnergySnapshot]:
    """Return DB rows for the date if they exist, otherwise fetch and persist."""
    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    stmt = (
        select(EnergySnapshot)
        .where(EnergySnapshot.timestamp >= day_start, EnergySnapshot.timestamp < day_end)
        .order_by(EnergySnapshot.timestamp)
    )
    rows = (await session.execute(stmt)).scalars().all()
    if len(rows) >= 24:
        return list(rows)

    async with WeatherClient() as wc:
        raw = await wc.fetch_historical(target_date, target_date)

    parsed = energy_model.parse_openmeteo_response(raw)
    new_rows = []
    for i, (ts_str, weather) in enumerate(parsed[:24]):
        power = energy_model.estimate_power(weather)
        snap = EnergySnapshot(
            timestamp=datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc),
            solar_kw=round(power.solar_kw, 3),
            wind_kw=round(power.wind_kw, 3),
            temperature_c=round(weather.temperature_c, 2),
            wind_speed_ms=round(weather.wind_speed_ms, 2),
            shortwave_radiation_wm2=round(weather.shortwave_radiation_wm2, 1),
            surface_pressure_hpa=round(weather.surface_pressure_hpa, 2),
            price_jpy_kwh=JEPX_DIURNAL_PROFILE[i % 24],
            carbon_g_kwh=float(CARBON_INTENSITY_PROFILE[i % 24]),
        )
        session.add(snap)
        new_rows.append(snap)

    await session.commit()
    return new_rows


async def run_optimization(
    session: AsyncSession,
    target_date: date,
) -> tuple[optimizer.OptimizerResult, list[WorkloadBlock]]:
    """Run the LP and persist results. Issues an audit certificate on success."""
    snapshots = await _get_or_fetch_snapshots(session, target_date)
    hours = snapshots[:24]

    inp = optimizer.OptimizerInput(
        horizon_h=len(hours),
        dt=1.0,
        renewable_kw=[s.solar_kw + s.wind_kw for s in hours],
        grid_price_jpy=[s.price_jpy_kwh for s in hours],
        carbon_g_kwh=[s.carbon_g_kwh for s in hours],
        rig_power_kw=settings.RIG_POWER_KW,
        num_rigs=settings.num_rigs,
        min_runtime_h=settings.min_runtime_h,
        max_runtime_h=settings.max_runtime_h,
        grid_cap_kw=settings.grid_cap_kw,
    )

    result = optimizer.run(inp)

    # Remove any previous schedule for this date before persisting new one
    await session.execute(
        delete(WorkloadBlock).where(WorkloadBlock.date == target_date.isoformat())
    )

    blocks = []
    now = datetime.now(tz=timezone.utc)
    for t, x in enumerate(result.schedule):
        renewable_available = inp.renewable_kw[t]
        load_kw = x * settings.RIG_POWER_KW
        grid_import = max(load_kw - renewable_available, 0.0)

        block = WorkloadBlock(
            created_at=now,
            date=target_date.isoformat(),
            slot_index=t,
            rigs_scheduled=round(x, 3),
            load_kw=round(load_kw, 3),
            renewable_kw_available=round(renewable_available, 3),
            price_jpy_kwh=inp.grid_price_jpy[t],
            grid_import_kw=round(grid_import, 3),
            status="scheduled",
        )
        session.add(block)
        blocks.append(block)

    await session.flush()

    payload = {
        "date": target_date.isoformat(),
        "total_cost_jpy": result.total_cost_jpy,
        "counterfactual_cost_jpy": result.counterfactual_cost_jpy,
        "savings_jpy": result.savings_jpy,
        "renewable_fraction": result.renewable_fraction,
        "total_co2_kg": result.total_co2_kg,
    }
    await cert_chain.issue_certificate(session, payload)

    return result, blocks
