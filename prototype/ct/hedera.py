"""
hedera.py  --  anchor CarbonTruth claims on the Hedera testnet.

  HCS  every verified claim (evidence hash, fingerprint, tCO2e, confidence) and every
       retirement is written to a public topic -> tamper-proof consensus timestamp.
  HTS  each Verified Climate Claim is minted as one NFT serial; retiring burns it.

The node bridge (hedera/bridge.mjs, official @hashgraph/sdk) does the signing. Everything
here is OPTIONAL: with no credentials the prototype keeps working exactly as before and
claims simply show `hedera: null`. Results are stored in data/hedera.json by fingerprint.
"""

import json
import os
import shutil
import subprocess
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
_BRIDGE_DIR = os.path.join(os.path.dirname(_HERE), "hedera")
_STORE = os.path.join(os.path.dirname(_HERE), "data", "hedera.json")
MIRROR = "https://testnet.mirrornode.hedera.com/api/v1"


def _load():
    try:
        with open(_STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d):
    os.makedirs(os.path.dirname(_STORE), exist_ok=True)
    with open(_STORE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def _call(cmd, args=None, timeout=60):
    node = shutil.which("node")
    if not node:
        return {"ok": False, "error": "node not installed"}
    if not os.path.isdir(os.path.join(_BRIDGE_DIR, "node_modules")):
        return {"ok": False, "error": "run `npm install` in prototype/hedera"}
    try:
        p = subprocess.run([node, "bridge.mjs", cmd, json.dumps(args or {})], cwd=_BRIDGE_DIR,
                           capture_output=True, text=True, timeout=timeout)
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"ok": False, "error": "bridge failed: %s" % e}


def enabled():
    """True when credentials exist (env or hedera/.env) -- cheap check, no network."""
    if os.environ.get("HEDERA_ACCOUNT_ID") and os.environ.get("HEDERA_PRIVATE_KEY"):
        return True
    return os.path.exists(os.path.join(_BRIDGE_DIR, ".env"))


def setup():
    return _call("setup", timeout=120)


def on_mint(block):
    """HCS-anchor the claim, then mint its NFT. Returns the hedera record (or None)."""
    if not enabled():
        return None
    msg = json.dumps({"t": "mint", "vcc": block["vcc_id"], "fp": block["fingerprint"],
                      "ev": block["evidence_hash"], "tco2e": block["tonnes"],
                      "conf": block["confidence"]}, separators=(",", ":"))
    anchor = _call("anchor", {"message": msg})
    nft = _call("mint", {"metadata": block["fingerprint"]})
    rec = {"anchor": anchor, "nft": nft}
    d = _load()
    d[block["fingerprint"]] = rec
    _save(d)
    return rec


def on_retire(fingerprint_hex):
    if not enabled():
        return None
    d = _load()
    rec = d.get(fingerprint_hex)
    if not rec:
        return None
    r = {"anchor": _call("anchor", {"message": json.dumps({"t": "retire", "fp": fingerprint_hex},
                                                          separators=(",", ":"))})}
    serial = (rec.get("nft") or {}).get("serial")
    if serial:
        r["burn"] = _call("burn", {"serial": serial})
    rec["retired"] = r
    _save(d)
    return r


def record(fingerprint_hex):
    return _load().get(fingerprint_hex)


def mirror_check(topic_id, sequence):
    """Independent verification straight from the public Mirror Node (no account needed)."""
    try:
        with urllib.request.urlopen("%s/topics/%s/messages/%s" % (MIRROR, topic_id, sequence), timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}
