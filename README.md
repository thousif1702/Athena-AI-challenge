# Athena-AI-challenge# Earthquake Activity Explorer (Athena AI Agent + MCP)

An Athena AI agent that explores recent earthquakes by **magnitude, depth, place and time range**.
It fetches real data from the public **USGS Earthquake Catalog API** through an **MCP server**
and renders the result in an **interactive widget** embedded in the Athena chat.

## Demo flow
1. Ask the agent: "Show earthquakes from the last 7 days above magnitude 4.5".
2. The agent calls the `search_earthquakes` MCP tool, which queries USGS live.
3. An interactive map widget renders inside Athena.

## Data source
- USGS Earthquake Catalog (FDSN Event API): https://earthquake.usgs.gov/fdsnws/event/1/

## MCP tool
| Tool | Purpose | Parameters |
|---|---|---|
| `search_earthquakes` | Fetch recent earthquakes and render the widget | `min_magnitude` (0-9), `days` (1-30), `place` (text filter), `limit` (1-500) |

The tool is read-only and returns `structuredContent` (events and stats) plus the widget template


## Widget interactions
- Magnitude slider that filters events live
- Depth chips (shallow / intermediate / deep) that toggle events by depth
- 24h / 7d / 30d switch that makes a new MCP tool call from inside the widget
- Click a quake on the map or list to see its details
- Sort by strongest, newest or deepest
- Place text filter


## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

## Connect to Athena
1. Create an agent at Athena Platform
2. Paste the MCP URL.
3. Use the system prompt
4. Open the agent and ask about earthquakes.

## Project structure
```
server.py          MCP server 
widget.html        Interactive map widget 
requirements.txt   Python dependencies 
agent_prompt.md    System prompt used for the Athena agent
```
