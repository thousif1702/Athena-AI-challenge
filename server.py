from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
WIDGET_URI = "ui://widget/quake-explorer.html"
HERE = Path(__file__).parent

mcp = FastMCP("earthquake-explorer", host="0.0.0.0", port=8787)


@mcp.resource(WIDGET_URI, mime_type="text/html+skybridge")
def widget() -> str:
    return (HERE / "widget.html").read_text(encoding="utf-8")


@mcp.tool(
    name="search_earthquakes",
    description=(
        "Use this when the user asks about recent earthquakes, seismic activity, "
        "quakes near a place, or quakes above a magnitude or in a time range. "
        "Fetches real events from the USGS catalog and shows an interactive map. "
        "Do not use for forecasts or predictions."
    ),
    meta={
        "openai/outputTemplate": WIDGET_URI,
        "openai/widgetAccessible": True,
        "openai/toolInvocation/invoking": "Fetching earthquakes from USGS…",
        "openai/toolInvocation/invoked": "Earthquakes loaded",
    },
    annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, openWorldHint=True
    ),
)
async def search_earthquakes(
    min_magnitude: Annotated[float, Field(description="Minimum magnitude, 0-9. Default 4.0")] = 4.0,
    days: Annotated[int, Field(description="Look-back window in days, 1-30. Default 7")] = 7,
    place: Annotated[str, Field(description="Optional place text filter, e.g. 'Japan', 'California', 'Chile'")] = "",
    limit: Annotated[int, Field(description="Max events to return, 1-500")] = 300,
) -> dict[str, Any]:
    min_magnitude = max(0.0, min(9.0, float(min_magnitude)))
    days = max(1, min(30, int(days)))
    limit = max(1, min(500, int(limit)))
    place = (place or "").strip()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": min_magnitude,
        "orderby": "time",
        "limit": 5000 if place else limit,
    }
    query = {"min_magnitude": min_magnitude, "days": days, "place": place}

    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "athena-quake-explorer/1.0"}) as client:
            r = await client.get(USGS_URL, params=params)
            r.raise_for_status()
            features = r.json().get("features", [])
    except Exception as exc:  # noqa: BLE001
        return {"query": query, "count": 0, "events": [], "stats": {}, "error": f"USGS request failed: {exc}"}

    events = []
    for f in features:
        p, g = f.get("properties", {}), f.get("geometry", {}).get("coordinates", [None, None, None])
        if p.get("mag") is None or g[0] is None:
            continue
        name = p.get("place") or "Unknown location"
        if place and place.lower() not in name.lower():
            continue
        events.append({
            "id": f.get("id"),
            "mag": round(float(p["mag"]), 1),
            "depth": round(float(g[2] or 0), 1),
            "lat": round(g[1], 3),
            "lon": round(g[0], 3),
            "place": name,
            "time": p.get("time"),
            "url": p.get("url"),
            "tsunami": bool(p.get("tsunami")),
        })
    events = events[:limit]

    stats = {}
    if events:
        top = max(events, key=lambda e: e["mag"])
        stats = {
            "strongest_mag": top["mag"],
            "strongest_place": top["place"],
            "avg_depth_km": round(sum(e["depth"] for e in events) / len(events), 1),
            "m5_plus": sum(1 for e in events if e["mag"] >= 5),
        }
    return {"query": query, "count": len(events), "events": events, "stats": stats, "source": "USGS Earthquake Catalog"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")