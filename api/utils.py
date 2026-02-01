from flask import session
from math import cos, sin, atan2, sqrt, pi


def calc_dist(lat2, lon2):
    lat1 = session['lat1']
    lon1 = session['lon1']
    phi1, phi2 = lat1 * pi / 180, lat2 * pi / 180
    phi_diff = (lat2 - lat1) * pi / 180
    lambda_diff = (lon2 - lon1) * pi / 180
    a = sin(phi_diff / 2) ** 2 + cos(phi1) * cos(phi2) * sin(lambda_diff / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(6371 * c, 2)


est_map = {
    "restaurant|food|cafe": ("Restaurants and food outlets", "amenity~"),
    "marketplace|supermarket|retail|trade|wholesale": ("Super Markets and Shops", "shop~"),
    "bar|pub|biergarten": ("Bars and Pubs", "amenity~"),
    "hotel|motel|resort|lodge|cabin|museum": ("Tourism (Hotels and museums)", "tourism~"),
    "bank|atm|payment_terminal|money_transfer": ("Banking and financial institutions", "amenity~"),
    "library|research_institute|book|training": ("Libraries and Research Institutes", "amenity~"),
    "college|university|school": ("Education Institutions", "amenity~"),
    "language_school": ("Language School", "amenity~"),
    "driving_school|driver_training": ("Driving Schools", "amenity~"),
    "parking": ("Vehicle parking", "amenity="),
    "car_wash": ("Car Wash", "amenity~"),
    "car_repair": ("Car repair", "shop~"),
    "fuel": ("Gas Stations", "amenity~"),
    "rental": ("Rental services", "amenity~"),
    "arts_centre|casino|music_venue": ("Entertainment and Arts", "amenity~"),
    "sports|fitness|gym": ("Sports centres and gyms", "leisure~"),
    "worship": ("Church and Temples", "amenity~"),
    "theatre|cinema": ("Movie and theatre", "amenity~"),
    "clinic|dentist|doctors|hospital|pharmacy|veterinary": ("Hospital and health institutions", "amenity~"),
    "fire_station|post_office|toilets|depot": ("Public services (Post office, Toilets)", "amenity~"),
    "courthouse|police|prison|ranger" : ("Law Enforcement", "amenity~"),
    "government": ("Government Offices", "office~")
}