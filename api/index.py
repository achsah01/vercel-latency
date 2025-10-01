from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import numpy as np

app = FastAPI()

# ✅ Enable CORS for all origins and POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data once at startup
with open("q-vercel-latency.json", "r") as f:
    telemetry_data = json.load(f)

@app.post("/")
async def check_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    results = {}

    for region in regions:
        if region not in telemetry_data:
            continue

        records = telemetry_data[region]
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime"] for r in records]

        if not latencies:
            continue

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > threshold)

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches
        }

    return JSONResponse(content=results)

@app.options("/")
async def options_handler():
    # Handle preflight CORS requests
    return JSONResponse(content={"message": "OK"})
