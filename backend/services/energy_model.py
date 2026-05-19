"""
Physics-based solar and wind power estimator.

Solar model: standard PV performance equation with temperature derating.
Wind model: cubic power curve with density correction for humidity and pressure.

Inputs come from Open-Meteo hourly data. Parameters are in config.py so they
can be tuned without touching this file.
"""

import math
from dataclasses import dataclass

from backend.config import settings


# Specific gas constant for dry air (J / kg·K)
R_DRY = 287.05
# Ratio of molar masses (water vapour / dry air)
MV_MA_RATIO = 0.622


@dataclass
class HourlyWeather:
    shortwave_radiation_wm2: float   # GHI in W/m²
    temperature_c: float
    wind_speed_ms: float
    surface_pressure_hpa: float
    cloudcover_pct: float = 0.0


@dataclass
class HourlyPower:
    solar_kw: float
    wind_kw: float
    air_density: float               # kg/m³ — kept for diagnostics


def air_density(temp_c: float, pressure_hpa: float) -> float:
    """
    Compute moist air density using the ideal gas law with humidity correction.

    Even small density changes matter at scale: a 2% reduction in ρ translates
    directly to a 2% reduction in wind power output per hour. Yokohama's coastal
    humidity makes this correction non-trivial in summer months.

    Uses the Magnus formula for saturation vapour pressure.
    """
    temp_k = temp_c + 273.15
    pressure_pa = pressure_hpa * 100.0

    # Saturation vapour pressure (Magnus formula, Pa)
    e_sat = 611.2 * math.exp(17.67 * temp_c / (temp_c + 243.5))

    # Assume 60% relative humidity as a conservative coastal default
    # Actual RH data could be pulled from Open-Meteo if needed
    rh = 0.60
    e_actual = rh * e_sat

    # Virtual temperature approximation for moist air
    rho = (pressure_pa - 0.378 * e_actual) / (R_DRY * temp_k)
    return rho


def solar_power_kw(weather: HourlyWeather) -> float:
    """
    Estimate PV array output in kW.

    P_pv = η × A × GHI × [1 − γ × (T_cell − T_ref)]

    T_cell is approximated as T_air + 25°C (NOCT correction at moderate irradiance).
    Below 10 W/m² (night / deep overcast) we return 0 to avoid floating-point noise.
    """
    ghi = weather.shortwave_radiation_wm2
    if ghi < 10.0:
        return 0.0

    t_cell = weather.temperature_c + 25.0
    derating = 1.0 - settings.panel_temp_coeff * (t_cell - settings.panel_temp_ref)
    derating = max(derating, 0.5)  # never derate below 50% of STC

    power_w = settings.panel_efficiency * settings.panel_area_m2 * ghi * derating
    return power_w / 1000.0


def wind_power_kw(weather: HourlyWeather) -> float:
    """
    Estimate wind turbine output in kW using the cubic power curve.

    P_wind = ½ × ρ × Cp × A × v³

    The cubic relationship means a 10% increase in wind speed yields a 33%
    increase in power — which is why the optimizer strongly prefers windy slots.
    Output is clipped at rated power and zeroed below cut-in / above cut-out.
    """
    v = weather.wind_speed_ms

    if v < settings.wind_cutin_speed_ms or v > settings.wind_cutout_speed_ms:
        return 0.0

    rho = air_density(weather.temperature_c, weather.surface_pressure_hpa)
    raw_w = 0.5 * rho * settings.power_coefficient * settings.rotor_area_m2 * (v ** 3)

    # Rated power = ½ρCpAv_rated³ at reference density (1.225 kg/m³)
    rated_w = (
        0.5 * 1.225 * settings.power_coefficient
        * settings.rotor_area_m2
        * (settings.wind_rated_speed_ms ** 3)
    )
    return min(raw_w, rated_w) / 1000.0


def estimate_power(weather: HourlyWeather) -> HourlyPower:
    rho = air_density(weather.temperature_c, weather.surface_pressure_hpa)
    return HourlyPower(
        solar_kw=solar_power_kw(weather),
        wind_kw=wind_power_kw(weather),
        air_density=rho,
    )


def parse_openmeteo_response(data: dict) -> list[tuple]:
    """
    Convert Open-Meteo JSON into a list of (timestamp_str, HourlyWeather) tuples.
    """
    hourly = data["hourly"]
    times = hourly["time"]
    results = []
    for i, ts in enumerate(times):
        w = HourlyWeather(
            shortwave_radiation_wm2=hourly["shortwave_radiation"][i] or 0.0,
            temperature_c=hourly["temperature_2m"][i] or 0.0,
            wind_speed_ms=hourly["windspeed_10m"][i] or 0.0,
            surface_pressure_hpa=hourly["surface_pressure"][i] or 1013.25,
            cloudcover_pct=hourly.get("cloud_cover", hourly.get("cloudcover", [0.0] * len(times)))[i] or 0.0,
        )
        results.append((ts, w))
    return results
