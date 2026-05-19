from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine
from backend.routers import certificates, energy, schedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="GridShift API",
    description="Renewable-aware workload scheduler for distributed compute",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(energy.router, prefix="/energy", tags=["energy"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(certificates.router, prefix="/certificates", tags=["certificates"])


@app.get("/health")
async def health():
    return {"status": "ok"}
