"""
ml.py  --  the AI in "AI-verified".

A small neural network (multilayer perceptron) that maps Sentinel-2 surface
reflectance to aboveground biomass (AGB, t/ha). The network is TRAINED offline
with scikit-learn (see scripts/train_biomass.py) on a GEDI-calibrated set of
tropical-forest reflectance -> biomass samples, then its weights are frozen into
`ct/model_mlp.json`.

Inference here is PURE standard library -- a hand-written forward pass -- so the
prototype still runs with `python app.py` and no pip installs. If the weights
file is missing, `available()` returns False and model.py falls back to the
transparent NDVI curve, so the pipeline never breaks.

Features per pixel (all derivable from the RED/NIR bands the sensor delivers):
    NDVI, SAVI, NIR, RED, NIR/RED ratio, NDVI^2
Feature engineering + a trained MLP is the standard shape of operational biomass
models; production swaps the GEDI-calibrated labels for real GEDI L4A footprints.
"""

import json
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "model_mlp.json")
EPS = 1e-6

_MODEL = None          # loaded lazily
_TRIED = False


def _load():
    global _MODEL, _TRIED
    if _TRIED:
        return _MODEL
    _TRIED = True
    try:
        with open(_PATH, encoding="utf-8") as f:
            _MODEL = json.load(f)
    except Exception:
        _MODEL = None
    return _MODEL


def available():
    return _load() is not None


def info():
    m = _load() or {}
    return {
        "version": m.get("version", "unavailable"),
        "metrics": m.get("metrics", {}),
        "features": m.get("features", []),
        "trained_on": m.get("trained_on", ""),
    }


def version():
    return (_load() or {}).get("version", "ndvi-agb-proxy@0.1.0")


# --------------------------------------------------------------- feature vector
def cell_features(red, nir):
    """Six remote-sensing features from one pixel's RED/NIR reflectance."""
    ndvi = (nir - red) / (nir + red + EPS)
    L = 0.5                                   # SAVI soil-adjustment factor
    savi = (nir - red) / (nir + red + L + EPS) * (1.0 + L)
    ratio = nir / (red + EPS)
    return [ndvi, savi, nir, red, ratio, ndvi * ndvi]


# ------------------------------------------------------------------- forward pass
def _relu(v):
    return v if v > 0.0 else 0.0


def _predict_one(feat, m):
    # standardize
    mean, std = m["scaler"]["mean"], m["scaler"]["std"]
    x = [(feat[i] - mean[i]) / (std[i] if std[i] else 1.0) for i in range(len(feat))]
    # dense layers: z = W.x + b  (W stored as [out][in])
    for layer in m["layers"]:
        W, b, act = layer["w"], layer["b"], layer["act"]
        z = [sum(W[o][i] * x[i] for i in range(len(x))) + b[o] for o in range(len(b))]
        x = [_relu(v) for v in z] if act == "relu" else z
    return max(0.0, x[0])


def predict_agb_grid(red, nir):
    """Per-pixel AGB (t/ha) from RED/NIR grids. Returns (grid, mean)."""
    m = _load()
    if m is None:
        raise RuntimeError("model_mlp.json not loaded")
    n = len(red)
    grid = [[_predict_one(cell_features(red[y][x], nir[y][x]), m)
             for x in range(len(red[y]))] for y in range(n)]
    flat = [v for row in grid for v in row]
    return grid, sum(flat) / len(flat)
