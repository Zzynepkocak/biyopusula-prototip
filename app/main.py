"""
BiyoPusula - CDR prototip API'si.

Çalıştırma: uvicorn app.main:app --reload --port 8000
Sonra tarayıcıda: http://localhost:8000
"""
from dataclasses import asdict

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .data_pilot import get_pilot_scenario
from .optimizer import solve_cvrp
from .baseline import solve_baseline
from .kpi import compute_kpis, compute_delta

app = FastAPI(title="BiyoPusula Prototip API")


def _route_to_dict(r):
    d = asdict(r)
    d["doluluk_yuzde"] = round(r.load_factor() * 100, 1)
    return d


@app.get("/api/scenario")
def get_scenario():
    producers, facility, vehicles = get_pilot_scenario()
    return {
        "uyari": "Bu veri seti [TEMSİLİ SENARYO]'dir; gerçek saha görüşmesiyle doğrulanmamıştır.",
        "uretici_sayisi": len(producers),
        "uretici_listesi": [asdict(p) for p in producers],
        "tesis": asdict(facility),
        "araclar": [asdict(v) for v in vehicles],
    }


@app.get("/api/compare")
def compare():
    producers, facility, vehicles = get_pilot_scenario()

    baseline_routes = solve_baseline(producers, facility, vehicles)
    baseline_kpi = compute_kpis(baseline_routes, vehicles, solve_seconds=None)

    optimized_routes, _dm, solve_seconds, status = solve_cvrp(producers, facility, vehicles)
    optimized_kpi = compute_kpis(optimized_routes, vehicles, solve_seconds=solve_seconds)

    delta = compute_delta(baseline_kpi, optimized_kpi)

    return {
        "durum": status,
        "uyari": (
            "Bu karşılaştırma [TEMSİLİ SENARYO] veri seti üzerinde çalıştırılmıştır. "
            "km/maliyet/CO2e rakamları gerçek saha ölçümü DEĞİLDİR; algoritmanın "
            "çalıştığını ve manuel plana göre yönünü göstermek amaçlıdır."
        ),
        "manuel_plan": {
            "rotalar": [_route_to_dict(r) for r in baseline_routes],
            "kpi": baseline_kpi,
        },
        "optimize_plan": {
            "rotalar": [_route_to_dict(r) for r in optimized_routes],
            "kpi": optimized_kpi,
        },
        "degisim": delta,
    }


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
