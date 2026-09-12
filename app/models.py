"""
BiyoPusula - temel veri modelleri.

Bu dosyadaki alanlar PDR raporunda tanımlanan veri setine dayanır:
Üretici (konum, biyokütle türü, miktar, hazır olma tarihi),
Tesis (konum, talep, kabul kapasitesi), Araç (kapasite, maliyet/emisyon varsayımları).
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Producer:
    id: str
    name: str
    district: str
    lat: float
    lon: float
    biomass_type: str
    quantity_tons: float
    ready_date: str  # YYYY-MM-DD, [TEMSİLİ SENARYO]


@dataclass
class Facility:
    id: str
    name: str
    district: str
    lat: float
    lon: float
    required_type: str
    daily_capacity_tons: float


@dataclass
class Vehicle:
    id: str
    capacity_tons: float
    # --- Varsayımlar (aşağıdaki üç alan [VARSAYIM] veya [LİTERATÜR VERİSİ] olarak etiketlidir,
    # gerçek teklif/fatura verisiyle güncellenmelidir) ---
    cost_per_km_try: float = 25.53  # yalnızca yakıt gideri, dayanak 0,28 L/km × 91,19 TL/L (Konya, 10 Eylül 2026).
    # güncel motorin fiyatıyla (≈88,9 TL/L, Eylül 2026) yakıt bileşeni tek başına
    # ~24,9 TL/km'dir - bu katsayı gerçekçi bir taban değil, göreli karşılaştırma içindir  
    fuel_l_per_km: float = 0.28  # [VARSAYIM] ~28 L/100km, orta ölçekli kamyon için tipik aralık
    co2e_kg_per_liter_diesel: float = 2.51072  # [LİTERATÜR VERİSİ] DEFRA 2020 dizel dönüşüm faktörü


@dataclass
class RouteStop:
    producer_id: str
    producer_name: str
    quantity_tons: float


@dataclass
class Route:
    vehicle_id: str
    vehicle_capacity_tons: float
    stops: list  # list[RouteStop]
    distance_km: float
    load_tons: float = 0.0

    def load_factor(self) -> float:
        if self.vehicle_capacity_tons <= 0:
            return 0.0
        return self.load_tons / self.vehicle_capacity_tons
