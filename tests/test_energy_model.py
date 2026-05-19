"""
Unit tests for physics-based energy estimation.

These tests use known-good inputs to verify the model produces physically
plausible outputs. We don't test for exact values because the physics equations
have floating-point sensitivity — we test that outputs are in the right order
of magnitude and obey expected monotonic relationships.
"""

import math
import pytest

from backend.services.energy_model import (
    HourlyWeather,
    air_density,
    estimate_power,
    solar_power_kw,
    wind_power_kw,
)


class TestAirDensity:
    def test_standard_conditions(self):
        """At STP (0°C, 1013.25 hPa), density should be close to 1.29 kg/m³."""
        rho = air_density(temp_c=0.0, pressure_hpa=1013.25)
        assert 1.20 < rho < 1.35, f"Expected ~1.29, got {rho}"

    def test_hot_day_lower_density(self):
        """Warmer air is less dense — should be lower than cold air density."""
        rho_cold = air_density(temp_c=5.0, pressure_hpa=1013.25)
        rho_warm = air_density(temp_c=35.0, pressure_hpa=1013.25)
        assert rho_warm < rho_cold

    def test_high_pressure_denser(self):
        """Higher pressure = higher density at same temperature."""
        rho_lo = air_density(temp_c=20.0, pressure_hpa=990.0)
        rho_hi = air_density(temp_c=20.0, pressure_hpa=1030.0)
        assert rho_hi > rho_lo

    def test_yokohama_summer(self):
        """Typical Yokohama July conditions: ~28°C, ~1006 hPa. Density ~1.17."""
        rho = air_density(temp_c=28.0, pressure_hpa=1006.0)
        assert 1.10 < rho < 1.25


class TestSolarPower:
    def test_night_returns_zero(self):
        """No irradiance at night."""
        w = HourlyWeather(
            shortwave_radiation_wm2=0.0,
            temperature_c=20.0,
            wind_speed_ms=3.0,
            surface_pressure_hpa=1013.0,
        )
        assert solar_power_kw(w) == 0.0

    def test_clear_midday_reasonable_output(self):
        """800 W/m² (clear summer day) should produce ~60–90 kW on a 500m² array."""
        w = HourlyWeather(
            shortwave_radiation_wm2=800.0,
            temperature_c=25.0,
            wind_speed_ms=3.0,
            surface_pressure_hpa=1013.0,
        )
        out = solar_power_kw(w)
        assert 50.0 < out < 120.0, f"Unexpected output: {out} kW"

    def test_temperature_derating(self):
        """Higher panel temperature should reduce output."""
        base = HourlyWeather(
            shortwave_radiation_wm2=600.0,
            temperature_c=15.0,
            wind_speed_ms=2.0,
            surface_pressure_hpa=1013.0,
        )
        hot = HourlyWeather(
            shortwave_radiation_wm2=600.0,
            temperature_c=40.0,
            wind_speed_ms=2.0,
            surface_pressure_hpa=1013.0,
        )
        assert solar_power_kw(hot) < solar_power_kw(base)

    def test_irradiance_proportionality(self):
        """Doubling irradiance should roughly double output (linear model)."""
        w1 = HourlyWeather(
            shortwave_radiation_wm2=400.0,
            temperature_c=25.0,
            wind_speed_ms=3.0,
            surface_pressure_hpa=1013.0,
        )
        w2 = HourlyWeather(
            shortwave_radiation_wm2=800.0,
            temperature_c=25.0,
            wind_speed_ms=3.0,
            surface_pressure_hpa=1013.0,
        )
        ratio = solar_power_kw(w2) / solar_power_kw(w1)
        assert 1.8 < ratio < 2.2, f"Expected ~2x, got {ratio:.2f}x"


class TestWindPower:
    def test_below_cutin_returns_zero(self):
        """Wind speed below cut-in (3 m/s) produces no power."""
        w = HourlyWeather(
            shortwave_radiation_wm2=0.0,
            temperature_c=20.0,
            wind_speed_ms=2.0,
            surface_pressure_hpa=1013.0,
        )
        assert wind_power_kw(w) == 0.0

    def test_above_cutout_returns_zero(self):
        """Wind speed above cut-out (25 m/s) — turbine is feathered."""
        w = HourlyWeather(
            shortwave_radiation_wm2=0.0,
            temperature_c=20.0,
            wind_speed_ms=30.0,
            surface_pressure_hpa=1013.0,
        )
        assert wind_power_kw(w) == 0.0

    def test_cubic_scaling(self):
        """Power scales cubically with wind speed (pre-rated region)."""
        make = lambda v: HourlyWeather(
            shortwave_radiation_wm2=0.0,
            temperature_c=15.0,
            wind_speed_ms=v,
            surface_pressure_hpa=1013.0,
        )
        p6 = wind_power_kw(make(6.0))
        p8 = wind_power_kw(make(8.0))
        # (8/6)³ ≈ 2.37; allow generous tolerance due to density correction
        ratio = p8 / p6
        assert 2.0 < ratio < 3.0, f"Expected cubic scaling ~2.37, got {ratio:.2f}"

    def test_rated_power_clipping(self):
        """Output at rated speed and above should be capped at the same value."""
        w_rated = HourlyWeather(
            shortwave_radiation_wm2=0.0,
            temperature_c=15.0,
            wind_speed_ms=12.0,
            surface_pressure_hpa=1013.0,
        )
        w_fast = HourlyWeather(
            shortwave_radiation_wm2=0.0,
            temperature_c=15.0,
            wind_speed_ms=20.0,
            surface_pressure_hpa=1013.0,
        )
        assert wind_power_kw(w_fast) <= wind_power_kw(w_rated) * 1.05


class TestEstimatePower:
    def test_returns_non_negative(self):
        for temp, wind, rad in [(5, 0, 0), (35, 15, 900), (20, 3, 300)]:
            w = HourlyWeather(
                shortwave_radiation_wm2=rad,
                temperature_c=temp,
                wind_speed_ms=wind,
                surface_pressure_hpa=1013.0,
            )
            p = estimate_power(w)
            assert p.solar_kw >= 0.0
            assert p.wind_kw >= 0.0
            assert p.air_density > 0.0
