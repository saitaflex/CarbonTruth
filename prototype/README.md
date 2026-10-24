# CarbonTruth — verification layer for climate claims

**Team Pyragrid · IEEE ClimateChain Global Hackathon 2026**
*"The SSL certificate for climate data."*

A climate claim goes in; a **Verified Climate Claim (VCC)** comes out — AI-verified
from independent open satellite data, anchored on a tamper-evident hash-chained
ledger, globally unique so a tonne can never be double-counted or double-spent.

This prototype is the real pipeline behind slide 6 of the pitch deck.

---

## Run it

```bash
cd prototype
python app.py            # -> http://127.0.0.1:8017
```

No pip install, no API keys — **pure Python standard library** (tested on 3.14).
Open the explorer, then:

1. **▶ Verify honest claim** → three independent oracles agree, confidence ~99%,
   a VCC is minted on the chain.
2. **▶ Verify honest claim again** → **double-count blocked** (same geo-temporal
   fingerprint can't mint twice).
3. **▶ Verify inflated claim** → an over-stated claim scores ~32%, **rejected**
   below the 90% gate. This is the over-crediting that *Science* found in real
   markets, caught before mint.
4. **Retire** any active credit → it moves active→retired, once, forever.

Quick check without the browser:

```bash
python app.py --selftest
```

---

## The pipeline  (`satellite → model → oracle → ledger`)

| Stage | File | What it does |
|---|---|---|
| **Observe** | `ct/satellite.py` | Sentinel-2 band math `NDVI = (B08−B04)/(B08+B04)`. Bundled sample scene by default; `search_stac()` really queries **Microsoft Planetary Computer** (free, no key) for live Sentinel-2 scene IDs over the plot. |
| **Estimate** | `ct/model.py` + `ct/ml.py` | A **trained neural network** (6→32→16 MLP) maps spectral features (NDVI, SAVI, NIR, RED, ratio, NDVI²) → aboveground biomass → CO₂e: `E = AGB·CF·44/12` (CF 0.47, IPCC). Counterfactual baseline → **additional** CO₂e only. Falls back to the transparent NDVI curve if the weights file is absent. |
| **Verify** | `ct/oracle.py` | Inverse-variance fusion of independent estimates: `μ = Σwᵢmᵢ / Σwᵢ`, `wᵢ = 1/σᵢ²`. Support `V = 1 − |μ−c|/c`. Mint iff `V ≥ θ` (0.90) **and** k-of-n oracles agree. |
| **Mint** | `ct/ledger.py` | SHA-256 hash-chained ledger. Fingerprint `f = H(geohash‖date‖projectID‖k)`, one token per `f` (double-count impossible), retire-once invariant `R ∩ A = ∅`, `verify_chain()` proves integrity. Mirrors the Solidity contract. |

## Smart contract

`contracts/CarbonTruthVCC.sol` — a real, dependency-free EVM contract enforcing the
same two invariants on-chain (fingerprint uniqueness + retire-once) with an
evidence-hash anchor and a 90% confidence gate (`THETA_BPS`). Deploy in Remix or
to Sepolia; `computeFingerprint()` keeps off-chain and on-chain fingerprints in sync.

## HTTP API

| Method | Route | Purpose |
|---|---|---|
| GET  | `/` | Explorer UI |
| POST | `/api/verify` | Run the pipeline (`{"scenario":"honest"\|"inflated"}`) |
| POST | `/api/retire` | Retire a credit (`{"fingerprint":"…"}`) |
| GET  | `/api/credits` | Registry + stats |
| GET  | `/api/chain` | Chain-integrity proof |
| GET  | `/api/stac` | Live Sentinel-2 scene discovery |
| GET  | `/api/meta` | Product / team / plot |

## Honesty about scope

Built in a hackathon: the **logic is real** (band math, a **trained neural network**
for biomass, inverse-variance fusion, hashing, invariants, live STAC discovery,
deployable contract). The biomass step is a real MLP (`scripts/train_biomass.py` →
`ct/model_mlp.json`, R²≈0.98 on held-out data, pure-stdlib inference); its training
labels are **GEDI-calibrated** (Chave 2014 backbone), not yet validated against field
plots at this site, and the **pixels are a bundled sample scene**. Dollar and tonne
figures illustrate the method — they are not audited credits. The production gap is
field-measured GEDI L4A labels and site calibration, not the architecture.

---
*CarbonTruth · Pyragrid · 2026*
