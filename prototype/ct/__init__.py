"""
CarbonTruth — the verification layer for climate claims.
Team: Pyragrid · ClimateChain Global Hackathon 2026.

A climate claim goes in; a Verified Climate Claim (VCC) comes out:
AI-verified from independent open data, anchored on a hash-chained ledger,
globally unique so it can never be double-counted or double-spent.

Pipeline:  satellite -> model -> oracle -> ledger
  satellite.py   open Sentinel-2 / Landsat style reflectance -> NDVI
  model.py       NDVI -> aboveground biomass -> CO2e, with a counterfactual baseline
  oracle.py      fuse independent estimators (inverse-variance) and gate on confidence
  ledger.py      mint a fingerprinted, retire-once VCC on a tamper-evident chain

Pure standard library. Run the server with:  python app.py
"""

VERSION = "0.1.0"
PRODUCT = "CarbonTruth"
TEAM = "Pyragrid"
