"""
Manuel / mevcut durum planlayıcısı (karşılaştırma için "baseline").

Bu, PDR'de tarif edilen bugünkü durumu taklit eder: planlamacı üreticileri
listede geldiği sırayla, mesafe/rota optimizasyonu yapmadan araçlara doldurur
("tablo üzerinden, deneyimle" planlama). Araç kapasitesi dolunca bir sonraki
araca geçilir; güzergah sırası da listede geldiği sıradır (en kısa rota için
yeniden sıralama YAPILMAZ). Bu, optimize edilmiş plana karşı dürüst ve
savunulabilir bir karşılaştırma noktası sağlar - yapay şekilde kötüleştirilmiş
bir "kukla" senaryo değildir.
"""
from .distance import haversine_km
from .models import Route, RouteStop


def solve_baseline(producers: list, facility, vehicles: list):
    """Araçlar sırayla (round-robin) kullanılır; bir araç dolduğunda sıradaki
    araca geçilir, araç listesi bitince baştan döner (yani bir araç günde
    birden fazla sefer yapabilir - optimize edilmiş plana adil kıyaslama için).
    Güzergah sırası HER ZAMAN üreticinin orijinal liste sırasıdır (mesafeye
    göre yeniden sıralama yapılmaz) - bu, "manuel/deneyimle planlama" varsayımıdır.
    """
    routes = []
    v_idx = 0
    trip_counter = {}
    current_stops = []
    current_load = 0.0

    def flush_route():
        nonlocal current_stops, current_load
        if not current_stops:
            return
        vehicle = vehicles[v_idx]
        points = [(facility.lat, facility.lon)] + [
            (s["lat"], s["lon"]) for s in current_stops
        ] + [(facility.lat, facility.lon)]
        dist = sum(
            haversine_km(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
            for i in range(len(points) - 1)
        )
        trip_counter[vehicle.id] = trip_counter.get(vehicle.id, 0) + 1
        routes.append(
            Route(
                vehicle_id=f"{vehicle.id} (Sefer {trip_counter[vehicle.id]})",
                vehicle_capacity_tons=vehicle.capacity_tons,
                stops=[RouteStop(s["id"], s["name"], s["qty"]) for s in current_stops],
                distance_km=round(dist, 2),
                load_tons=current_load,
            )
        )
        current_stops = []
        current_load = 0.0

    for p in producers:
        vehicle = vehicles[v_idx]
        if current_load + p.quantity_tons > vehicle.capacity_tons:
            flush_route()
            v_idx = (v_idx + 1) % len(vehicles)
            vehicle = vehicles[v_idx]
        current_stops.append({"id": p.id, "name": p.name, "qty": p.quantity_tons, "lat": p.lat, "lon": p.lon})
        current_load += p.quantity_tons

    flush_route()
    return routes
