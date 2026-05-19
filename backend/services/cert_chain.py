"""
Tamper-evident audit log for optimizer scheduling decisions.

Each certificate covers one optimization run. The chain works identically to
git's object model: cert_hash is a function of the payload AND the previous
cert's hash, so retroactively altering any record invalidates every subsequent
hash without touching those rows.

This is NOT a distributed ledger. There is no consensus protocol, no
proof-of-work, and no peer network. The security guarantee is the same as a
certificate transparency log or a signed audit trail: a trusted authority
(this server) issues records, and anyone with DB read access can verify
integrity without trusting the authority.
"""

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.certificate import EnergyCertificate

GENESIS_HASH = "0" * 64


def _canonical_json(payload: dict) -> str:
    """Deterministic serialisation — sorted keys, no whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _compute_cert_hash(seq: int, prev_hash: str, payload_hash: str) -> str:
    return _sha256(f"{seq}:{prev_hash}:{payload_hash}")


async def issue_certificate(session: AsyncSession, payload: dict) -> EnergyCertificate:
    """Append a new certificate to the chain and persist it."""
    canonical = _canonical_json(payload)
    payload_hash = _sha256(canonical)

    # Fetch the most recent certificate to get prev_hash
    stmt = select(EnergyCertificate).order_by(EnergyCertificate.seq.desc()).limit(1)
    row = (await session.execute(stmt)).scalar_one_or_none()

    if row is None:
        prev_hash = GENESIS_HASH
        next_seq = 1
    else:
        prev_hash = row.cert_hash
        next_seq = row.seq + 1

    cert_hash = _compute_cert_hash(next_seq, prev_hash, payload_hash)

    cert = EnergyCertificate(
        seq=next_seq,
        issued_at=datetime.now(tz=timezone.utc),
        prev_hash=prev_hash,
        payload_hash=payload_hash,
        cert_hash=cert_hash,
        data_json=canonical,
    )
    session.add(cert)
    await session.commit()
    await session.refresh(cert)
    return cert


async def verify_chain(session: AsyncSession) -> tuple[bool, int | None]:
    """
    Walk the full chain and recompute every hash.

    Returns (True, None) if intact, or (False, broken_seq) if tampered.
    """
    stmt = select(EnergyCertificate).order_by(EnergyCertificate.seq.asc())
    rows = (await session.execute(stmt)).scalars().all()

    expected_prev = GENESIS_HASH
    for cert in rows:
        # Verify payload hash
        recomputed_payload = _sha256(cert.data_json)
        if recomputed_payload != cert.payload_hash:
            return False, cert.seq

        # Verify cert hash
        recomputed_cert = _compute_cert_hash(cert.seq, expected_prev, cert.payload_hash)
        if recomputed_cert != cert.cert_hash:
            return False, cert.seq

        # Verify chain linkage
        if cert.prev_hash != expected_prev:
            return False, cert.seq

        expected_prev = cert.cert_hash

    return True, None
