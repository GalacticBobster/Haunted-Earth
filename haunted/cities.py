"""~120 large / hazard-exposed cities: (name, lat, lon, population in millions (approx. metro), coastal)."""
CITIES = [
    ("Tokyo, Japan", 35.68, 139.69, 37.4, True), ("Delhi, India", 28.61, 77.21, 32.9, False),
    ("Shanghai, China", 31.23, 121.47, 29.0, True), ("Dhaka, Bangladesh", 23.81, 90.41, 23.0, False),
    ("São Paulo, Brazil", -23.55, -46.63, 22.6, False), ("Mexico City, Mexico", 19.43, -99.13, 22.3, False),
    ("Cairo, Egypt", 30.04, 31.24, 22.0, False), ("Beijing, China", 39.90, 116.41, 21.8, False),
    ("Mumbai, India", 19.08, 72.88, 21.3, True), ("Osaka, Japan", 34.69, 135.50, 19.0, True),
    ("New York, USA", 40.71, -74.01, 18.9, True), ("Karachi, Pakistan", 24.86, 67.01, 17.0, True),
    ("Chongqing, China", 29.56, 106.55, 17.0, False), ("Kinshasa, DR Congo", -4.44, 15.27, 16.0, False),
    ("Lagos, Nigeria", 6.52, 3.38, 15.9, True), ("Istanbul, Türkiye", 41.01, 28.98, 15.8, True),
    ("Buenos Aires, Argentina", -34.60, -58.38, 15.5, True), ("Kolkata, India", 22.57, 88.36, 15.3, False),
    ("Manila, Philippines", 14.60, 120.98, 14.7, True), ("Guangzhou, China", 23.13, 113.26, 14.0, False),
    ("Tianjin, China", 39.34, 117.36, 14.0, True), ("Lahore, Pakistan", 31.55, 74.34, 13.9, False),
    ("Rio de Janeiro, Brazil", -22.91, -43.17, 13.7, True), ("Bengaluru, India", 12.97, 77.59, 13.6, False),
    ("Shenzhen, China", 22.54, 114.06, 13.0, True), ("Moscow, Russia", 55.76, 37.62, 12.6, False),
    ("Los Angeles, USA", 34.05, -118.24, 12.5, True), ("Chennai, India", 13.08, 80.27, 11.8, True),
    ("Bogotá, Colombia", 4.71, -74.07, 11.5, False), ("Jakarta, Indonesia", -6.21, 106.85, 11.2, True),
    ("Lima, Peru", -12.05, -77.04, 11.2, True), ("Paris, France", 48.86, 2.35, 11.1, False),
    ("Bangkok, Thailand", 13.76, 100.50, 11.0, True), ("Hyderabad, India", 17.39, 78.49, 10.8, False),
    ("Seoul, South Korea", 37.57, 126.98, 10.0, False), ("London, UK", 51.51, -0.13, 9.6, False),
    ("Nagoya, Japan", 35.18, 136.91, 9.5, True), ("Tehran, Iran", 35.69, 51.39, 9.5, False),
    ("Ho Chi Minh City, Vietnam", 10.82, 106.63, 9.3, True), ("Luanda, Angola", -8.84, 13.23, 9.0, True),
    ("Chicago, USA", 41.88, -87.63, 8.9, False), ("Ahmedabad, India", 23.02, 72.57, 8.6, False),
    ("Kuala Lumpur, Malaysia", 3.14, 101.69, 8.4, False), ("Hanoi, Vietnam", 21.03, 105.85, 8.0, False),
    ("Surat, India", 21.17, 72.83, 7.8, True), ("Riyadh, Saudi Arabia", 24.71, 46.68, 7.7, False),
    ("Hong Kong", 22.32, 114.17, 7.6, True), ("Baghdad, Iraq", 33.31, 44.36, 7.5, False),
    ("Dar es Salaam, Tanzania", -6.79, 39.21, 7.4, True), ("Houston, USA", 29.76, -95.37, 7.1, True),
    ("Taipei, Taiwan", 25.03, 121.57, 7.0, True), ("Pune, India", 18.52, 73.86, 7.0, False),
    ("Santiago, Chile", -33.45, -70.67, 6.9, False), ("Madrid, Spain", 40.42, -3.70, 6.7, False),
    ("Dallas, USA", 32.78, -96.80, 6.5, False), ("San Francisco Bay Area, USA", 37.77, -122.42, 6.3, True),
    ("Toronto, Canada", 43.65, -79.38, 6.3, False), ("Miami, USA", 25.76, -80.19, 6.2, True),
    ("Johannesburg, South Africa", -26.20, 28.05, 6.2, False), ("Belo Horizonte, Brazil", -19.92, -43.94, 6.2, False),
    ("Atlanta, USA", 33.75, -84.39, 6.1, False), ("Singapore", 1.35, 103.82, 6.0, True),
    ("Khartoum, Sudan", 15.50, 32.56, 6.0, False), ("Philadelphia, USA", 39.95, -75.17, 5.8, False),
    ("Barcelona, Spain", 41.39, 2.17, 5.6, True), ("Yangon, Myanmar", 16.84, 96.17, 5.6, True),
    ("Fukuoka, Japan", 33.59, 130.40, 5.5, True), ("Abidjan, Côte d'Ivoire", 5.36, -4.01, 5.5, True),
    ("Saint Petersburg, Russia", 59.93, 30.36, 5.5, True), ("Alexandria, Egypt", 31.20, 29.92, 5.4, True),
    ("Washington DC, USA", 38.91, -77.04, 5.4, False), ("Guadalajara, Mexico", 20.66, -103.35, 5.3, False),
    ("Ankara, Türkiye", 39.93, 32.86, 5.3, False), ("Chittagong, Bangladesh", 22.36, 91.78, 5.3, True),
    ("Sydney, Australia", -33.87, 151.21, 5.3, True), ("Melbourne, Australia", -37.81, 144.96, 5.1, True),
    ("Nairobi, Kenya", -1.29, 36.82, 5.1, False), ("Monterrey, Mexico", 25.69, -100.32, 5.1, False),
    ("Addis Ababa, Ethiopia", 9.03, 38.74, 5.0, False), ("Cape Town, South Africa", -33.92, 18.42, 4.8, True),
    ("Kabul, Afghanistan", 34.56, 69.21, 4.4, False), ("Rome, Italy", 41.90, 12.50, 4.3, False),
    ("Seattle, USA", 47.61, -122.33, 4.0, True), ("Casablanca, Morocco", 33.57, -7.59, 3.7, True),
    ("Kampala, Uganda", 0.35, 32.58, 3.7, False), ("Busan, South Korea", 35.18, 129.08, 3.4, True),
    ("Athens, Greece", 37.98, 23.73, 3.2, True), ("Tampa, USA", 27.95, -82.46, 3.2, True),
    ("Cebu, Philippines", 10.32, 123.89, 3.0, True), ("Naples, Italy", 40.85, 14.27, 3.0, True),
    ("Izmir, Türkiye", 38.42, 27.14, 3.0, True), ("Guayaquil, Ecuador", -2.19, -79.89, 3.0, True),
    ("Lisbon, Portugal", 38.72, -9.14, 2.9, True), ("Caracas, Venezuela", 10.48, -66.90, 2.9, False),
    ("Port-au-Prince, Haiti", 18.59, -72.31, 2.8, True), ("Kaohsiung, Taiwan", 22.63, 120.30, 2.7, True),
    ("Sapporo, Japan", 43.06, 141.35, 2.6, True), ("Vancouver, Canada", 49.28, -123.12, 2.6, True),
    ("Brisbane, Australia", -27.47, 153.03, 2.6, True), ("Accra, Ghana", 5.60, -0.19, 2.5, True),
    ("Medan, Indonesia", 3.59, 98.67, 2.5, False), ("San Juan, Puerto Rico", 18.47, -66.11, 2.4, True),
    ("Havana, Cuba", 23.11, -82.37, 2.1, True), ("Perth, Australia", -31.95, 115.86, 2.1, True),
    ("Quito, Ecuador", -0.18, -78.47, 2.0, False), ("Davao, Philippines", 7.19, 125.46, 1.8, True),
    ("Auckland, New Zealand", -36.85, 174.76, 1.7, True), ("Kathmandu, Nepal", 27.72, 85.32, 1.5, False),
    ("Makassar, Indonesia", -5.15, 119.43, 1.5, True), ("New Orleans, USA", 29.95, -90.07, 1.3, True),
    ("Da Nang, Vietnam", 16.05, 108.20, 1.2, True), ("Islamabad, Pakistan", 33.68, 73.05, 1.2, False),
    ("Sendai, Japan", 38.27, 140.87, 1.1, True), ("Padang, Indonesia", -0.95, 100.35, 1.0, True),
    ("Valparaíso, Chile", -33.05, -71.61, 1.0, True), ("Honolulu, USA", 21.31, -157.86, 1.0, True),
    ("Acapulco, Mexico", 16.85, -99.88, 0.9, True), ("Denpasar (Bali), Indonesia", -8.65, 115.22, 0.9, True),
    ("Colombo, Sri Lanka", 6.93, 79.86, 0.8, True), ("Wellington, New Zealand", -41.29, 174.78, 0.4, True),
    ("Christchurch, New Zealand", -43.53, 172.64, 0.4, True), ("Antofagasta, Chile", -23.65, -70.40, 0.4, True),
    ("Anchorage, USA", 61.22, -149.90, 0.3, True), ("Naha (Okinawa), Japan", 26.21, 127.68, 0.3, True),
    ("Hualien, Taiwan", 23.99, 121.60, 0.3, True), ("Catania, Italy", 37.50, 15.09, 0.3, True),
    ("Reykjavík, Iceland", 64.15, -21.94, 0.2, True), ("Guam", 13.44, 144.79, 0.15, True),
    ("Darwin, Australia", -12.46, 130.84, 0.15, True),
]


def slug(name: str) -> str:
    import re
    return "city-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:36]


def population(place: dict) -> float:
    """Approximate metro population (people) for a watched place; default 200k if unknown."""
    key = place.get("name", "").split(",")[0].lower()
    for name, _, _, pop, _ in CITIES:
        if name.split(",")[0].lower() == key or slug(name) == place.get("id"):
            return pop * 1e6
    return 2e5


def nearest(lat: float, lon: float, km: float = 600, k: int = 6) -> list[tuple[float, tuple]]:
    from .physics import haversine_km
    out = sorted(((haversine_km(lat, lon, c[1], c[2]), c) for c in CITIES), key=lambda x: x[0])
    return [x for x in out if x[0] <= km][:k]
