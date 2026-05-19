from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class EnergyCertificate(Base):
    """
    Tamper-evident audit log for optimizer scheduling decisions.

    Same structural concept as git's object model or certificate transparency
    logs — not a distributed ledger. Each row's cert_hash covers the sequence
    number, the previous row's cert_hash, and the SHA-256 of the payload JSON.
    Any modification to historical data breaks the chain at that sequence number.
    """

    __tablename__ = "energy_certificates"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    cert_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
