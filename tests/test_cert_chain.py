"""
Unit tests for the hash-chain certificate system.

We test three properties:
  1. Hash continuity — each cert's prev_hash equals the previous cert's cert_hash
  2. Tamper detection — modifying any field causes verify_chain to fail
  3. Genesis block — the first certificate always links to the all-zeros hash
"""

import hashlib
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.cert_chain import (
    GENESIS_HASH,
    _canonical_json,
    _compute_cert_hash,
    _sha256,
)


class TestHashHelpers:
    def test_canonical_json_sorted_keys(self):
        payload = {"z": 1, "a": 2, "m": 3}
        result = _canonical_json(payload)
        parsed = json.loads(result)
        assert list(parsed.keys()) == sorted(parsed.keys())

    def test_canonical_json_no_whitespace(self):
        payload = {"key": "value"}
        result = _canonical_json(payload)
        assert " " not in result
        assert "\n" not in result

    def test_canonical_json_deterministic(self):
        payload = {"date": "2025-03-14", "savings": 2340.5, "fraction": 0.673}
        assert _canonical_json(payload) == _canonical_json(payload)

    def test_sha256_known_value(self):
        result = _sha256("hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert result == expected

    def test_sha256_length(self):
        result = _sha256("anything")
        assert len(result) == 64

    def test_genesis_hash_format(self):
        assert len(GENESIS_HASH) == 64
        assert all(c == "0" for c in GENESIS_HASH)


class TestCertHashComputation:
    def test_cert_hash_changes_with_seq(self):
        h1 = _compute_cert_hash(1, GENESIS_HASH, "abc")
        h2 = _compute_cert_hash(2, GENESIS_HASH, "abc")
        assert h1 != h2

    def test_cert_hash_changes_with_prev_hash(self):
        h1 = _compute_cert_hash(1, GENESIS_HASH, "abc")
        h2 = _compute_cert_hash(1, "a" * 64, "abc")
        assert h1 != h2

    def test_cert_hash_changes_with_payload(self):
        h1 = _compute_cert_hash(1, GENESIS_HASH, "payload_a")
        h2 = _compute_cert_hash(1, GENESIS_HASH, "payload_b")
        assert h1 != h2

    def test_cert_hash_deterministic(self):
        h1 = _compute_cert_hash(5, "x" * 64, "payload")
        h2 = _compute_cert_hash(5, "x" * 64, "payload")
        assert h1 == h2


class TestChainIntegrity:
    """Test the mathematical properties of the chain without a real database."""

    def _build_chain(self, n: int, payloads: list[dict]) -> list[dict]:
        """Build an in-memory certificate chain for testing."""
        chain = []
        prev_hash = GENESIS_HASH
        for seq, payload in enumerate(payloads[:n], start=1):
            canonical = _canonical_json(payload)
            payload_hash = _sha256(canonical)
            cert_hash = _compute_cert_hash(seq, prev_hash, payload_hash)
            chain.append({
                "seq": seq,
                "prev_hash": prev_hash,
                "payload_hash": payload_hash,
                "cert_hash": cert_hash,
                "data_json": canonical,
            })
            prev_hash = cert_hash
        return chain

    def _verify_chain(self, chain: list[dict]) -> tuple[bool, int | None]:
        expected_prev = GENESIS_HASH
        for cert in sorted(chain, key=lambda c: c["seq"]):
            if _sha256(cert["data_json"]) != cert["payload_hash"]:
                return False, cert["seq"]
            if cert["prev_hash"] != expected_prev:
                return False, cert["seq"]
            expected = _compute_cert_hash(cert["seq"], expected_prev, cert["payload_hash"])
            if expected != cert["cert_hash"]:
                return False, cert["seq"]
            expected_prev = cert["cert_hash"]
        return True, None

    def test_valid_chain_passes(self):
        payloads = [
            {"date": f"2025-03-{i:02d}", "savings": float(1000 + i * 37)}
            for i in range(1, 8)
        ]
        chain = self._build_chain(7, payloads)
        valid, broken = self._verify_chain(chain)
        assert valid is True
        assert broken is None

    def test_tampered_data_json_fails(self):
        payloads = [{"date": "2025-03-14", "savings": 2340.5}] * 3
        chain = self._build_chain(3, payloads)

        # Tamper with the second certificate's payload
        chain[1] = dict(chain[1])
        chain[1]["data_json"] = chain[1]["data_json"].replace("2340.5", "9999.0")

        valid, broken = self._verify_chain(chain)
        assert valid is False
        assert broken == 2

    def test_tampered_prev_hash_fails(self):
        payloads = [{"date": f"2025-03-{i:02d}", "v": i} for i in range(1, 5)]
        chain = self._build_chain(4, payloads)

        chain[2] = dict(chain[2])
        chain[2]["prev_hash"] = "f" * 64  # break the linkage

        valid, broken = self._verify_chain(chain)
        assert valid is False
        assert broken == 3

    def test_first_cert_links_to_genesis(self):
        payloads = [{"date": "2025-03-01", "savings": 500.0}]
        chain = self._build_chain(1, payloads)
        assert chain[0]["prev_hash"] == GENESIS_HASH

    def test_each_cert_links_to_previous(self):
        payloads = [{"v": i} for i in range(10)]
        chain = self._build_chain(10, payloads)
        for i in range(1, len(chain)):
            assert chain[i]["prev_hash"] == chain[i - 1]["cert_hash"]
