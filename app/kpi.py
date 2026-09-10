"""
KPI hesaplama - PDR raporunda tanımlanan ölçüm göstergeleri.

Etiketleme:
- toplam_km, sefer_sayisi, ortalama_doluluk_yuzde: doğrudan üretilen plandan
  hesaplanır -> bu çalışma için [TEST SONUCU] (gerçek saha verisi değil,
  [TEMSİLİ SENARYO] veri setinde çalıştırılmış gerçek bir algoritma çıktısıdır).
- tahmini_maliyet_try, tahmini_co2e_kg: KPI hesaplaması gerçek ama girdi
  katsayıları (TL/km, L/km) [VARSAYIM]; CO2e katsayısı [LİTERATÜR VERİSİ]
  (DEFRA 2020 dizel dönüşüm faktörü, bkz. models.py).
- plan_olusturma_suresi_sn: optimizer.py içinde GERÇEKTEN ölçülen süredir
  ([TEST SONUCU] - bu, temsili veri seti üzerinde de olsa gerçek bir ölçümdür).
"""


def compute_kpis(routes: list, vehicles: list, solve_seconds: float = None) -> dict:
    if not routes:
        return {
            "toplam_km": 0.0,
            "sefer_sayisi": 0,
            "ortalama_doluluk_yuzde": 0.0,
            "tahmini_maliyet_try": 0.0,
            "tahmini_co2e_kg": 0.0,
            "plan_olusturma_suresi_sn": solve_seconds,
            "toplam_taban_miktar": 0.0,
        }

    vehicle_by_id = {v.id: v for v in vehicles}

    toplam_km = sum(r.distance_km for r in routes)
    sefer_sayisi = len(routes)
    doluluk_oranlari = [r.load_factor() for r in routes]
    ortalama_doluluk = sum(doluluk_oranlari) / len(doluluk_oranlari) if doluluk_oranlari else 0.0

    tahmini_maliyet = 0.0
    tahmini_co2e = 0.0
    for r in routes:
        base_vehicle_id = r.vehicle_id.split(" (")[0]
        v = vehicle_by_id.get(base_vehicle_id)
        cost_per_km = v.cost_per_km_try if v else 15.0
        fuel_l_per_km = v.fuel_l_per_km if v else 0.28
        co2e_factor = v.co2e_kg_per_liter_diesel if v else 2.51072
        tahmini_maliyet += r.distance_km * cost_per_km
        tahmini_co2e += r.distance_km * fuel_l_per_km * co2e_factor

    toplam_taban_miktar = sum(r.load_tons for r in routes)

    return {
        "toplam_km": round(toplam_km, 1),
        "sefer_sayisi": sefer_sayisi,
        "ortalama_doluluk_yuzde": round(ortalama_doluluk * 100, 1),
        "tahmini_maliyet_try": round(tahmini_maliyet, 0),
        "tahmini_co2e_kg": round(tahmini_co2e, 1),
        "plan_olusturma_suresi_sn": round(solve_seconds, 3) if solve_seconds is not None else None,
        "toplam_taban_miktar": round(toplam_taban_miktar, 1),
    }


def compute_delta(baseline_kpi: dict, optimized_kpi: dict) -> dict:
    def pct_change(old, new):
        if not old:
            return 0.0
        return round((new - old) / old * 100, 1)

    return {
        "delta_km": round(optimized_kpi["toplam_km"] - baseline_kpi["toplam_km"], 1),
        "delta_km_pct": pct_change(baseline_kpi["toplam_km"], optimized_kpi["toplam_km"]),
        "delta_sefer": optimized_kpi["sefer_sayisi"] - baseline_kpi["sefer_sayisi"],
        "delta_doluluk_puan": round(
            optimized_kpi["ortalama_doluluk_yuzde"] - baseline_kpi["ortalama_doluluk_yuzde"], 1
        ),
        "delta_maliyet_try": round(
            optimized_kpi["tahmini_maliyet_try"] - baseline_kpi["tahmini_maliyet_try"], 0
        ),
        "delta_maliyet_pct": pct_change(
            baseline_kpi["tahmini_maliyet_try"], optimized_kpi["tahmini_maliyet_try"]
        ),
        "delta_co2e_kg": round(
            optimized_kpi["tahmini_co2e_kg"] - baseline_kpi["tahmini_co2e_kg"], 1
        ),
        "delta_co2e_pct": pct_change(
            baseline_kpi["tahmini_co2e_kg"], optimized_kpi["tahmini_co2e_kg"]
        ),
    }
