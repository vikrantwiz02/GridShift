from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.schedule import WorkloadBlock
from backend.schemas.schedule import OptimizeRequest, OptimizeResponse, WorkloadBlockOut
from backend.services import scheduler

router = APIRouter()


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(req: OptimizeRequest, db: AsyncSession = Depends(get_db)):
    """Run the LP optimizer for the given date and persist the result."""
    try:
        target = date.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    try:
        result, blocks = await scheduler.run_optimization(db, target)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return OptimizeResponse(
        date=req.date,
        total_cost_jpy=result.total_cost_jpy,
        counterfactual_cost_jpy=result.counterfactual_cost_jpy,
        savings_jpy=result.savings_jpy,
        renewable_fraction=result.renewable_fraction,
        total_co2_kg=result.total_co2_kg,
        counterfactual_co2_kg=result.counterfactual_co2_kg,
        blocks=[WorkloadBlockOut.model_validate(b) for b in blocks],
    )


@router.get("/current", response_model=list[WorkloadBlockOut])
async def get_current(target_date: date = date.today(), db: AsyncSession = Depends(get_db)):
    """Return the most recent persisted schedule for the given date."""
    stmt = (
        select(WorkloadBlock)
        .where(WorkloadBlock.date == target_date.isoformat())
        .order_by(WorkloadBlock.slot_index)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows
