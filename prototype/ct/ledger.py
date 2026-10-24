"""
ledger.py  --  Mint.

A tamper-evident, hash-chained ledger that mirrors the CarbonTruth smart contract
(contracts/CarbonTruthVCC.sol). Two integrity invariants, straight from the deck:

  1. Uniqueness   each tonne gets a geo-temporal fingerprint; one token per
                  fingerprint -> double counting cannot be expressed.
                        f = H(geohash || date || projectID || tonne_index)

  2. Retire-once  retired set R and active set A never intersect (R n A = {}).

Every block hashes the one before it, so any edit to history is detectable
(`verify_chain`). Persisted to data/ledger.json.
"""

import hashlib
import json
import os
import time

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PATH = os.path.join(_DATA, "ledger.json")


def fingerprint(geohash, date, project_id, tonne_index):
    """f = SHA-256(geohash || date || projectID || tonne_index)."""
    raw = "%s|%s|%s|%d" % (geohash, date, project_id, tonne_index)
    return hashlib.sha256(raw.encode()).hexdigest()


def _hash_block(b):
    payload = {k: b[k] for k in b if k != "hash"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class Ledger:
    def __init__(self, path=_PATH):
        self.path = path
        self.chain = []
        self._load()
        if not self.chain:
            self._genesis()

    # ------------------------------------------------------------------ storage
    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                self.chain = json.load(f)
        except Exception:
            self.chain = []

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.chain, f, indent=2)

    def _genesis(self):
        g = {
            "index": 0, "ts": 0, "type": "genesis",
            "fingerprint": "0" * 64, "prev_hash": "0" * 64,
        }
        g["hash"] = _hash_block(g)
        self.chain = [g]
        self._save()

    # -------------------------------------------------------------------- mint
    def has_fingerprint(self, fp):
        return any(b.get("fingerprint") == fp for b in self.chain if b["index"] > 0)

    def mint(self, *, project_id, geohash, date, tonnes, confidence,
             evidence_hash, scenes, tonne_index=1):
        """
        Mint a Verified Climate Claim. Rejects a duplicate fingerprint, which is
        how double-counting is prevented at the protocol level.
        """
        fp = fingerprint(geohash, date, project_id, tonne_index)
        if self.has_fingerprint(fp):
            return {"ok": False, "error": "duplicate fingerprint -- already minted (double-count blocked)",
                    "fingerprint": fp}
        prev = self.chain[-1]
        block = {
            "index": len(self.chain),
            "ts": int(time.time()),
            "type": "mint",
            "vcc_id": "CT-0x" + fp[:10],
            "project_id": project_id,
            "geohash": geohash,
            "date": date,
            "tonnes": round(tonnes, 1),
            "confidence": confidence,
            "evidence_hash": evidence_hash,
            "scenes": scenes,
            "status": "active",
            "fingerprint": fp,
            "prev_hash": prev["hash"],
        }
        block["hash"] = _hash_block(block)
        self.chain.append(block)
        self._save()
        return {"ok": True, "block": block}

    # ------------------------------------------------------------------ retire
    def retire(self, fingerprint_hex):
        for b in self.chain:
            if b.get("fingerprint") == fingerprint_hex and b.get("status") == "active":
                b["status"] = "retired"
                b["retired_ts"] = int(time.time())
                # append an immutable retirement record so history stays auditable
                prev = self.chain[-1]
                rec = {"index": len(self.chain), "ts": b["retired_ts"], "type": "retire",
                       "fingerprint": fingerprint_hex, "prev_hash": prev["hash"]}
                rec["hash"] = _hash_block(rec)
                self.chain.append(rec)
                self._save()
                return {"ok": True}
        return {"ok": False, "error": "no active credit with that fingerprint"}

    # --------------------------------------------------------------- integrity
    def verify_chain(self):
        """Recompute every hash + link. Returns (ok, broken_index|None)."""
        for i, b in enumerate(self.chain):
            if _hash_block(b) != b["hash"]:
                return False, i
            if i > 0 and b["prev_hash"] != self.chain[i - 1]["hash"]:
                return False, i
        # invariant R n A = {} : no fingerprint is both active and retired-active
        active = {b["fingerprint"] for b in self.chain if b.get("status") == "active"}
        retired = {b["fingerprint"] for b in self.chain
                   if b.get("type") == "retire"}
        return (len(active & retired) == 0), None

    # -------------------------------------------------------------------- views
    def credits(self):
        return [b for b in self.chain if b.get("type") == "mint"]

    def stats(self):
        mints = self.credits()
        active = [b for b in mints if b["status"] == "active"]
        return {
            "total": len(mints),
            "active": len(active),
            "retired": len(mints) - len(active),
            "tonnes_active": round(sum(b["tonnes"] for b in active), 1),
            "blocks": len(self.chain),
        }
