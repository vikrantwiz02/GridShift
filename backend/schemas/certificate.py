from datetime import datetime

from pydantic import BaseModel


class CertificateOut(BaseModel):
    seq: int
    issued_at: datetime
    prev_hash: str
    payload_hash: str
    cert_hash: str
    data_json: str

    model_config = {"from_attributes": True}


class ChainVerifyResult(BaseModel):
    valid: bool
    total_certs: int
    broken_at_seq: int | None = None
    message: str
