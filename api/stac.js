// CarbonTruth — live Sentinel-2 scene discovery (Vercel serverless function).
// Queries Microsoft's Planetary Computer STAC API (free, no key) for recent
// Sentinel-2 L2A scenes over the selected plot. Runs server-side, so the
// browser never hits a CORS wall. Mirrors ct/satellite.py::search_stac().

export default async function handler(req, res) {
  const lat = parseFloat(req.query.lat) || -0.9167;
  const lon = parseFloat(req.query.lon) || -52.5;
  const d = 0.03;
  const body = {
    collections: ["sentinel-2-l2a"],
    bbox: [lon - d, lat - d, lon + d, lat + d],
    datetime: "2023-01-01/2024-12-31",
    query: { "eo:cloud_cover": { lt: 20 } },
    limit: 4,
  };
  try {
    const r = await fetch(
      "https://planetarycomputer.microsoft.com/api/stac/v1/search",
      {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(8000),
      }
    );
    const j = await r.json();
    const scenes = (j.features || []).map((f) => ({
      id: f.id,
      datetime: f.properties?.datetime,
      cloud: f.properties?.["eo:cloud_cover"],
    }));
    res.setHeader("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400");
    res.status(200).json({ scenes, source: "planetary-computer" });
  } catch (e) {
    // graceful: the site falls back to its bundled sample scene IDs
    res.status(200).json({ scenes: [], error: String(e) });
  }
}
