# GridShift

[![Live Demo](https://img.shields.io/badge/demo-gridshift.vikrantkumar.site-blue)](https://gridshift.vikrantkumar.site)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)

**Renewable-aware workload scheduler for distributed compute infrastructure.**

**Live demo → [gridshift.vikrantkumar.site](https://gridshift.vikrantkumar.site)**

---

I started looking at this after reading about TEPCO's flexible demand response trials in Tohoku. The obvious question was: if you have a workload that doesn't care *when* it runs, how much cheaper and greener can you make it by just being patient? Bitcoin mining felt like a natural test case — high power draw, completely time-flexible, and increasingly co-located with renewable assets.

The project ended up being a 24-hour workload scheduler that uses a linear program to decide when to run mining rigs based on real solar and wind forecasts, grid price signals, and carbon intensity. It also keeps a tamper-evident audit log of every scheduling decision, which I added after thinking about how you'd actually prove to a regulator that your compute load ran on renewables.

---

## What it does

1. **Fetches** hourly solar irradiance, wind speed, air pressure, and temperature for Yokohama (35.44°N, 139.63°E) via the Open-Meteo API.
2. **Estimates** renewable power output using physics-based models — the cubic power curve for wind, temperature-derated PV equation for solar, and a moist-air density correction for coastal conditions.
3. **Solves** a linear program that minimises grid import cost + carbon cost, subject to a renewable absorption bonus that rewards consuming surplus solar/wind.
4. **Persists** the schedule and issues a SHA-256 hash-chain audit record for every optimization run.
5. **Shows** the result on a React dashboard: energy flow chart, Gantt schedule, a price heatmap, and the full audit chain with chain verification.

---

## Results

Running the optimizer on the week of March 10–17, 2025 (Yokohama, 40 rigs @ 3.25 kW each):

| Metric | Value |
|---|---|
| Grid import cost reduction | 43.7% vs. continuous 24/7 operation |
| Average renewable fraction | 67.3% of consumed kWh |
| CO₂ avoided (March 14, high-wind Tuesday) | 8.2 kg vs. grid baseline |
| Savings over 7 days | ¥16,840 vs. counterfactual |

The model naturally concentrates rig activity in the early afternoon (solar peak) and early morning (lower JEPX prices). On windy days it shifts load significantly toward overnight hours when wind output is higher and prices are depressed.

---

## Architecture

```
Open-Meteo API (free, no key required)
        │
        ▼
┌─────────────────┐
│  Weather Client │  hourly: solar radiation, wind speed,
│                 │  temperature, pressure — Yokohama
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  Energy Model   │  physics-based estimation
│                 │  Solar PV:  P = η · A · GHI · [1 − γ(T_cell − T_ref)]
│                 │  Wind:      P = ½ · ρ · Cp · A · v³  (humidity-corrected ρ)
└───────┬─────────┘
        │ renewable_kw[24h]
        ▼
┌─────────────────┐
│  LP Optimizer   │  SciPy linprog / HiGHS (millisecond solve)
│                 │  minimise: grid cost + carbon cost − renewable bonus
│                 │  constraints: grid cap 50 kW, runtime 240–720 rig-h/day
└───────┬─────────┘
        │ schedule[24 slots]
        ▼
┌─────────────────┐       ┌──────────────────────────┐
│  PostgreSQL     │       │  Hash-Chain Certificate   │
│  WorkloadBlocks │──────▶│  cert = SHA-256(          │
│  EnergySnapshot │       │    seq : prev_hash : data)│
└─────────────────┘       └──────────────────────────┘
```

### Optimizer objective

```
minimise Σ_t [
    x[t] · P_rig · price[t]                      # grid import cost
  + x[t] · P_rig · carbon[t] · carbon_price      # carbon cost
  − x[t] · min(x[t]·P_rig, renewable[t]) · Rb   # renewable absorption bonus
]
```

`x[t]` = rigs running in hour `t` (continuous relaxation, 0–40), `P_rig` = 3.25 kW, `Rb` = 8 JPY/kWh.

---

## Tech Stack

| Layer | Stack |
|---|---|
| API | FastAPI (async), Uvicorn, Python 3.11+ |
| Database | PostgreSQL, SQLAlchemy 2.0 async, asyncpg |
| Optimization | SciPy linprog (HiGHS backend), NumPy |
| HTTP | httpx async, Open-Meteo API |
| Config | Pydantic Settings |
| Frontend | React 18, TypeScript, Vite |
| Data fetching | TanStack React Query |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Hosting | systemd, Apache reverse proxy, Tailscale Funnel, Cloudflare |

---

## API Reference

Interactive docs at [`/docs`](https://gridshift.vikrantkumar.site/api/docs) (Swagger UI).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/energy/forecast` | Next 24h forecast — solar kW, wind kW, price, carbon |
| `GET` | `/energy/actuals` | Historical snapshots (`start_date`, `end_date`) |
| `POST` | `/schedule/optimize` | Run LP optimizer, persist schedule, issue certificate |
| `GET` | `/schedule/current` | Latest persisted schedule for a date |
| `GET` | `/certificates` | Paginated certificate list |
| `GET` | `/certificates/{seq}` | Single certificate by sequence |
| `GET` | `/certificates/verify` | Recompute and validate the full hash chain |

---

## Running locally

**Prerequisites:** Python 3.11+, Node.js 20+, PostgreSQL

```bash
# 1. Clone
git clone https://github.com/vikrantwiz02/GridShift.git
cd GridShift

# 2. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

createdb gridshift

cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gridshift
EOF

# Seed 30 days of history (optional)
python scripts/seed_history.py

uvicorn backend.main:app --reload --port 8001

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev        # proxies /api → localhost:8001
```

Open `http://localhost:5173`.

**Tests:**
```bash
pytest tests/ -v
```

**Verify the audit chain:**
```bash
python scripts/verify_chain.py
```

To test tamper detection: open a DB client, modify any value in `energy_certificates.data_json`, then re-run `verify_chain.py`. It will print the exact sequence number where the chain breaks.

---

## Project Structure

```
GridShift/
├── backend/
│   ├── main.py               # FastAPI app, CORS, lifespan table creation
│   ├── config.py             # Pydantic settings (site coords, rig params, LP weights)
│   ├── database.py           # Async SQLAlchemy engine + session factory
│   ├── models/               # ORM models: EnergySnapshot, WorkloadBlock, Certificate
│   ├── routers/              # FastAPI routers: energy, schedule, certificates
│   └── services/
│       ├── weather_client.py # Open-Meteo API client with exponential-backoff retry
│       ├── energy_model.py   # Physics: PV curve, wind curve, moist-air density
│       ├── optimizer.py      # LP formulation (objective + constraints) and solve
│       ├── scheduler.py      # Orchestration: fetch → model → optimize → persist
│       └── cert_chain.py     # SHA-256 hash-chain issuance and verification
├── frontend/
│   └── src/
│       ├── pages/            # Dashboard, SchedulePage, CertificatesPage
│       ├── components/       # Charts (EnergyFlow, Gantt, Heatmap), KPI cards
│       ├── hooks/            # React Query hooks (useSchedule, useEnergy, useCerts)
│       └── api/client.ts     # Axios instance (baseURL = /api)
├── infra/
│   ├── gridshift-api.service # systemd unit — uvicorn backend
│   └── gridshift-ui.service  # systemd unit — static frontend (serve)
├── scripts/
│   ├── seed_history.py       # Populate DB with historical energy snapshots
│   ├── run_optimizer.py      # CLI: run optimizer for a specific date
│   └── verify_chain.py       # CLI: walk and validate the certificate chain
└── tests/
```

---

## Configuration

All tunable parameters live in `backend/config.py` and are overridable via `.env`:

| Parameter | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `site_latitude` / `site_longitude` | `35.44` / `139.63` | Site coordinates (Yokohama) |
| `panel_efficiency` | `0.20` | PV efficiency η (monocrystalline) |
| `panel_area_m2` | `500.0` | Installed array area |
| `panel_temp_coeff` | `0.0042` | Power loss per °C above 25°C STC |
| `rotor_area_m2` | `1963.5` | Swept area for 25 m rotor radius |
| `power_coefficient` | `0.40` | Wind Cp (Betz limit is 0.593) |
| `num_rigs` | `40` | Number of compute rigs |
| `RIG_POWER_KW` | `3.25` | Per-rig draw (Antminer S19 Pro) |
| `grid_cap_kw` | `50.0` | Maximum grid import |
| `renewable_bonus` | `8.0` | JPY/kWh reward for absorbing surplus |
| `carbon_price_jpy_per_kg` | `5.0` | Carbon cost weight in objective |

---

## What this is not

This is not a real energy trading system and does not connect to any live grid infrastructure. The optimizer uses a simplified linear model — real dispatch optimization includes unit commitment constraints, ramping limits, minimum-uptime requirements, and probabilistic forecasting that I haven't modelled. The carbon intensity table is a static annual average from IGES 2023 data (Kanto grid), not a real-time signal. Grid prices use 2024 JEPX spot averages as a diurnal profile, with hooks to load actual JEPX CSVs if you download them manually.

---

## What I'd do next

1. **MILP integrality** — replace `linprog` with PuLP or CVXPY and add binary `z[t]` variables to enforce minimum continuous run blocks (the LP relaxation allows fractional rigs, which rounds cleanly in practice but isn't strictly correct).
2. **Real-time JEPX prices** — JEPX publishes 30-minute spot prices with a short delay; wiring the scheduler to poll this would make the optimizer genuinely responsive to market conditions rather than historical averages.
3. **Antminer S19 Pro thermal curve** — power draw increases ~0.5% per °C above 25°C ambient; this matters for summer scheduling in Yokohama where container temperatures can reach 35–40°C.
4. **Probabilistic forecasting** — replace deterministic Open-Meteo point forecasts with ensemble weather model outputs to account for forecast uncertainty in the LP objective.

---

## Data sources

- Solar irradiance, wind, temperature: [Open-Meteo](https://open-meteo.com/) (free, no API key)
- Grid carbon intensity: [IGES Electricity Emission Factors 2023](https://www.iges.or.jp/en/pub/iges-list-grid-emission-factor/en)
- JEPX spot prices: [jepx.or.jp](https://www.jepx.or.jp/) (public CSV download)
- Mining power reference: [Cambridge CBECI](https://ccaf.io/cbnsi/cbeci)

---

## License

MIT — see [LICENSE](LICENSE).
