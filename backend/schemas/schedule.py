from datetime import datetime

from pydantic import BaseModel


class WorkloadBlockOut(BaseModel):
    id: int
    created_at: datetime
    date: str
    slot_index: int
    rigs_scheduled: float
    load_kw: float
    renewable_kw_available: float
    price_jpy_kwh: float
    grid_import_kw: float
    status: str

    model_config = {"from_attributes": True}


class OptimizeRequest(BaseModel):
    date: str  # YYYY-MM-DD; defaults to today in Tokyo if omitted


class OptimizeResponse(BaseModel):
    date: str
    total_cost_jpy: float
    counterfactual_cost_jpy: float
    savings_jpy: float
    renewable_fraction: float
    total_co2_kg: float
    counterfactual_co2_kg: float
    blocks: list[WorkloadBlockOut]
