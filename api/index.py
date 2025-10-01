from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json, math

app = FastAPI()

# CORS: allow POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry from file (placed at repo root)
with open("q-vercel-latency.json", "r") as f:
    telemetry = json.load(f)

def percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    k = (pct / 100.0) * (len(sorted_vals) - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return float(d0 + d1)

@app.post("/")
async def latency_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        region_data = [r for r in telemetry if r.get("region") == region]
        if not region_data:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        latencies = sorted([float(x["latency_ms"]) for x in region_data])
        uptimes = [float(x["uptime_pct"]) for x in region_data]

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = percentile(latencies, 95)
        avg_uptime = sum(uptimes) / len(uptimes)
        breaches = sum(1 for l in latencies if l > threshold)

        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2) if p95_latency is not None else None,
            "avg_uptime": round(avg_uptime, 3),
            "breaches": int(breaches)
        }

    return result
