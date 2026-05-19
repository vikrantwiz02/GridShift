from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class WorkloadBlock(Base):
    __tablename__ = "workload_blocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–23 (hourly)
    rigs_scheduled: Mapped[float] = mapped_column(Float, nullable=False)
    load_kw: Mapped[float] = mapped_column(Float, nullable=False)
    renewable_kw_available: Mapped[float] = mapped_column(Float, nullable=False)
    price_jpy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    grid_import_kw: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
