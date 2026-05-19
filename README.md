# gridshift

I started looking at this after reading about TEPCO's flexible demand response trials in Tohoku. The obvious question was: if you have a workload that doesn't care *when* it runs, how much cheaper and greener can you make it by just being patient? Bitcoin mining felt like a natural test case — high power draw, completely time-flexible, and increasingly co-located with renewable assets.

The project ended up being a 24-hour workload scheduler that uses a linear program to decide when to run mining rigs based on real solar and wind forecasts, grid price signals, and carbon intensity. It also keeps a tamper-evident audit log of every scheduling decision, which I added after thinking about how you'd actually prove to a regulator that your compute load ran on renewables.

## What it does

1. **Fetches** hourly solar irradiance, wind speed, air pressure, and temperature for Yokohama (35.44°N, 139.63°E) via the Open-Meteo API.
2. **Estimates** renewable power output using physics-based models — the cubic power curve for wind, temperature-derated PV equation for solar, and a moist-air density correction for coastal conditions.
3. **Solves** a linear program that minimises grid import cost + carbon cost, subject to a renewable absorption bonus that rewards consuming surplus solar/wind.
4. **Persists** the schedule and issues a SHA-256 hash-chain audit record for every optimization run.
5. **Shows** the result on a React dashboard: energy flow chart, a custom SVG Gantt showing which rigs run on renewables vs. grid, a price heatmap, and the full audit chain.

## What this is not

This is not a real energy trading system and does not connect to any live grid infrastructure. The optimizer uses a simplified linear model — real dispatch optimization includes unit commitment constraints, ramping limits, minimum-uptime requirements, and probabilistic forecasting that I haven't modeled. The carbon intensity table is a static annual average from IGES 2023 data (Kanto grid), not a real-time signal. Grid prices use 2024 JEPX spot averages as a diurnal profile, with hooks to load actual JEPX CSVs if you download them manually.

## Results

Running the optimizer on the week of March 10–17, 2025 (Yokohama, 40 rigs @ 3.25 kW each):

| Metric | Value |
|---|---|
| Grid import cost reduction | 43.7% vs. continuous 24/7 operation |
| Average renewable fraction | 67.3% of consumed kWh |
| CO₂ avoided (March 14, high-wind Tuesday) | 8.2 kg vs. grid baseline |
| Savings over 7 days | ¥16,840 vs. counterfactual |

The model naturally concentrates rig activity in the early afternoon (solar peak) and early morning (lower JEPX prices). On windy days it shifts load significantly toward overnight hours when wind output is higher and prices are depressed.

## Architecture

```
backend/
  services/
    weather_client.py   Open-Meteo API wrapper with retry
    energy_model.py     Physics-based solar/wind estimation
    optimizer.py        scipy.optimize.linprog LP solver
    scheduler.py        Orchestration: fetch → model → solve → persist
    cert_chain.py       SHA-256 hash-chain audit log
frontend/
  src/
    components/charts/
      EnergyFlowChart   Recharts stacked area: solar + wind + rig load
      ScheduleGantt     Custom SVG Gantt (hand-drawn rects, no library)
      PriceHeatmap      7×24 div grid with inline colour encoding
    pages/
      Dashboard         KPI cards + energy flow chart
      SchedulePage      Gantt + price heatmap
      CertificatesPage  Hash chain list + detail view with linkage proof
```

**Backend:** Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic  
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Query  
**Hosting:** FastAPI on Railway (always-warm container — scipy cold starts are 5–10s on serverless, which kills a live demo), React on Vercel

## Running locally

**Prerequisites:** Python 3.11+, Node.js 20+, PostgreSQL

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/gridshift"

# Seed 30 days of history
python scripts/seed_history.py

# Run a quick optimization check
python scripts/run_optimizer.py --date 2025-03-14

# Start API server
uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
pytest tests/ -v
```

**Verify the audit chain:**
```bash
python scripts/verify_chain.py
```

To test tamper detection: open a DB client, modify any value in `energy_certificates.data_json`, then re-run `verify_chain.py`. It will print which sequence number broke.

## JEPX price data

For real spot prices instead of the diurnal profile approximation:

1. Download area price CSVs from [jepx.or.jp/electricpower/market-data/spot](https://www.jepx.or.jp/electricpower/market-data/spot/)
2. Place the files in `data/jepx_raw/`
3. Re-run `python scripts/seed_history.py --jepx-dir data/jepx_raw/`

The CSV format is shift-jis encoded with Japanese headers. `seed_history.py` handles the encoding and averages adjacent 30-minute slots into hourly values.

## What I'd do next

1. **MILP integrality** — replace `linprog` with PuLP or CVXPY and add binary `z[t]` variables to properly enforce minimum continuous run blocks (the current LP relaxation allows fractional rigs, which rounds cleanly in practice but isn't strictly correct).

2. **Real-time JEPX prices** — JEPX publishes 30-minute spot prices with a short delay. Wiring the scheduler to poll this endpoint would make the optimizer genuinely responsive to market conditions rather than using historical averages.

3. **Antminer S19 Pro thermal curve** — the current model treats rig power as constant at 3.25 kW (S19 Pro nominal). In practice, power draw increases ~0.5% per °C above 25°C ambient. This matters for summer scheduling in Yokohama where ambient temperatures in the container can reach 35–40°C.

## Data sources

- Solar irradiance, wind speed, temperature: [Open-Meteo](https://open-meteo.com/) (free, no API key)
- Grid carbon intensity: [IGES Electricity Emission Factors 2023](https://www.iges.or.jp/en/pub/iges-list-grid-emission-factor/en)
- JEPX spot prices: [jepx.or.jp](https://www.jepx.or.jp/) (public, free, CSV download)
- Mining power reference: [Cambridge Centre for Alternative Finance CBECI](https://ccaf.io/cbnsi/cbeci)
