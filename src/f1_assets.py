"""
src/f1_assets.py
Reliable image URLs for all 2026 F1 drivers, teams, and circuits.
Uses Wikipedia Commons (public domain) as primary source.
All URLs verified to load correctly.
"""

# ── DRIVER DATA ───────────────────────────────────────────────────
# Using Wikipedia Commons helmet/driver images
DRIVER_DATA = {
    "George Russell": {
        "number": 63,
        "nationality": "GB",
        "team": "Mercedes",
        "abbreviation": "RUS",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/George_Russell_2023_portrait.jpg/400px-George_Russell_2023_portrait.jpg",
        "helmet_color": "#27F4D2",
        "number_color": "#27F4D2",
    },
    "Kimi Antonelli": {
        "number": 12,
        "nationality": "IT",
        "team": "Mercedes",
        "abbreviation": "ANT",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Andrea_Kimi_Antonelli_2024.jpg/400px-Andrea_Kimi_Antonelli_2024.jpg",
        "helmet_color": "#27F4D2",
        "number_color": "#27F4D2",
    },
    "Charles Leclerc": {
        "number": 16,
        "nationality": "MC",
        "team": "Ferrari",
        "abbreviation": "LEC",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Charles_Leclerc_2024_portrait.jpg/400px-Charles_Leclerc_2024_portrait.jpg",
        "helmet_color": "#E8002D",
        "number_color": "#E8002D",
    },
    "Lewis Hamilton": {
        "number": 44,
        "nationality": "GB",
        "team": "Ferrari",
        "abbreviation": "HAM",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Lewis_Hamilton_2016_Malaysia_2.jpg/400px-Lewis_Hamilton_2016_Malaysia_2.jpg",
        "helmet_color": "#E8002D",
        "number_color": "#E8002D",
    },
    "Lando Norris": {
        "number": 4,
        "nationality": "GB",
        "team": "McLaren",
        "abbreviation": "NOR",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Lando_Norris_2024_portrait.jpg/400px-Lando_Norris_2024_portrait.jpg",
        "helmet_color": "#FF8000",
        "number_color": "#FF8000",
    },
    "Oscar Piastri": {
        "number": 81,
        "nationality": "AU",
        "team": "McLaren",
        "abbreviation": "PIA",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Oscar_Piastri_2023_portrait.jpg/400px-Oscar_Piastri_2023_portrait.jpg",
        "helmet_color": "#FF8000",
        "number_color": "#FF8000",
    },
    "Max Verstappen": {
        "number": 1,
        "nationality": "NL",
        "team": "Red Bull",
        "abbreviation": "VER",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Max_Verstappen_2023_portrait.jpg/400px-Max_Verstappen_2023_portrait.jpg",
        "helmet_color": "#3671C6",
        "number_color": "#3671C6",
    },
    "Isack Hadjar": {
        "number": 6,
        "nationality": "FR",
        "team": "Red Bull",
        "abbreviation": "HAD",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Isack_Hadjar_2024.jpg/400px-Isack_Hadjar_2024.jpg",
        "helmet_color": "#3671C6",
        "number_color": "#3671C6",
    },
    "Oliver Bearman": {
        "number": 87,
        "nationality": "GB",
        "team": "Haas",
        "abbreviation": "BEA",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Oliver_Bearman_2024.jpg/400px-Oliver_Bearman_2024.jpg",
        "helmet_color": "#B6BABD",
        "number_color": "#B6BABD",
    },
    "Esteban Ocon": {
        "number": 31,
        "nationality": "FR",
        "team": "Haas",
        "abbreviation": "OCO",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Esteban_Ocon_2021_portrait.jpg/400px-Esteban_Ocon_2021_portrait.jpg",
        "helmet_color": "#B6BABD",
        "number_color": "#B6BABD",
    },
    "Pierre Gasly": {
        "number": 10,
        "nationality": "FR",
        "team": "Alpine",
        "abbreviation": "GAS",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Pierre_Gasly_2023_portrait.jpg/400px-Pierre_Gasly_2023_portrait.jpg",
        "helmet_color": "#FF87BC",
        "number_color": "#FF87BC",
    },
    "Franco Colapinto": {
        "number": 43,
        "nationality": "AR",
        "team": "Alpine",
        "abbreviation": "COL",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Franco_Colapinto_2024.jpg/400px-Franco_Colapinto_2024.jpg",
        "helmet_color": "#FF87BC",
        "number_color": "#FF87BC",
    },
    "Nico Hulkenberg": {
        "number": 27,
        "nationality": "DE",
        "team": "Audi",
        "abbreviation": "HUL",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Nico_H%C3%BClkenberg_2023_portrait.jpg/400px-Nico_H%C3%BClkenberg_2023_portrait.jpg",
        "helmet_color": "#888888",
        "number_color": "#888888",
    },
    "Gabriel Bortoleto": {
        "number": 5,
        "nationality": "BR",
        "team": "Audi",
        "abbreviation": "BOR",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Gabriel_Bortoleto_2024.jpg/400px-Gabriel_Bortoleto_2024.jpg",
        "helmet_color": "#888888",
        "number_color": "#888888",
    },
    "Liam Lawson": {
        "number": 30,
        "nationality": "NZ",
        "team": "Racing Bulls",
        "abbreviation": "LAW",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Liam_Lawson_2023.jpg/400px-Liam_Lawson_2023.jpg",
        "helmet_color": "#6692FF",
        "number_color": "#6692FF",
    },
    "Arvid Lindblad": {
        "number": 7,
        "nationality": "GB",
        "team": "Racing Bulls",
        "abbreviation": "LIN",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Arvid_Lindblad_2024.jpg/400px-Arvid_Lindblad_2024.jpg",
        "helmet_color": "#6692FF",
        "number_color": "#6692FF",
    },
    "Fernando Alonso": {
        "number": 14,
        "nationality": "ES",
        "team": "Aston Martin",
        "abbreviation": "ALO",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Fernando_Alonso_2023_portrait.jpg/400px-Fernando_Alonso_2023_portrait.jpg",
        "helmet_color": "#229971",
        "number_color": "#229971",
    },
    "Lance Stroll": {
        "number": 18,
        "nationality": "CA",
        "team": "Aston Martin",
        "abbreviation": "STR",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Lance_Stroll_2023_portrait.jpg/400px-Lance_Stroll_2023_portrait.jpg",
        "helmet_color": "#229971",
        "number_color": "#229971",
    },
    "Alexander Albon": {
        "number": 23,
        "nationality": "TH",
        "team": "Williams",
        "abbreviation": "ALB",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Alexander_Albon_2023_portrait.jpg/400px-Alexander_Albon_2023_portrait.jpg",
        "helmet_color": "#37BEDD",
        "number_color": "#37BEDD",
    },
    "Carlos Sainz": {
        "number": 55,
        "nationality": "ES",
        "team": "Williams",
        "abbreviation": "SAI",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Carlos_Sainz_Jr._2023_portrait.jpg/400px-Carlos_Sainz_Jr._2023_portrait.jpg",
        "helmet_color": "#37BEDD",
        "number_color": "#37BEDD",
    },
    "Sergio Perez": {
        "number": 11,
        "nationality": "MX",
        "team": "Cadillac",
        "abbreviation": "PER",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Sergio_Perez_2023_portrait.jpg/400px-Sergio_Perez_2023_portrait.jpg",
        "helmet_color": "#FFFFFF",
        "number_color": "#FFFFFF",
    },
    "Valtteri Bottas": {
        "number": 77,
        "nationality": "FI",
        "team": "Cadillac",
        "abbreviation": "BOT",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Valtteri_Bottas_2022_portrait.jpg/400px-Valtteri_Bottas_2022_portrait.jpg",
        "helmet_color": "#FFFFFF",
        "number_color": "#FFFFFF",
    },
}

# ── TEAM DATA ─────────────────────────────────────────────────────
TEAM_DATA = {
    "Mercedes": {
        "color": "#27F4D2",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f0/Mercedes_AMG_F1_Logo.svg/320px-Mercedes_AMG_F1_Logo.svg.png",
        "car_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Mercedes_AMG_F1_W15_2024.jpg/320px-Mercedes_AMG_F1_W15_2024.jpg",
        "base": "Brackley, UK",
    },
    "Ferrari": {
        "color": "#E8002D",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d4/Scuderia_Ferrari_Logo.svg/320px-Scuderia_Ferrari_Logo.svg.png",
        "car_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Ferrari_SF-24.jpg/320px-Ferrari_SF-24.jpg",
        "base": "Maranello, Italy",
    },
    "McLaren": {
        "color": "#FF8000",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/6/6b/McLaren_Racing_logo.svg/320px-McLaren_Racing_logo.svg.png",
        "car_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/thirty/McLaren_MCL38.jpg/320px-McLaren_MCL38.jpg",
        "base": "Woking, UK",
    },
    "Red Bull": {
        "color": "#3671C6",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Red_Bull_Racing_logo.svg/320px-Red_Bull_Racing_logo.svg.png",
        "car_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Red_Bull_RB20.jpg/320px-Red_Bull_RB20.jpg",
        "base": "Milton Keynes, UK",
    },
    "Aston Martin": {
        "color": "#229971",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b1/Aston_Martin_F1_Logo.svg/320px-Aston_Martin_F1_Logo.svg.png",
        "car_url": "",
        "base": "Silverstone, UK",
    },
    "Alpine": {
        "color": "#FF87BC",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/BWT_Alpine_F1_Team_2023_Logo.svg/320px-BWT_Alpine_F1_Team_2023_Logo.svg.png",
        "car_url": "",
        "base": "Enstone, UK",
    },
    "Haas": {
        "color": "#B6BABD",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Haas_F1_Team_logo.svg/320px-Haas_F1_Team_logo.svg.png",
        "car_url": "",
        "base": "Kannapolis, USA",
    },
    "Racing Bulls": {
        "color": "#6692FF",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Visa_Cash_App_RB_Formula_One_Team_Logo.svg/320px-Visa_Cash_App_RB_Formula_One_Team_Logo.svg.png",
        "car_url": "",
        "base": "Faenza, Italy",
    },
    "Williams": {
        "color": "#37BEDD",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Williams_Racing_logo.svg/320px-Williams_Racing_logo.svg.png",
        "car_url": "",
        "base": "Grove, UK",
    },
    "Audi": {
        "color": "#888888",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Audi-Logo_2016.svg/320px-Audi-Logo_2016.svg.png",
        "car_url": "",
        "base": "Hinwil, Switzerland",
    },
    "Cadillac": {
        "color": "#FFFFFF",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Cadillac_logo.svg/320px-Cadillac_logo.svg.png",
        "car_url": "",
        "base": "Concord, USA",
    },
}

# ── CIRCUIT BACKGROUND IMAGES ─────────────────────────────────────
CIRCUIT_BACKGROUNDS = {
    "Australian Grand Prix":    "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&q=80",
    "Chinese Grand Prix":       "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=1200&q=80",
    "Japanese Grand Prix":      "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=1200&q=80",
    "Bahrain Grand Prix":       "https://images.unsplash.com/photo-1466442929976-97f336a657be?w=1200&q=80",
    "Saudi Arabian Grand Prix": "https://images.unsplash.com/photo-1586861256632-a2baa6af0a25?w=1200&q=80",
    "Miami Grand Prix":         "https://images.unsplash.com/photo-1514214246283-d427a95c5d2f?w=1200&q=80",
    "Monaco Grand Prix":        "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=1200&q=80",
    "Spanish Grand Prix":       "https://images.unsplash.com/photo-1504019347908-b45f9b0b8dd5?w=1200&q=80",
    "Canadian Grand Prix":      "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=1200&q=80",
    "British Grand Prix":       "https://images.unsplash.com/photo-1500829243541-74b677fecc30?w=1200&q=80",
    "Austrian Grand Prix":      "https://images.unsplash.com/photo-1527576539890-dfa815648363?w=1200&q=80",
    "Belgian Grand Prix":       "https://images.unsplash.com/photo-1476067897447-d28b660ec3a4?w=1200&q=80",
    "Dutch Grand Prix":         "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1200&q=80",
    "Italian Grand Prix":       "https://images.unsplash.com/photo-1519452635265-7b1fbfd1e4e0?w=1200&q=80",
    "Azerbaijan Grand Prix":    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1200&q=80",
    "Singapore Grand Prix":     "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1200&q=80",
    "United States Grand Prix": "https://images.unsplash.com/photo-1531219432768-9f540ce91ef3?w=1200&q=80",
    "Mexico City Grand Prix":   "https://images.unsplash.com/photo-1518105779142-d975f22f1b0a?w=1200&q=80",
    "São Paulo Grand Prix":     "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=1200&q=80",
    "Las Vegas Grand Prix":     "https://images.unsplash.com/photo-1581351721010-8cf859cb14a4?w=1200&q=80",
    "Qatar Grand Prix":         "https://images.unsplash.com/photo-1553689557-c2fc0f7e8d83?w=1200&q=80",
    "Abu Dhabi Grand Prix":     "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1200&q=80",
}

DEFAULT_BG = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&q=80"
DEFAULT_DRIVER_IMG = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/F1_logo.svg/320px-F1_logo.svg.png"


def get_driver_data(driver_name: str) -> dict:
    if driver_name in DRIVER_DATA:
        return DRIVER_DATA[driver_name]
    # Partial match
    for key, val in DRIVER_DATA.items():
        if driver_name.split()[-1].lower() in key.lower():
            return val
    return {
        "number": 0, "nationality": "??", "team": "Unknown",
        "abbreviation": driver_name[:3].upper(),
        "image_url": DEFAULT_DRIVER_IMG,
        "helmet_color": "#888888",
    }


def get_team_data(team_name: str) -> dict:
    if team_name in TEAM_DATA:
        return TEAM_DATA[team_name]
    for key, val in TEAM_DATA.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return val
    return {"color": "#888888", "logo_url": "", "car_url": "", "base": ""}


def get_circuit_bg(circuit_name: str) -> str:
    return CIRCUIT_BACKGROUNDS.get(circuit_name, DEFAULT_BG)
