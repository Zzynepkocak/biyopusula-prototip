"""
BiyoPusula optimizasyon motoru - Google OR-Tools tabanlı Kapasiteli Araç Rotalama (CVRP).

Model:
- Düğüm 0 = tesis (depo). Düğüm 1..n = üreticiler (toplama noktaları).
- Her üreticinin "talebi" = toplanacak biyokütle miktarı (ton). Araç, tesisten
  boş çıkar, güzergâh boyunca üreticilerden yük toplar (kümülatif yük artar),
  kümülatif yük hiçbir zaman araç kapasitesini aşamaz, tesise döner.
  (Bu, klasik "teslimat" CVRP'sinin matematiksel olarak simetriği olan bir
  "toplama" (pickup) CVRP'sidir - kapasite kısıtının yönü aynıdır.)
- Amaç fonksiyonu: toplam mesafe + kullanılan her araç için sabit bir "sefer
  maliyeti" cezası. Bu ceza, sistemin gereksiz yere fazla araç/sefer kullanmak
  yerine yakın üreticileri aynı sevkiyatta birleştirmesini teşvik eder - PDR'de
  tanımlanan temel hedefle (doluluk oranını artırma) doğrudan uyumludur.

Not: Zaman pencereleri (hazır olma tarihi / tesis kabul dönemi) bu ilk sürümde
MODELLENMEMİŞTİR - tüm üreticilerin aynı planlama günü için hazır olduğu
varsayılmıştır (bkz. data_pilot.py). Bu bilinçli bir MVP kapsam kararıdır;
CVRPTW (zaman pencereli CVRP) olarak genişletilmesi sonraki bir iterasyon
konusudur.
"""
import time
import os
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from .distance import build_distance_matrix
from .models import Route, RouteStop

FIXED_COST_PER_VEHICLE_TRY = 300  # [VARSAYIM] optimizasyon ceza parametresi - fazla sefer açmayı caydırır. Maliyet modelinin parçası DEĞİLDİR; KPI hesabına (kpi.py) girmez, raporlanan maliyet yalnızca km x TL/km üzerinden hesaplanır.
DISTANCE_SCALE = 1000  # km -> "metre benzeri" tam sayıya çevirmek için (OR-Tools tam sayı ister)
TRIPS_PER_VEHICLE = 4  # bir aracın planlama döneminde yapabileceği varsayılan maksimum sefer sayısı [VARSAYIM]


def solve_cvrp(producers: list, facility, vehicles: list):
    """Dönen: (routes: list[Route], distance_matrix, solve_seconds: float, status: str)

    Not: Toplam üretici talebi tek bir aracın/tek bir seferin kapasitesini çok
    aştığından, her fiziksel araca birden fazla sefer hakkı tanınır
    (TRIPS_PER_VEHICLE). OR-Tools'a bu, aynı fiziksel aracın "sanal kopyaları"
    olarak sunulur; sonuçta kaç sanal kopyanın gerçekten kullanıldığı = gerçek
    sefer sayısıdır.
    """
    t0 = time.perf_counter()

    nodes = [(facility.lat, facility.lon)] + [(p.lat, p.lon) for p in producers]
    distance_matrix_km = build_distance_matrix(nodes)
    n = len(nodes)

    demands = [0] + [int(round(p.quantity_tons)) for p in producers]

    # Her fiziksel aracı TRIPS_PER_VEHICLE kez tekrarlayarak "sefer slotu" oluştur
    slot_vehicle_index = []  # slot -> vehicles listesindeki index
    for vi, _ in enumerate(vehicles):
        for _t in range(TRIPS_PER_VEHICLE):
            slot_vehicle_index.append(vi)
    capacities = [int(round(vehicles[vi].capacity_tons)) for vi in slot_vehicle_index]
    num_slots = len(slot_vehicle_index)

    manager = pywrapcp.RoutingIndexManager(n, num_slots, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return int(round(distance_matrix_km[i][j] * DISTANCE_SCALE))

    transit_cb_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_index)

    def demand_callback(from_index):
        i = manager.IndexToNode(from_index)
        return demands[i]

    demand_cb_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_cb_index,
        0,  # slack yok
        capacities,
        True,  # kümülatif yük depoda 0'dan başlar
        "Capacity",
    )

    for slot in range(num_slots):
        routing.SetFixedCostOfVehicle(int(FIXED_COST_PER_VEHICLE_TRY * DISTANCE_SCALE / 15), slot)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    time_limit_ms = int(os.environ.get("SOLVER_TIME_LIMIT_MS", "5000"))
    search_params.time_limit.FromMilliseconds(time_limit_ms)

    solution = routing.SolveWithParameters(search_params)
    solve_seconds = time.perf_counter() - t0

    if solution is None:
        return [], distance_matrix_km, solve_seconds, "COZUM_BULUNAMADI"

    routes = []
    trip_counter = {}  # fiziksel araç id -> kaçıncı sefer
    for slot in range(num_slots):
        index = routing.Start(slot)
        stops = []
        route_distance_km = 0.0
        load = 0.0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                p = producers[node - 1]
                stops.append(RouteStop(producer_id=p.id, producer_name=p.name, quantity_tons=p.quantity_tons))
                load += p.quantity_tons
            prev_index = index
            index = solution.Value(routing.NextVar(index))
            prev_node = manager.IndexToNode(prev_index)
            next_node = manager.IndexToNode(index)
            route_distance_km += distance_matrix_km[prev_node][next_node]
        if stops:
            vi = slot_vehicle_index[slot]
            vehicle = vehicles[vi]
            trip_counter[vehicle.id] = trip_counter.get(vehicle.id, 0) + 1
            routes.append(
                Route(
                    vehicle_id=f"{vehicle.id} (Sefer {trip_counter[vehicle.id]})",
                    vehicle_capacity_tons=vehicle.capacity_tons,
                    stops=stops,
                    distance_km=round(route_distance_km, 2),
                    load_tons=load,
                )
            )
    return routes, distance_matrix_km, solve_seconds, "COZUM_BULUNDU"
