from datetime import datetime

from pydantic import BaseModel


class EnergySnapshotOut(BaseModel):
    id: int
    timestamp: datetime
    solar_kw: float
    wind_kw: float
    temperature_c: float
    wind_speed_ms: float
    shortwave_radiation_wm2: float
    price_jpy_kwh: float
    carbon_g_kwh: float

    model_config = {"from_attributes": True}


class ForecastPoint(BaseModel):
    timestamp: datetime
    solar_kw: float
    wind_kw: float
    total_renewable_kw: float
    price_jpy_kwh: float
    carbon_g_kwh: float
