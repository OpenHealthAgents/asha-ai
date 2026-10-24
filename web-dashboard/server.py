"""
SevaFirst Unified Web Dashboard & Interactive Simulator Server.
Runs on Port 3000.
Serves:
1. ASHA Mobile Field Copilot Simulator (DrGodly-Mobile-Aplication)
2. PHC Medical Officer Command Center (bezs-hms)
3. Clinical Impact & Observability Telemetry Dashboard (bezs-observability)
4. System Mesh Ports & Microservice Explorer
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from pathlib import Path

app = FastAPI(title="SevaFirst Frontline Web Dashboard")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def get_index():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def get_health():
    return {"status": "healthy", "service": "sevafirst-web-dashboard", "port": 3000}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
