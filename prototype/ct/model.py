"""
model.py  --  Estimate.

NDVI grids -> aboveground biomass (AGB) -> certified CO2e, plus a counterfactual
baseline so only *additional* carbon is credited.

The prototype uses a transparent, documented NDVI->AGB proxy. In production the
same interface is fed structure from spaceborne lidar (NASA GEDI) and the
pantropical allometric model of Chave et al. (2014):

        AGB = 0.0673 * (rho * D^2 * H) ^ 0.976        [GCB, doi:10.1111/gcb.12629]

Carbon accounting (IPCC):
        C   = AGB * CF            CF = 0.47 carbon fraction
        CO2e = C * 44/12         molar mass CO2 / C
"""

import hashlib

from . import ml

MODEL_VERSION = "ndvi-agb-proxy@0.1.0"
CF = 0.47                      # IPCC carbon fraction of dry biomass
CO2_PER_C = 44.0 / 12.0       # 3.667

# NDVI -> AGB (t/ha). Saturating exponential calibrated so bare/degraded NDVI
# (~0.1) ~ 8 t/ha and closed tropical canopy (NDVI ~0.88) ~ 310 t/ha.
_A = 11.0
_B = 3.85


def agb_from_ndvi(ndvi):
    """Per-cell AGB in t/ha; returns (grid, mean)."""
    grid = [[_A * (pow(2.718281828, _B * max(0.0, v)) - 1.0) for v in row] for row in ndvi]
    flat = [v for row in grid for v in row]
    return grid, sum(flat) / len(flat)


def co2e_per_ha(mean_agb):
    """Mean AGB (t/ha) -> mean stored CO2e (t/ha)."""
    return mean_agb * CF * CO2_PER_C


def estimate_stock(scene):
    """
    Full carbon stock readout for one dated scene. Uses the trained neural
    network (ct/ml.py) when its weights are present and the scene carries the
    RED/NIR bands; otherwise falls back to the transparent NDVI curve.
    """
    if ml.available() and scene.get("red") and scene.get("nir"):
        agb_grid, mean_agb = ml.predict_agb_grid(scene["red"], scene["nir"])
        estimator = ml.version()
    else:
        agb_grid, mean_agb = agb_from_ndvi(scene["ndvi"])
        estimator = MODEL_VERSION
    return {
        "date": scene["date"],
        "scene_id": scene["scene_id"],
        "mean_agb_t_ha": round(mean_agb, 2),
        "co2e_t_ha": round(co2e_per_ha(mean_agb), 2),
        "agb_grid": agb_grid,
        "estimator": estimator,
    }


def change_and_additionality(before, after, hectares, baseline_rate=-0.6):
    """
    Net additional CO2e for the plot between two dates.

      project_delta = (after - before) stock over the plot area
      baseline      = counterfactual: what would have happened anyway
                      (default: continued slight degradation, baseline_rate t/ha)
      credits       = max(0, project_delta - baseline_delta)

    `baseline_rate` is CO2e/ha that the baseline scenario would have changed by
    (negative = ongoing loss without the project). Returns a dict of tonnes.
    """
    b = estimate_stock(before)
    a = estimate_stock(after)
    project_delta_ha = a["co2e_t_ha"] - b["co2e_t_ha"]        # t/ha gained
    baseline_delta_ha = baseline_rate                          # t/ha counterfactual
    additional_ha = project_delta_ha - baseline_delta_ha

    project_total = project_delta_ha * hectares
    baseline_total = baseline_delta_ha * hectares
    additional_total = max(0.0, additional_ha * hectares)

    return {
        "before": b,
        "after": a,
        "hectares": hectares,
        "project_delta_t_ha": round(project_delta_ha, 2),
        "baseline_delta_t_ha": round(baseline_delta_ha, 2),
        "additional_t_ha": round(additional_ha, 2),
        "project_total_tco2e": round(project_total, 1),
        "baseline_total_tco2e": round(baseline_total, 1),
        "additional_tco2e": round(additional_total, 1),   # the claim we verify
        "model_version": a.get("estimator", MODEL_VERSION),
    }


def model_fingerprint(result):
    """Hash of model identity + key outputs, for the on-chain evidence bundle."""
    key = "%s|%s|%s|%.3f" % (
        MODEL_VERSION, result["before"]["scene_id"],
        result["after"]["scene_id"], result["additional_tco2e"],
    )
    return hashlib.sha256(key.encode()).hexdigest()
