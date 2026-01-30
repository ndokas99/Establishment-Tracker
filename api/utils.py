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
    "restaurant|food|cafe": "Restaurants and food outlets",
    "marketplace|supermarket|retail|trade|wholesale": "Super Markets and Shops",
    "bar|pub|biergarten": "Bars and Pubs",
    "hotel|motel|resort|lodge|cabin": "Hotels and motels",
    "bank|atm|payment_terminal|money_transfer": "Banking and financial institutions",
    "library|research_institute|book|training": "Libraries and Research Institutes",
    "college|university|school": "Education Institutions",
    "language_school": "Language School",
    "driving_school|driver_training": "Driving Schools",
    "parking": "Vehicle parking",
    "wash|repair|vehicle_inspection|weighbridge": "Vehicle services (wash, repair, etc)",
    "fuel": "Gas Stations",
    "rental": "Rental services",
    "arts_centre|casino|music_venue": "Entertainment and Arts",
    "sports|recreation|fitness|leisure|outdoors": "Sports centres and gyms",
    "church|temple|religion": "Church and Temples",
    "theatre|cinema": "Movie and theatre",
    "clinic|dentist|doctors|hospital|pharmacy|veterinary": "Hospital and health institutions",
    "fire_station|post_office|toilets|depot": "Public services (Post office, Toilets)",
    "courthouse|police|prison|ranger" : "Law Enforcement"
}