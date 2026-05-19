from datetime import datetime

from sqlalchemy import DateTime, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class EnergySnapshot(Base):
    __tablename__ = "energy_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    solar_kw: Mapped[float] = mapped_column(Float, nullable=False)
    wind_kw: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_ms: Mapped[float] = mapped_column(Float, nullable=False)
    shortwave_radiation_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    surface_pressure_hpa: Mapped[float] = mapped_column(Float, nullable=False)
    price_jpy_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    carbon_g_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=480.0)

    __table_args__ = (
        Index("ix_energy_snapshots_timestamp", "timestamp"),
    )
