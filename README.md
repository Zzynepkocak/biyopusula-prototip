# BiyoPusula – CDR Prototipi

BiyoPusula projesinin CDR (Kritik Tasarım Raporu) aşaması için geliştirilen ilk çalışan
prototip. Bu, PDR'de tarif edilen "biyokütle toplama ve taşıma sürecini optimize eden
web tabanlı karar destek sistemi" fikrinin, kısıtlı bir kapsamda kod olarak
somutlaştırılmış hâlidir.

## Bu prototip ne yapıyor, ne yapmıyor

**Yapıyor:**
- Konya bölgesi için bir üretici/tesis/araç veri setini optimizasyon motoruna verir.
- Google OR-Tools ile kapasiteli araç rotalama (CVRP) problemini çözer: hangi üreticiden
  ne kadar biyokütlenin, hangi araçla, hangi sırayla toplanacağına karar verir.
- Aynı veri setinde "manuel/mevcut durum" tarzı optimize edilmemiş bir plan da üretir.
- İki planı km, sefer sayısı, araç doluluk oranı, tahmini maliyet ve tahmini CO2e
  açısından karşılaştırır.
- Sonuçları basit bir web arayüzünde (tablo + harita) gösterir.

**Yapmıyor (bilinçli MVP kapsam kararları):**
- Zaman pencereleri (hazır olma tarihi / tesis kabul dönemi) henüz modellenmedi -
  tüm üreticiler tek bir planlama günü için hazır kabul ediliyor.
- Gerçek yol mesafesi kullanmıyor (kuş uçuşu/haversine mesafe kullanılıyor).
- Kullanıcı girişi/kimlik doğrulama, veri kalıcılığı (veritabanı) yok - veriler
  şimdilik kod içinde sabit (data_pilot.py).
- React/Next.js/PostgreSQL kullanılmadı; bilinçli olarak hafif bir FastAPI + düz
  HTML/JS arayüzüyle hızlı bir demo hedeflendi (CDR süresi kısıtı nedeniyle).

## Veri ve varsayım etiketleme kuralı

Kod içinde ve arayüzde her sayı şu etiketlerden biriyle işaretlenmiştir (proje
çalışma kuralımız gereği):

- **[TEMSİLİ SENARYO]** - üretici sayısı, miktarlar, hazır olma tarihleri. Gerçek
  saha görüşmesiyle doğrulanmamıştır.
- **[VARSAYIM]** - maliyet/km, yakıt tüketimi/km, sefer başına sabit maliyet gibi
  katsayılar. Gerçek teklif/fatura verisiyle güncellenmelidir.
- **[LİTERATÜR VERİSİ]** - CO2e hesaplamasında kullanılan dizel dönüşüm faktörü
  (2,51072 kg CO2/litre), DEFRA'nın 2020 sera gazı raporlama dönüşüm faktörlerinden
  alınmıştır (bkz. app/models.py içindeki kaynak notu).
- **[TEST SONUCU]** - km/sefer/doluluk karşılaştırma çıktıları ve algoritmanın
  gerçekten ölçülen çalışma süresi. Bunlar gerçek bir algoritma çalıştırmasından
  gelir ama [TEMSİLİ SENARYO] veri seti üzerindedir - saha testi DEĞİLDİR.

CDR raporuna bu prototipten sayı aktarılırken bu etiketlerin korunması, "kanıtlanmamış
başarı yüzdesi" izlenimi vermemek için önemlidir.

## Kurulum ve çalıştırma

```bash
cd biyopusula-prototip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Sonra tarayıcıda `http://localhost:8000` adresini açın. Sayfa otomatik olarak
`/api/compare` uç noktasını çağırıp manuel-vs-optimize karşılaştırmasını hesaplar
(küçük veri setinde birkaç saniye sürebilir).

## Kod yapısı

```
app/
  models.py      -> Producer, Facility, Vehicle, Route veri sınıfları (+ varsayımlar)
  data_pilot.py  -> Konya pilot senaryosu (gerçek ilçe koordinatları + temsili miktarlar)
  distance.py    -> Haversine mesafe hesabı
  optimizer.py   -> OR-Tools CVRP optimizasyon motoru (çoklu sefer destekli)
  baseline.py    -> Manuel/mevcut durum benzetimi (karşılaştırma için)
  kpi.py         -> KPI hesaplama ve iki plan arasındaki fark (delta) hesaplama
  main.py        -> FastAPI uç noktaları (/api/scenario, /api/compare)
  static/index.html -> Basit arayüz (tablo + Leaflet harita)
```

## Sırada ne var (bir sonraki iterasyon için)

1. Gerçek saha görüşmesi verisiyle `data_pilot.py`'yi güncellemek (veya görüşme
   olmazsa BEPA/TÜİK kaynaklı tahminlerle daha savunulabilir hâle getirmek).
2. Zaman pencerelerini (CVRPTW) modele eklemek.
3. Gerçek yol mesafesi için bir routing servisi (OSRM/OpenRouteService) entegre etmek.
4. Üretici/tesis/araç veri girişini arayüzden yapılabilir hâle getirmek (şu an
   sabit veri seti kullanılıyor).
5. Bu çıktıları CDR raporunun "Prototip" ve "İlk Denemeler ve Öğrenimler"
   sayfalarına ekran görüntüleriyle taşımak.
