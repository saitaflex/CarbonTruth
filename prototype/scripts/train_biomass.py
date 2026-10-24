"""
train_biomass.py  --  train the AGB neural network, freeze it to JSON.

Trains a scikit-learn MLPRegressor to map Sentinel-2 RED/NIR-derived features to
aboveground biomass (t/ha), then exports the standardizer + weights to
ct/model_mlp.json, which ct/ml.py reads with a pure-stdlib forward pass.

Labels are generated from the GEDI-calibrated pantropical biomass relationship
(Chave et al. 2014 backbone) with a structural SAVI correction and heteroscedastic
measurement noise -- the transparent prototype stand-in for real GEDI L4A
footprints. Run once:  python scripts/train_biomass.py

Needs numpy + scikit-learn (training only; inference stays dependency-free).
"""
import json
import math
import os
import sys

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
sys.path.insert(0, PROTO)
from ct.ml import cell_features                 # identical features at train + inference

RNG = np.random.default_rng(7)
N = 6000


def gedi_agb(ndvi, savi):
    """GEDI-calibrated backbone (Chave 2014 shape) + small structural correction."""
    agb = 12.05 * (math.exp(3.85 * ndvi) - 1.0)         # tropical AGB vs NDVI (GEDI-calibrated)
    agb *= (1.0 + 0.4 * (savi - ndvi))                   # canopy-structure nudge
    return max(2.0, agb)


def make_dataset(n):
    X, y = [], []
    for _ in range(n):
        v = RNG.uniform(0.0, 1.0)                          # vegetation fraction
        nir = float(np.clip(0.10 + 0.34 * v + RNG.normal(0, 0.02), 0.03, 0.55))
        red = float(np.clip(0.135 - 0.095 * v + RNG.normal(0, 0.01), 0.01, 0.20))
        f = cell_features(red, nir)                       # [ndvi,savi,nir,red,ratio,ndvi2]
        agb = gedi_agb(f[0], f[1])
        agb += RNG.normal(0, 0.10 * agb)                  # heteroscedastic noise
        X.append(f); y.append(max(2.0, agb))
    return np.array(X), np.array(y)


def main():
    X, y = make_dataset(N)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=7)

    pipe = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(32, 16), activation="relu", solver="adam",
                     alpha=1e-4, max_iter=4000, random_state=7, tol=1e-6),
    )
    pipe.fit(Xtr, ytr)

    pred = pipe.predict(Xte)
    r2 = r2_score(yte, pred)
    rmse = math.sqrt(mean_squared_error(yte, pred))
    mae = mean_absolute_error(yte, pred)
    cv = cross_val_score(pipe, X, y, cv=5, scoring="r2")

    print("=== AGB neural network ===")
    print("  samples          : %d (train %d / test %d)" % (N, len(Xtr), len(Xte)))
    print("  architecture     : 6 -> 32 -> 16 -> 1 (ReLU), StandardScaler")
    print("  test R^2         : %.4f" % r2)
    print("  test RMSE        : %.2f t/ha" % rmse)
    print("  test MAE         : %.2f t/ha" % mae)
    print("  5-fold CV R^2    : %.4f +/- %.4f" % (cv.mean(), cv.std()))

    scaler = pipe.named_steps["standardscaler"]
    net = pipe.named_steps["mlpregressor"]
    layers = []
    for i, (W, b) in enumerate(zip(net.coefs_, net.intercepts_)):
        layers.append({"w": W.T.tolist(), "b": b.tolist(),
                       "act": "relu" if i < len(net.coefs_) - 1 else "linear"})

    out = {
        "version": "mlp-biomass@1.0",
        "arch": "6-32-16-1 relu MLP",
        "features": ["ndvi", "savi", "nir", "red", "ratio", "ndvi2"],
        "scaler": {"mean": scaler.mean_.tolist(), "std": scaler.scale_.tolist()},
        "layers": layers,
        "metrics": {"r2": round(float(r2), 4), "rmse": round(float(rmse), 2),
                    "mae": round(float(mae), 2), "cv_r2": round(float(cv.mean()), 4),
                    "n_train": int(len(Xtr))},
        "trained_on": "GEDI-calibrated tropical-forest reflectance->AGB (Chave 2014 backbone; synthetic prototype labels)",
    }
    dst = os.path.join(PROTO, "ct", "model_mlp.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("  exported         : %s (%d bytes)" % (dst, os.path.getsize(dst)))


if __name__ == "__main__":
    main()
