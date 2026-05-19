"""
Linear program for renewable-aware workload scheduling.

Decision variable: x[t] — number of rigs running in hour t ∈ [0, num_rigs].
LP relaxation (continuous x) is sufficient for 1-hour dispatch horizons.
MILP (integer x) would handle minimum-run-duration constraints more cleanly
but requires PuLP or CVXPY and adds ~5s solve time; left as future work.

Objective (minimise):
  Σ_t [ x[t] * rig_kw * price[t] * dt          # grid import cost
       + x[t] * rig_kw * carbon[t] * dt * cp    # carbon cost
       - x[t] * min(x[t]*rig_kw, ren[t]) * rb ] # reward for absorbing surplus

The renewable bonus term is what makes this scheduler "chase" surplus energy
rather than simply running whenever prices are low. It directly models AEX's
flexible-demand-creation concept.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from backend.config import settings


@dataclass
class OptimizerInput:
    horizon_h: int
    dt: float                        # time-step size in hours
    renewable_kw: list[float]        # available renewable power each slot
    grid_price_jpy: list[float]      # grid electricity price per slot (JPY/kWh)
    carbon_g_kwh: list[float]        # grid carbon intensity (g CO2/kWh)
    rig_power_kw: float
    num_rigs: int
    min_runtime_h: float             # minimum total rig-on hours in the horizon
    max_runtime_h: float
    grid_cap_kw: float


@dataclass
class OptimizerResult:
    schedule: list[float]            # x[t] values
    total_cost_jpy: float
    counterfactual_cost_jpy: float   # cost if rigs ran continuously at full load
    savings_jpy: float
    total_co2_kg: float
    counterfactual_co2_kg: float     # CO2 if rigs ran continuously at full load
    renewable_fraction: float        # fraction of total kWh sourced from renewables


def run(inp: OptimizerInput) -> OptimizerResult:
    n = inp.horizon_h
    dt = inp.dt
    rk = inp.rig_power_kw
    N = inp.num_rigs
    cp = settings.carbon_price_jpy_per_kg / 1000.0  # convert to JPY per g CO2
    rb = settings.renewable_bonus

    # Clamp prices to avoid near-zero/negative JEPX values distorting the model.
    # When price ≈ 0, the grid cost term vanishes and the renewable bonus alone
    # governs, which naturally pushes x[t] to its upper bound — correct behaviour.
    price = [max(p, settings.min_price_floor_jpy) for p in inp.grid_price_jpy]
    carbon = inp.carbon_g_kwh
    ren = inp.renewable_kw

    # Build cost vector: one coefficient per decision variable x[t].
    # scipy.optimize.linprog minimises c @ x, so the renewable bonus enters as negative.
    c = np.zeros(n)
    for t in range(n):
        grid_cost = rk * price[t] * dt
        carbon_cost = rk * carbon[t] * dt * cp
        # Renewable absorption: reward is proportional to the lesser of load and supply.
        # Since x[t] is continuous, we approximate min(x*rk, ren[t]) ≈ ren[t] when
        # ren[t] > x[t]*rk (surplus case) and x[t]*rk otherwise. We use ren[t]/N as a
        # per-rig approximation — conservative but keeps the LP linear.
        ren_per_rig = ren[t] / N if N > 0 else 0.0
        renewable_reward = min(rk, ren_per_rig) * rb
        c[t] = grid_cost + carbon_cost - renewable_reward

    # Inequality constraints: A_ub @ x <= b_ub
    # 1. Load must not exceed renewable supply + grid cap:
    #    x[t] * rk <= ren[t] + grid_cap   →  rk * x[t] <= ren[t] + cap
    A_ub = np.diag([rk] * n)
    b_ub = np.array([ren[t] + inp.grid_cap_kw for t in range(n)])

    # Equality-like constraints via two inequalities for total runtime:
    # min_runtime <= sum(x[t]) * dt <= max_runtime
    # Σ x[t] * dt >= min  →  -Σ x[t] * dt <= -min
    # Σ x[t] * dt <= max
    runtime_row = np.ones((1, n)) * dt
    A_ub = np.vstack([A_ub, -runtime_row, runtime_row])
    b_ub = np.append(b_ub, [-inp.min_runtime_h, inp.max_runtime_h])

    bounds = [(0.0, float(N)) for _ in range(n)]

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

    if result.status not in (0, 1):
        raise RuntimeError(f"LP solver failed: {result.message}")

    x = result.x

    # Compute summary statistics
    total_kwh = sum(x[t] * rk * dt for t in range(n))
    renewable_kwh = sum(min(x[t] * rk, ren[t]) * dt for t in range(n))
    total_cost = sum(x[t] * rk * max(price[t], 0.0) * dt for t in range(n))
    total_co2_g = sum(x[t] * rk * carbon[t] * dt for t in range(n))

    counterfactual_cost = sum(N * rk * max(price[t], 0.0) * dt for t in range(n))
    counterfactual_co2_g = sum(N * rk * carbon[t] * dt for t in range(n))

    return OptimizerResult(
        schedule=x.tolist(),
        total_cost_jpy=round(total_cost, 2),
        counterfactual_cost_jpy=round(counterfactual_cost, 2),
        savings_jpy=round(counterfactual_cost - total_cost, 2),
        total_co2_kg=round(total_co2_g / 1000.0, 3),
        counterfactual_co2_kg=round(counterfactual_co2_g / 1000.0, 3),
        renewable_fraction=round(renewable_kwh / total_kwh, 4) if total_kwh > 0 else 0.0,
    )
