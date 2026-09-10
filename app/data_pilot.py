"""
BiyoPusula - Konya pilot senaryosu.

ÖNEMLİ ETİKETLEME (proje çalışma kuralımız):
- Konum/koordinatlar: Konya ilçe merkezlerinin GERÇEK, yaklaşık coğrafi konumlarıdır
  (kamuya açık coğrafi bilgi). Mesafe hesapları bu yüzden gerçek geografyaya dayanır.
- Üretici sayısı, miktarlar (ton) ve hazır olma tarihleri: [TEMSİLİ SENARYO].
  Henüz gerçek üretici/tesis görüşmesiyle doğrulanmamıştır.
- Tesis konumu (Çumra): PDR'de ve saha araştırmamızda tespit ettiğimiz gerçek biyogaz
  tesislerinin (Akoda Enerji, Beyaz Piramit) bulunduğu ilçeye göre seçilmiştir; ancak
  bu tesislerin gerçek kapasite/talep verisi elimizde YOKTUR - kapasite değeri [VARSAYIM]dır.
- Araç maliyet/yakıt/emisyon varsayımları: models.py içinde ayrıca etiketlenmiştir.

Bu senaryo, saha görüşmesi tamamlanana kadar YALNIZCA teknik doğrulama (optimizasyon
motorunun çalıştığını göstermek ve manuel plana göre iyileşmeyi ölçmek) amaçlıdır.
CDR raporunda bu veri seti kesinlikle [TEMSİLİ SENARYO] olarak etiketlenmeli, gerçek
saha/test sonucu gibi sunulmamalıdır.
"""
from .models import Producer, Facility, Vehicle

# Konya ilçe merkezlerinin yaklaşık gerçek koordinatları (kamuya açık coğrafi bilgi)
DISTRICT_COORDS = {
    "Selçuklu": (37.9250, 32.5000),
    "Meram": (37.8300, 32.4200),
    "Karatay": (37.8800, 32.5500),
    "Çumra": (37.5667, 32.7667),
    "Sarayönü": (38.2667, 31.9333),
    "Kulu": (39.0900, 33.0800),
    "Cihanbeyli": (38.6500, 32.9167),
    "Altınekin": (38.3167, 32.6833),
    "Akşehir": (38.3564, 31.4144),
    "Ilgın": (38.2814, 31.9106),
    "Yunak": (38.8167, 31.7333),
    "Doğanhisar": (38.0333, 31.4167),
}


def get_facility() -> Facility:
    lat, lon = DISTRICT_COORDS["Çumra"]
    return Facility(
        id="TESIS-1",
        name="Pilot Biyokütle Tesisi (Çumra)",
        district="Çumra",
        lat=lat,
        lon=lon,
        required_type="Mısır sapı",
        daily_capacity_tons=120.0,  # [VARSAYIM]
    )


def get_producers() -> list:
    # (district, ton, hazır tarih) - [TEMSİLİ SENARYO]
    raw = [
        ("Sarayönü", 8, "2026-09-10"),
        ("Selçuklu", 12, "2026-09-10"),
        ("Karatay", 15, "2026-09-10"),
        ("Meram", 6, "2026-09-10"),
        ("Cihanbeyli", 20, "2026-09-10"),
        ("Kulu", 10, "2026-09-10"),
        ("Altınekin", 18, "2026-09-10"),
        ("Akşehir", 9, "2026-09-10"),
        ("Ilgın", 14, "2026-09-10"),
        ("Yunak", 11, "2026-09-10"),
    ]
    producers = []
    for i, (district, ton, ready) in enumerate(raw, start=1):
        lat, lon = DISTRICT_COORDS[district]
        producers.append(
            Producer(
                id=f"URET-{i}",
                name=f"Üretici {i} ({district})",
                district=district,
                lat=lat,
                lon=lon,
                biomass_type="Mısır sapı",
                quantity_tons=ton,
                ready_date=ready,
            )
        )
    return producers


def get_vehicles() -> list:
    # 3 araç, farklı kapasiteler - [TEMSİLİ SENARYO]
    return [
        Vehicle(id="ARAC-1", capacity_tons=20.0),
        Vehicle(id="ARAC-2", capacity_tons=15.0),
        Vehicle(id="ARAC-3", capacity_tons=25.0),
    ]


def get_pilot_scenario():
    return get_producers(), get_facility(), get_vehicles()
