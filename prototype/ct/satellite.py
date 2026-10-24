"""
satellite.py  --  Observe.

Turns satellite optical bands into an NDVI grid for a forest plot on two dates.

Default source is a deterministic SAMPLE scene so the demo runs offline with
`python app.py` and no API keys. The band math is the real Sentinel-2 formula:

        NDVI = (NIR - RED) / (NIR + RED)        (B08 - B04) / (B08 + B04)

Real imagery: Microsoft Planetary Computer exposes a free, no-auth STAC API for
Sentinel-2 L2A. `search_stac()` below really queries it for scene IDs + dates
over a bounding box; pixel/COG reads need rasterio and are left as the documented
production path. The prototype runs the full pipeline on representative pixels so
the logic is exercised end to end.
"""

import json
import random
import urllib.request

# --- the plot under verification (a real place; coords -> geohash-style key) ---
PLOT = {
    "project_id": "CT-REDD-0417",
    "name": "Rio Jari reforestation unit, Para, Brazil",
    "lat": -0.9167,
    "lon": -52.5000,
    "geohash": "6rnuqg7",          # ~1 km cell containing the plot centroid
    "hectares": 118.0,              # project area the sampled grid represents
}

GRID = 16                          # NxN sampled cells (representative of the plot)
EPS = 1e-6

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"


# ---------------------------------------------------------------- band sampling
def _reflectance(which, seed):
    """
    Representative Sentinel-2 surface reflectance (0..1) for RED (B04) and
    NIR (B08). The plot holds a degraded patch that is regrowing: on the 'after'
    date the patch's NIR rises and RED falls, so NDVI increases there -- the
    signal of real sequestration the oracle will later cross-check.
    """
    rng = random.Random(seed)
    red = [[0.0] * GRID for _ in range(GRID)]
    nir = [[0.0] * GRID for _ in range(GRID)]
    # a roughly circular degraded patch, centre-ish
    cx, cy, r = 7.5, 8.0, 5.5
    regrowth = 0.0 if which == "before" else 0.62   # fraction recovered
    for y in range(GRID):
        for x in range(GRID):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            in_patch = d < r
            # healthy forest baseline
            base_nir = 0.42 + rng.uniform(-0.03, 0.03)
            base_red = 0.045 + rng.uniform(-0.01, 0.01)
            if in_patch:
                # degraded -> low NIR, high RED; regrowth pushes back toward forest
                deg = (1.0 - d / r)                     # 1 at centre, 0 at edge
                nir_v = base_nir - deg * 0.26 * (1.0 - regrowth)
                red_v = base_red + deg * 0.085 * (1.0 - regrowth)
            else:
                nir_v, red_v = base_nir, base_red
            nir[y][x] = max(0.01, nir_v)
            red[y][x] = max(0.005, red_v)
    return red, nir


def ndvi_grid(red, nir):
    """Elementwise NDVI = (NIR - RED) / (NIR + RED)."""
    return [
        [(nir[y][x] - red[y][x]) / (nir[y][x] + red[y][x] + EPS) for x in range(GRID)]
        for y in range(GRID)
    ]


def fetch_scene(which, seed=None):
    """
    Return one dated scene: {date, scene_id, source, ndvi, red, nir}.
    `which` is 'before' or 'after'. Deterministic for a given seed.
    """
    if seed is None:
        seed = 20230115 if which == "before" else 20240820
    date = "2023-01-15" if which == "before" else "2024-08-20"
    scene_id = ("S2A_MSIL2A_%sT%s_T22NBM" %
                (date.replace("-", ""), "131241" if which == "before" else "131249"))
    red, nir = _reflectance(which, seed)
    return {
        "date": date,
        "scene_id": scene_id,
        "source": "sample",            # 'stac' when wired to real imagery
        "ndvi": ndvi_grid(red, nir),
        "red": red,
        "nir": nir,
    }


# -------------------------------------------------- optional: real STAC discovery
def search_stac(bbox=None, datetime_range="2023-01-01/2024-12-31", limit=3, timeout=8):
    """
    Really query Microsoft Planetary Computer for Sentinel-2 L2A scenes over the
    plot. Returns a list of {id, datetime, cloud}. Network-optional: returns []
    on any failure so the prototype never breaks. No API key required.
    """
    if bbox is None:
        d = 0.03
        bbox = [PLOT["lon"] - d, PLOT["lat"] - d, PLOT["lon"] + d, PLOT["lat"] + d]
    body = json.dumps({
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox,
        "datetime": datetime_range,
        "query": {"eo:cloud_cover": {"lt": 20}},
        "limit": limit,
    }).encode()
    try:
        req = urllib.request.Request(
            STAC_URL, data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            feats = json.load(r).get("features", [])
        return [{
            "id": f["id"],
            "datetime": f["properties"].get("datetime"),
            "cloud": f["properties"].get("eo:cloud_cover"),
        } for f in feats]
    except Exception:
        return []
