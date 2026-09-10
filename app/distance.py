"""
Mesafe hesaplama.

NOT: Burada "kuş uçuşu" (great-circle / haversine) mesafe kullanılmaktadır - gerçek
kara yolu mesafesi değildir. Bu bilinçli bir MVP sınırlamasıdır: gerçek yol mesafesi
için bir yol ağı/rota servisi (örn. OSRM, OpenRouteService) entegrasyonu gerekir.
Haversine mesafesi, gerçek yol mesafesine göre genellikle %20-30 daha kısa çıkar;
CDR raporunda bu sınırlama açıkça belirtilmelidir.
"""
import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0  # Dünya yarıçapı, km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def build_distance_matrix(nodes: list) -> list:
    """nodes: [(lat, lon), ...] - index 0 depo/tesis olmalı."""
    n = len(nodes)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine_km(nodes[i][0], nodes[i][1], nodes[j][0], nodes[j][1])
    return matrix
