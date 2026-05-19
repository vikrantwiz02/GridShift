#!/usr/bin/env python3
"""
Standalone certificate chain verifier.

Reads all EnergyCertificate rows in sequence order and recomputes every hash.
This script has no dependency on the running web server — it connects directly
to the database, making it suitable for offline audits or CI checks.

Usage:
    python scripts/verify_chain.py
    DATABASE_URL=postgresql+asyncpg://... python scripts/verify_chain.py
"""

import asyncio
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from backend.database import AsyncSessionLocal, Base, engine
from backend.models.certificate import EnergyCertificate

GENESIS_HASH = "0" * 64


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_cert_hash(seq: int, prev_hash: str, payload_hash: str) -> str:
    return sha256(f"{seq}:{prev_hash}:{payload_hash}")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        stmt = select(EnergyCertificate).order_by(EnergyCertificate.seq.asc())
        rows = (await session.execute(stmt)).scalars().all()

    if not rows:
        print("No certificates in database.")
        sys.exit(0)

    print(f"Verifying {len(rows)} certificate(s)...\n")

    expected_prev = GENESIS_HASH
    errors = []

    for cert in rows:
        ok = True

        # 1. Verify payload hash
        recomputed_payload = sha256(cert.data_json)
        if recomputed_payload != cert.payload_hash:
            errors.append(
                f"  seq={cert.seq}: payload_hash mismatch\n"
                f"    stored:   {cert.payload_hash}\n"
                f"    computed: {recomputed_payload}"
            )
            ok = False

        # 2. Verify chain linkage
        if cert.prev_hash != expected_prev:
            errors.append(
                f"  seq={cert.seq}: prev_hash linkage broken\n"
                f"    expected: {expected_prev}\n"
                f"    stored:   {cert.prev_hash}"
            )
            ok = False

        # 3. Verify cert hash
        recomputed_cert = compute_cert_hash(cert.seq, expected_prev, cert.payload_hash)
        if recomputed_cert != cert.cert_hash:
            errors.append(
                f"  seq={cert.seq}: cert_hash mismatch\n"
                f"    stored:   {cert.cert_hash}\n"
                f"    computed: {recomputed_cert}"
            )
            ok = False

        status = "✓" if ok else "✗"
        issued = cert.issued_at.strftime("%Y-%m-%d %H:%M UTC") if cert.issued_at else "?"
        print(f"  {status}  seq={cert.seq:>4}  {issued}  {cert.cert_hash[:16]}...")

        if not ok:
            print(f"\nChain broken at seq={cert.seq}. Stopping verification.")
            for e in errors:
                print(e)
            sys.exit(1)

        expected_prev = cert.cert_hash

    print(f"\nChain OK ({len(rows)} certificates verified)")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
