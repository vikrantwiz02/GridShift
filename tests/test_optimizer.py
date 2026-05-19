"""
Unit tests for the LP optimizer.

We use synthetic inputs to verify:
  - The LP produces a feasible solution (no solver errors)
  - The schedule respects supply and runtime constraints
  - The renewable bonus actually causes the optimizer to prefer high-renewable slots
  - Near-zero JEPX prices are handled correctly
"""

import pytest

from backend.services.optimizer import OptimizerInput, OptimizerResult, run


def make_input(**overrides) -> OptimizerInput:
    defaults = dict(
        horizon_h=24,
        dt=1.0,
        renewable_kw=[50.0] * 24,
        grid_price_jpy=[15.0] * 24,
        carbon_g_kwh=[480.0] * 24,
        rig_power_kw=3.25,
        num_rigs=40,
        min_runtime_h=6.0,
        max_runtime_h=20.0,
        grid_cap_kw=50.0,
    )
    defaults.update(overrides)
    return OptimizerInput(**defaults)


class TestFeasibility:
    def test_uniform_inputs_solves(self):
        """Constant renewable and price — LP must find a feasible solution."""
        result = run(make_input())
        assert isinstance(result, OptimizerResult)
        assert len(result.schedule) == 24

    def test_zero_renewable_solves(self):
        """No renewable available — optimizer falls back to full grid import."""
        result = run(make_input(renewable_kw=[0.0] * 24))
        assert result is not None
        total_runtime = sum(result.schedule)
        assert total_runtime > 0

    def test_very_high_price_minimises_runtime(self):
        """Extremely expensive grid should push schedule toward minimum runtime."""
        cheap = run(make_input(grid_price_jpy=[5.0] * 24))
        expensive = run(make_input(grid_price_jpy=[500.0] * 24))
        assert sum(expensive.schedule) <= sum(cheap.schedule) + 0.01


class TestConstraints:
    def test_respects_min_runtime(self):
        """Total rig-hours must be >= min_runtime_h."""
        inp = make_input(min_runtime_h=8.0, max_runtime_h=18.0)
        result = run(inp)
        total_rig_hours = sum(result.schedule) * inp.dt
        assert total_rig_hours >= inp.min_runtime_h - 0.01

    def test_respects_max_runtime(self):
        """Total rig-hours must be <= max_runtime_h."""
        inp = make_input(min_runtime_h=4.0, max_runtime_h=10.0)
        result = run(inp)
        total_rig_hours = sum(result.schedule) * inp.dt
        assert total_rig_hours <= inp.max_runtime_h + 0.01

    def test_supply_constraint(self):
        """Load in each slot must not exceed renewable + grid cap."""
        cap = 30.0
        ren = [20.0] * 24
        inp = make_input(renewable_kw=ren, grid_cap_kw=cap, rig_power_kw=3.25, num_rigs=40)
        result = run(inp)
        for t, x in enumerate(result.schedule):
            load = x * inp.rig_power_kw
            assert load <= ren[t] + cap + 0.01, f"Slot {t}: load {load:.2f} > {ren[t] + cap:.2f}"

    def test_rig_count_bound(self):
        """x[t] must never exceed num_rigs."""
        inp = make_input(num_rigs=10)
        result = run(inp)
        for t, x in enumerate(result.schedule):
            assert x <= inp.num_rigs + 0.01, f"Slot {t}: {x:.2f} > {inp.num_rigs}"


class TestRenewablePreference:
    def test_prefers_high_renewable_slots(self):
        """
        Given two groups of hours — one with abundant renewable, one without —
        the scheduler should assign more rig-time to the high-renewable slots.
        """
        renewable = [0.0] * 12 + [200.0] * 12   # first half has no renewable
        price = [15.0] * 24                       # uniform price

        result = run(make_input(renewable_kw=renewable, grid_price_jpy=price))

        low_ren_total = sum(result.schedule[:12])
        high_ren_total = sum(result.schedule[12:])
        assert high_ren_total >= low_ren_total, (
            f"Expected more rigs during high-renewable slots: "
            f"low={low_ren_total:.2f}, high={high_ren_total:.2f}"
        )

    def test_prefers_low_price_slots(self):
        """Given uniform renewable, optimizer should concentrate on cheapest hours."""
        price = [20.0] * 12 + [5.0] * 12
        result = run(make_input(grid_price_jpy=price, renewable_kw=[0.0] * 24))

        cheap_total = sum(result.schedule[12:])
        expensive_total = sum(result.schedule[:12])
        assert cheap_total >= expensive_total


class TestPriceFloor:
    def test_near_zero_price_handled(self):
        """JEPX can drop near zero — the price floor should prevent distortion."""
        result = run(make_input(grid_price_jpy=[0.01] * 24))
        assert result is not None
        assert len(result.schedule) == 24

    def test_negative_price_handled(self):
        """Negative prices (rare but possible on JEPX) must not crash the solver."""
        result = run(make_input(grid_price_jpy=[-5.0] * 24))
        assert result is not None


class TestMetrics:
    def test_renewable_fraction_in_range(self):
        result = run(make_input())
        assert 0.0 <= result.renewable_fraction <= 1.0

    def test_savings_non_negative_when_optimizing(self):
        """Optimizer should never produce a plan that costs more than running flat-out."""
        result = run(make_input())
        assert result.savings_jpy >= -0.01  # allow tiny float error

    def test_co2_non_negative(self):
        result = run(make_input())
        assert result.total_co2_kg >= 0.0
