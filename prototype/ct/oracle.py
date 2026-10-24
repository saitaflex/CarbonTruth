"""
oracle.py  --  Verify.

The oracle problem: a ledger only proves a number did not change, not that it was
ever true. CarbonTruth cross-checks a climate claim against several INDEPENDENT
estimators before anything is minted. No single feed can be spoofed into a credit.

Three independent estimates m_i of the plot's net additional CO2e, each with a
variance sigma_i^2, are fused by inverse-variance weighting:

        w_i = 1 / sigma_i^2
        mu  = sum(w_i * m_i) / sum(w_i)         fused estimate
        s   = sqrt(1 / sum(w_i))                fused std. dev.

Against a claim c the support score is

        V = 1 - |mu - c| / c      (clamped to [0, 1])

Mint iff  V >= theta  AND  at least k of n oracles agree with mu within tol.
"""

import hashlib
import random

THETA = 0.90          # confidence gate
K_OF_N = 2            # minimum agreeing oracles
TOL = 0.12            # relative tolerance for "agrees with mu"


def _oracle_estimates(truth_tco2e, seed):
    """
    Three independent estimators of the same net-additional CO2e, each biased and
    noised differently and carrying its own uncertainty:
      optical  Sentinel-2 NDVI model   (medium precision)
      lidar    GEDI canopy-height AGB   (high precision)
      archive  Landsat baseline trend   (lower precision, wider sigma)
    Deterministic for a given seed.
    """
    rng = random.Random(seed)
    specs = [
        ("optical_sentinel2", 1.00, 0.06),   # (name, bias factor, rel. sigma)
        ("lidar_gedi",        0.98, 0.04),
        ("archive_landsat",   1.03, 0.09),
    ]
    out = []
    for name, bias, rel in specs:
        sigma = max(1.0, rel * truth_tco2e)
        m = truth_tco2e * bias + rng.gauss(0, sigma * 0.35)
        out.append({"name": name, "estimate": round(m, 1), "sigma": round(sigma, 1)})
    return out


def fuse(estimates):
    """Inverse-variance fusion -> (mu, s, weights)."""
    ws = [1.0 / (e["sigma"] ** 2) for e in estimates]
    mu = sum(w * e["estimate"] for w, e in zip(ws, estimates)) / sum(ws)
    s = (1.0 / sum(ws)) ** 0.5
    return mu, s, ws


def verify(claim_tco2e, truth_tco2e, evidence_inputs, seed=7):
    """
    Run consensus on a claim. `truth_tco2e` is what the independent estimators
    center on (the model's additional CO2e). `claim_tco2e` is what the project
    asserts -- inflate it and the oracle rejects the over-credit.

    Returns the full decision bundle, including the on-chain evidence hash.
    """
    estimates = _oracle_estimates(truth_tco2e, seed)
    mu, s, ws = fuse(estimates)

    support = 1.0 - abs(mu - claim_tco2e) / max(1.0, claim_tco2e)
    support = max(0.0, min(1.0, support))

    agree = sum(1 for e in estimates if abs(e["estimate"] - mu) / max(1.0, mu) <= TOL)
    passed = (support >= THETA) and (agree >= K_OF_N)

    # evidence bundle: everything needed to reproduce the verdict, hashed
    bundle = "|".join([
        evidence_inputs.get("before_scene", ""),
        evidence_inputs.get("after_scene", ""),
        evidence_inputs.get("model_version", ""),
        evidence_inputs.get("model_hash", ""),
        "claim=%.1f" % claim_tco2e,
        "mu=%.1f" % mu,
        "V=%.4f" % support,
        "|".join("%s=%.1f" % (e["name"], e["estimate"]) for e in estimates),
    ])
    evidence_hash = hashlib.sha256(bundle.encode()).hexdigest()

    return {
        "estimates": estimates,
        "mu": round(mu, 1),
        "sigma": round(s, 2),
        "claim_tco2e": round(claim_tco2e, 1),
        "confidence": round(support * 100, 1),     # percent, for the gauge
        "theta": THETA * 100,
        "agree": agree,
        "k_of_n": "%d/%d" % (agree, len(estimates)),
        "passed": passed,
        "evidence_hash": evidence_hash,
        "reason": ("consensus confirms the claim" if passed else
                   "claim exceeds independent estimates -- over-credit rejected"),
    }
