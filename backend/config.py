from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gridshift"

    # Site coordinates — Yokohama (TEPCO service territory)
    site_latitude: float = 35.44
    site_longitude: float = 139.63
    site_timezone: str = "Asia/Tokyo"

    # Solar panel parameters
    panel_efficiency: float = 0.20          # η: 20% monocrystalline
    panel_area_m2: float = 500.0            # A: installed array area
    panel_temp_coeff: float = 0.0042        # γ: power loss per °C above T_ref
    panel_temp_ref: float = 25.0            # T_ref in °C (STC)

    # Wind turbine parameters
    rotor_area_m2: float = 1963.5           # π * r² for 25m rotor radius
    power_coefficient: float = 0.40         # Cp: Betz limit is 0.593; 0.40 is realistic
    wind_rated_speed_ms: float = 12.0       # rated wind speed m/s
    wind_cutout_speed_ms: float = 25.0      # cut-out speed m/s
    wind_cutin_speed_ms: float = 3.0        # cut-in speed m/s

    # Mining rig parameters
    RIG_POWER_KW: float = 3.25             # Antminer S19 Pro nominal draw
    # FUTURE: Integrate Bitmain S19 Pro thermal efficiency curves
    # (Power draw increases ~0.5% per 1°C ambient above 25°C)
    num_rigs: int = 40                      # total rigs in the container
    grid_cap_kw: float = 50.0              # max allowed grid import kW
    min_runtime_h: float = 240.0           # minimum daily rig-hours (6h × 40 rigs)
    max_runtime_h: float = 720.0           # maximum daily rig-hours (18h × 40 rigs)

    # Optimizer cost weights
    carbon_price_jpy_per_kg: float = 5.0
    renewable_bonus: float = 8.0            # JPY reward per kWh of renewable absorbed
    min_price_floor_jpy: float = 0.5        # guard against near-zero / negative JEPX prices

    # Open-Meteo API
    openmeteo_base_url: str = "https://api.open-meteo.com/v1"
    openmeteo_timeout_s: float = 15.0


settings = Settings()
