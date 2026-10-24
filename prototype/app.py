"""
CarbonTruth prototype  --  Pyragrid · ClimateChain Global Hackathon 2026.

    python app.py              start the explorer at http://127.0.0.1:8017
    python app.py --selftest   run one honest + one inflated verification, print it

Pure standard library: no pip install, no API keys. The pipeline
satellite -> model -> oracle -> ledger is real; satellite pixels are a bundled
sample scene (see ct/satellite.py for the live Sentinel-2 STAC path), and the
ledger mirrors contracts/CarbonTruthVCC.sol.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from ct import satellite, model, oracle, VERSION, PRODUCT, TEAM
from ct.ledger import Ledger

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
PORT = 8017
LED = Ledger()

INFLATE = 3.1   # how much the 'inflated' scenario over-claims


# ----------------------------------------------------------------- the pipeline
def run_verification(scenario="honest"):
    """satellite -> model -> oracle -> (maybe) mint. Returns the full bundle."""
    before = satellite.fetch_scene("before")
    after = satellite.fetch_scene("after")
    plot = satellite.PLOT

    m = model.change_and_additionality(before, after, plot["hectares"])
    truth = m["additional_tco2e"]
    claim = truth if scenario == "honest" else round(truth * INFLATE, 1)

    ev_inputs = {
        "before_scene": before["scene_id"],
        "after_scene": after["scene_id"],
        "model_version": m["model_version"],
        "model_hash": model.model_fingerprint(m),
    }
    v = oracle.verify(claim, truth, ev_inputs)

    minted = None
    if v["passed"]:
        minted = LED.mint(
            project_id=plot["project_id"],
            geohash=plot["geohash"],
            date=after["date"],
            tonnes=v["mu"],                 # mint the independently-verified amount
            confidence=v["confidence"],
            evidence_hash=v["evidence_hash"],
            scenes=[before["scene_id"], after["scene_id"]],
        )

    return {
        "scenario": scenario,
        "plot": plot,
        "scenes": {
            "before": {"date": before["date"], "id": before["scene_id"],
                       "ndvi": before["ndvi"], "source": before["source"]},
            "after": {"date": after["date"], "id": after["scene_id"],
                      "ndvi": after["ndvi"], "source": after["source"]},
        },
        "model": {k: m[k] for k in (
            "project_delta_t_ha", "baseline_delta_t_ha", "additional_t_ha",
            "project_total_tco2e", "baseline_total_tco2e", "additional_tco2e",
            "hectares", "model_version")},
        "oracle": v,
        "mint": minted,
    }


# ----------------------------------------------------------------- HTTP server
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):            # quiet, custom banner handles output
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        if p in ("/", "/index.html"):
            return self._file("explorer.html", "text/html; charset=utf-8")
        if p == "/api/credits":
            return self._send(200, {"stats": LED.stats(), "credits": list(reversed(LED.credits()))})
        if p == "/api/credit":
            fp = (q.get("fp") or [""])[0]
            b = next((x for x in LED.credits() if x["fingerprint"] == fp), None)
            return self._send(200 if b else 404, b or {"error": "not found"})
        if p == "/api/chain":
            ok, bad = LED.verify_chain()
            return self._send(200, {"intact": ok, "broken_at": bad, "blocks": len(LED.chain)})
        if p == "/api/stac":
            return self._send(200, {"scenes": satellite.search_stac()})
        if p == "/api/meta":
            return self._send(200, {"product": PRODUCT, "team": TEAM, "version": VERSION,
                                    "plot": satellite.PLOT})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except Exception:
            body = {}
        if u.path == "/api/verify":
            scenario = body.get("scenario", "honest")
            return self._send(200, run_verification(scenario))
        if u.path == "/api/retire":
            return self._send(200, LED.retire(body.get("fingerprint", "")))
        return self._send(404, {"error": "not found"})

    def _file(self, name, ctype):
        path = os.path.join(WEB, name)
        try:
            with open(path, "rb") as f:
                return self._send(200, f.read().decode("utf-8"), ctype)
        except Exception:
            return self._send(500, {"error": "missing " + name})


# ----------------------------------------------------------------------- entry
def selftest():
    for sc in ("honest", "inflated"):
        r = run_verification(sc)
        o, mo = r["oracle"], r["model"]
        print("\n=== scenario: %s ===" % sc.upper())
        print("  plot            : %s (%.0f ha)" % (r["plot"]["name"], mo["hectares"]))
        print("  additional CO2e : %.1f tCO2e  (model)" % mo["additional_tco2e"])
        print("  claim           : %.1f tCO2e" % o["claim_tco2e"])
        print("  oracles         : " + ", ".join(
            "%s=%.0f(s%.0f)" % (e["name"], e["estimate"], e["sigma"]) for e in o["estimates"]))
        print("  fused mu / sigma: %.1f / %.2f" % (o["mu"], o["sigma"]))
        print("  confidence      : %.1f%%  (theta %.0f%%, agree %s)"
              % (o["confidence"], o["theta"], o["k_of_n"]))
        print("  decision        : %s -- %s" % ("MINT" if o["passed"] else "REJECT", o["reason"]))
        if r["mint"]:
            if r["mint"]["ok"]:
                b = r["mint"]["block"]
                print("  minted VCC      : %s  %.1f tCO2e  fp=%s..." % (b["vcc_id"], b["tonnes"], b["fingerprint"][:12]))
            else:
                print("  mint            : BLOCKED -- %s" % r["mint"]["error"])
    ok, bad = LED.verify_chain()
    print("\nchain integrity   : %s (%d blocks)\n" % ("INTACT" if ok else "BROKEN@%s" % bad, len(LED.chain)))


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    bar = "=" * 54
    print("\n" + bar)
    print("  %s  -- verification layer for climate claims" % PRODUCT)
    print("  team %s · v%s" % (TEAM, VERSION))
    print(bar)
    print("  Explorer:  http://127.0.0.1:%d" % PORT)
    print("  Stop:      Ctrl+C")
    print(bar + "\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        srv.server_close()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        serve()
