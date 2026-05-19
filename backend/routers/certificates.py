from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.certificate import EnergyCertificate
from backend.schemas.certificate import CertificateOut, ChainVerifyResult
from backend.services import cert_chain

router = APIRouter()


@router.get("", response_model=list[CertificateOut])
async def list_certificates(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EnergyCertificate)
        .order_by(EnergyCertificate.seq.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows


@router.get("/verify", response_model=ChainVerifyResult)
async def verify(db: AsyncSession = Depends(get_db)):
    """Recompute every hash in the chain. Returns pass/fail with the first broken seq."""
    stmt = select(EnergyCertificate)
    count = len((await db.execute(stmt)).scalars().all())

    valid, broken_at = await cert_chain.verify_chain(db)
    if valid:
        return ChainVerifyResult(
            valid=True,
            total_certs=count,
            message=f"Chain OK ({count} certificates verified)",
        )
    return ChainVerifyResult(
        valid=False,
        total_certs=count,
        broken_at_seq=broken_at,
        message=f"Chain broken at seq={broken_at}",
    )


@router.get("/{seq}", response_model=CertificateOut)
async def get_certificate(seq: int, db: AsyncSession = Depends(get_db)):
    stmt = select(EnergyCertificate).where(EnergyCertificate.seq == seq)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Certificate seq={seq} not found")
    return row
