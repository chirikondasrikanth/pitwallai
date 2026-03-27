"""
src/circuit_data.py
Rich circuit data for all 24 2026 F1 circuits.
Includes:
  - Unsplash image URLs (free, no API key needed)
  - Circuit SVG track maps
  - Full race facts
  - Historical records
  - DRS zones
  - Tire recommendations
"""

import unicodedata

_GENERIC_CIRCUIT_TOKENS = {
    "autodrome", "autodromo", "circuit", "formula", "gp", "grand",
    "international", "prix", "race", "ring", "street", "track",
}

_CIRCUIT_ALIASES = {
    "abu dhabi": "Abu Dhabi Grand Prix",
    "abu dhabi grand prix": "Abu Dhabi Grand Prix",
    "australia": "Australian Grand Prix",
    "australian grand prix": "Australian Grand Prix",
    "austria": "Austrian Grand Prix",
    "austrian grand prix": "Austrian Grand Prix",
    "azerbaijan": "Azerbaijan Grand Prix",
    "azerbaijan grand prix": "Azerbaijan Grand Prix",
    "bahrain": "Bahrain Grand Prix",
    "bahrain grand prix": "Bahrain Grand Prix",
    "belgian grand prix": "Belgian Grand Prix",
    "belgium": "Belgian Grand Prix",
    "britain": "British Grand Prix",
    "british grand prix": "British Grand Prix",
    "canada": "Canadian Grand Prix",
    "canadian grand prix": "Canadian Grand Prix",
    "china": "Chinese Grand Prix",
    "chinese grand prix": "Chinese Grand Prix",
    "cota": "United States Grand Prix",
    "dutch grand prix": "Dutch Grand Prix",
    "emilia romagna": "Emilia Romagna Grand Prix",
    "emilia romagna grand prix": "Emilia Romagna Grand Prix",
    "hungarian grand prix": "Hungarian Grand Prix",
    "hungary": "Hungarian Grand Prix",
    "imola": "Emilia Romagna Grand Prix",
    "interlagos": "S\u00e3o Paulo Grand Prix",
    "italian grand prix": "Italian Grand Prix",
    "italy": "Italian Grand Prix",
    "japan": "Japanese Grand Prix",
    "japanese grand prix": "Japanese Grand Prix",
    "jeddah": "Saudi Arabian Grand Prix",
    "las vegas": "Las Vegas Grand Prix",
    "las vegas grand prix": "Las Vegas Grand Prix",
    "melbourne": "Australian Grand Prix",
    "mexico city": "Mexico City Grand Prix",
    "mexico city grand prix": "Mexico City Grand Prix",
    "miami": "Miami Grand Prix",
    "miami grand prix": "Miami Grand Prix",
    "monaco": "Monaco Grand Prix",
    "monaco grand prix": "Monaco Grand Prix",
    "montreal": "Canadian Grand Prix",
    "monza": "Italian Grand Prix",
    "qatar": "Qatar Grand Prix",
    "qatar grand prix": "Qatar Grand Prix",
    "sakhir": "Bahrain Grand Prix",
    "sao paulo": "S\u00e3o Paulo Grand Prix",
    "sao paulo grand prix": "S\u00e3o Paulo Grand Prix",
    "saudi arabia": "Saudi Arabian Grand Prix",
    "saudi arabian grand prix": "Saudi Arabian Grand Prix",
    "shanghai": "Chinese Grand Prix",
    "singapore": "Singapore Grand Prix",
    "singapore grand prix": "Singapore Grand Prix",
    "silverstone": "British Grand Prix",
    "spa": "Belgian Grand Prix",
    "spa francorchamps": "Belgian Grand Prix",
    "spain": "Spanish Grand Prix",
    "spanish grand prix": "Spanish Grand Prix",
    "suzuka": "Japanese Grand Prix",
    "united states": "United States Grand Prix",
    "united states grand prix": "United States Grand Prix",
    "us grand prix": "United States Grand Prix",
    "yas marina": "Abu Dhabi Grand Prix",
    "zandvoort": "Dutch Grand Prix",
}


def _normalize_circuit_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name or "")
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_name.lower().replace("-", " ").split())


def _meaningful_tokens(name: str) -> set[str]:
    return {
        token
        for token in _normalize_circuit_name(name).split()
        if len(token) > 2 and token not in _GENERIC_CIRCUIT_TOKENS
    }

# ── CIRCUIT DATABASE ──────────────────────────────────────────────
# Images from Wikimedia Commons (public domain) and Unsplash (free)

CIRCUIT_DATA = {
    "Australian Grand Prix": {
        "location":      "Melbourne, Australia",
        "circuit_name":  "Albert Park Circuit",
        "country":       "🇦🇺",
        "laps":          58,
        "distance_km":   307.6,
        "lap_length":    5.303,
        "type":          "Street/Permanent",
        "overtaking":    "Medium",
        "drs_zones":     4,
        "first_gp":      1996,
        "lap_record":    "1:20.235 (Leclerc, 2022)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Albert_Park_circuit_2020.png/640px-Albert_Park_circuit_2020.png",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Albert_Park_circuit_2020.png/320px-Albert_Park_circuit_2020.png",
        "description":   "The Albert Park circuit winds through a public park in Melbourne. Known for its fast flowing nature and beautiful lakeside setting.",
        "tire_info":     "Medium/Hard compounds preferred. Low degradation circuit.",
        "weather_avg":   "25°C, low rain chance",
        "most_wins":     "Michael Schumacher (4)",
        "color":         "#3671C6",
        "facts": [
            "Season opener since 1996",
            "4 DRS zones added in 2022 revamp",
            "Albert Park lake runs alongside the circuit",
            "Safety car appearances very common here",
        ]
    },

    "Chinese Grand Prix": {
        "location":      "Shanghai, China",
        "circuit_name":  "Shanghai International Circuit",
        "country":       "🇨🇳",
        "laps":          56,
        "distance_km":   305.1,
        "lap_length":    5.451,
        "type":          "Permanent",
        "overtaking":    "High",
        "drs_zones":     2,
        "first_gp":      2004,
        "lap_record":    "1:32.238 (Verstappen, 2024)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Shanghai_International_Circuit_2009.jpg/640px-Shanghai_International_Circuit_2009.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Shanghai_circuit.svg/320px-Shanghai_circuit.svg.png",
        "description":   "The Shanghai circuit is famous for its unique snail-shaped Turn 1-2 complex and long back straight. One of the best overtaking venues on the calendar.",
        "tire_info":     "High deg circuit — tire strategy is critical.",
        "weather_avg":   "18°C, moderate rain chance",
        "most_wins":     "Michael Schumacher (6)",
        "color":         "#E8002D",
        "facts": [
            "Iconic Turn 1-2 snail complex",
            "Long 1.2km back straight enables overtaking",
            "Sprint race format in 2026",
            "Kimi Antonelli won maiden race here in 2026",
        ]
    },

    "Japanese Grand Prix": {
        "location":      "Suzuka, Japan",
        "circuit_name":  "Suzuka Circuit",
        "country":       "🇯🇵",
        "laps":          53,
        "distance_km":   307.5,
        "lap_length":    5.807,
        "type":          "Permanent",
        "overtaking":    "Low",
        "drs_zones":     1,
        "first_gp":      1987,
        "lap_record":    "1:30.983 (Verstappen, 2023)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Suzuka_circuit_2005.jpg/640px-Suzuka_circuit_2005.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Suzuka_circuit_map.svg/320px-Suzuka_circuit_map.svg.png",
        "description":   "Suzuka is the most technically demanding circuit on the F1 calendar. The figure-of-eight layout is unique and the high speed S-curves are legendary.",
        "tire_info":     "Medium/Soft compounds. High energy circuit stresses tires.",
        "weather_avg":   "17°C, moderate rain chance",
        "most_wins":     "Ayrton Senna (6)",
        "color":         "#FF8000",
        "facts": [
            "Only figure-of-eight circuit in F1",
            "130R corner taken at 300km/h",
            "Japanese fans are the most passionate in F1",
            "Championship decider venue multiple times",
        ]
    },

    "Bahrain Grand Prix": {
        "location":      "Sakhir, Bahrain",
        "circuit_name":  "Bahrain International Circuit",
        "country":       "🇧🇭",
        "laps":          57,
        "distance_km":   308.2,
        "lap_length":    5.412,
        "type":          "Permanent",
        "overtaking":    "High",
        "drs_zones":     3,
        "first_gp":      2004,
        "lap_record":    "1:31.447 (De la Rosa, 2005)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Bahrain_GP_2010.jpg/640px-Bahrain_GP_2010.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Bahrain_International_Circuit--Grand_Prix_Layout.svg/320px-Bahrain_International_Circuit--Grand_Prix_Layout.svg.png",
        "description":   "The Bahrain circuit races under floodlights in the desert. Known for its excellent racing and multiple overtaking opportunities.",
        "tire_info":     "High deg — sand on track affects tire life.",
        "weather_avg":   "28°C, very low rain chance",
        "most_wins":     "Lewis Hamilton (5)",
        "color":         "#229971",
        "facts": [
            "First floodlit F1 race in 2014",
            "Desert sand causes high tire degradation",
            "3 DRS zones create overtaking opportunities",
            "Pre-season testing held here every year",
        ]
    },

    "Saudi Arabian Grand Prix": {
        "location":      "Jeddah, Saudi Arabia",
        "circuit_name":  "Jeddah Corniche Circuit",
        "country":       "🇸🇦",
        "laps":          50,
        "distance_km":   308.5,
        "lap_length":    6.174,
        "type":          "Street",
        "overtaking":    "Medium",
        "drs_zones":     3,
        "first_gp":      2021,
        "lap_record":    "1:30.734 (Leclerc, 2022)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Jeddah_Corniche_Circuit_2021.jpg/640px-Jeddah_Corniche_Circuit_2021.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Jeddah_Corniche_Circuit_2021.jpg/320px-Jeddah_Corniche_Circuit_2021.jpg",
        "description":   "The Jeddah Corniche Circuit is the fastest street circuit in F1 history. Average speeds exceed 250km/h along the Red Sea corniche.",
        "tire_info":     "Low degradation — 1-stop strategy typical.",
        "weather_avg":   "30°C, very low rain chance",
        "most_wins":     "Max Verstappen (2)",
        "color":         "#27F4D2",
        "facts": [
            "Fastest street circuit in F1 history",
            "Average speed over 250km/h",
            "50+ corners in one lap",
            "Opened in 2021 — one of newest circuits",
        ]
    },

    "Miami Grand Prix": {
        "location":      "Miami, Florida, USA",
        "circuit_name":  "Miami International Autodrome",
        "country":       "🇺🇸",
        "laps":          57,
        "distance_km":   308.3,
        "lap_length":    5.412,
        "type":          "Street",
        "overtaking":    "Medium",
        "drs_zones":     3,
        "first_gp":      2022,
        "lap_record":    "1:29.708 (Verstappen, 2023)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Miami_Grand_Prix_2022.jpg/640px-Miami_Grand_Prix_2022.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Miami_Grand_Prix_2022.jpg/320px-Miami_Grand_Prix_2022.jpg",
        "description":   "The Miami circuit surrounds the Hard Rock Stadium. A glitzy American event with a fake marina and party atmosphere.",
        "tire_info":     "High deg — bumpy surface wears tires quickly.",
        "weather_avg":   "30°C, moderate humidity",
        "most_wins":     "Max Verstappen (2)",
        "color":         "#FF87BC",
        "facts": [
            "Surrounds Hard Rock Stadium",
            "Fake marina created for atmosphere",
            "Sprint race format in 2026",
            "One of the most glamorous events on calendar",
        ]
    },

    "Monaco Grand Prix": {
        "location":      "Monte Carlo, Monaco",
        "circuit_name":  "Circuit de Monaco",
        "country":       "🇲🇨",
        "laps":          78,
        "distance_km":   260.3,
        "lap_length":    3.337,
        "type":          "Street",
        "overtaking":    "Very Low",
        "drs_zones":     1,
        "first_gp":      1950,
        "lap_record":    "1:12.909 (Leclerc, 2021)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Monaco_Formula_1_Grand_Prix_2010.jpg/640px-Monaco_Formula_1_Grand_Prix_2010.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Monte_Carlo_Formula_1_track_map.svg/320px-Monte_Carlo_Formula_1_track_map.svg.png",
        "description":   "The jewel of the F1 calendar. Monaco is the most prestigious race in motorsport — narrow streets, zero room for error, and the most glamorous setting in sport.",
        "tire_info":     "Qualifying position everything — overtaking nearly impossible.",
        "weather_avg":   "22°C, low rain chance",
        "most_wins":     "Ayrton Senna (6)",
        "color":         "#FFD700",
        "facts": [
            "Part of the Triple Crown of motorsport",
            "Held since 1929 — oldest active GP",
            "Narrowest circuit on the calendar",
            "Winning from pole is almost mandatory",
        ]
    },

    "Spanish Grand Prix": {
        "location":      "Barcelona, Spain",
        "circuit_name":  "Circuit de Barcelona-Catalunya",
        "country":       "🇪🇸",
        "laps":          66,
        "distance_km":   308.4,
        "lap_length":    4.675,
        "type":          "Permanent",
        "overtaking":    "Low",
        "drs_zones":     2,
        "first_gp":      1991,
        "lap_record":    "1:16.330 (Verstappen, 2023)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Circuit_de_Barcelona_Catalunya.jpg/640px-Circuit_de_Barcelona_Catalunya.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Barcelona_circuit_map.svg/320px-Barcelona_circuit_map.svg.png",
        "description":   "Barcelona is the definitive test of an F1 car. Teams know this circuit better than any other from pre-season testing.",
        "tire_info":     "High deg — teams know this circuit best from testing.",
        "weather_avg":   "26°C, low rain chance",
        "most_wins":     "Michael Schumacher (6)",
        "color":         "#E8002D",
        "facts": [
            "Pre-season testing held here every year",
            "Teams know every corner intimately",
            "Sector 3 chicane removed in 2023",
            "Very hard to overtake — strategy key",
        ]
    },

    "Canadian Grand Prix": {
        "location":      "Montreal, Canada",
        "circuit_name":  "Circuit Gilles Villeneuve",
        "country":       "🇨🇦",
        "laps":          70,
        "distance_km":   305.3,
        "lap_length":    4.361,
        "type":          "Street/Permanent",
        "overtaking":    "High",
        "drs_zones":     2,
        "first_gp":      1978,
        "lap_record":    "1:13.078 (Verstappen, 2022)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Circuit_Gilles_Villeneuve.jpg/640px-Circuit_Gilles_Villeneuve.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Gilles_Villeneuve_track_map.svg/320px-Gilles_Villeneuve_track_map.svg.png",
        "description":   "Named after the legendary Gilles Villeneuve. The island circuit along the St Lawrence River produces classic races with its Wall of Champions.",
        "tire_info":     "Heavy braking zones — brake wear critical.",
        "weather_avg":   "22°C, moderate rain chance",
        "most_wins":     "Michael Schumacher (7)",
        "color":         "#FF8000",
        "facts": [
            "Named after Gilles Villeneuve",
            "Wall of Champions claims many victims",
            "Safety car appears almost every year",
            "Island circuit on the St Lawrence River",
        ]
    },

    "British Grand Prix": {
        "location":      "Silverstone, UK",
        "circuit_name":  "Silverstone Circuit",
        "country":       "🇬🇧",
        "laps":          52,
        "distance_km":   306.2,
        "lap_length":    5.891,
        "type":          "Permanent",
        "overtaking":    "Medium",
        "drs_zones":     2,
        "first_gp":      1950,
        "lap_record":    "1:27.097 (Hamilton, 2020)",
        "image_url":     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Silverstone_Circuit_2020.jpg/640px-Silverstone_Circuit_2020.jpg",
        "map_url":       "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Silverstone_circuit_2020.svg/320px-Silverstone_circuit_2020.svg.png",
        "description":   "Home of the first ever Formula 1 World Championship race in 1950. Silverstone is the spiritual home of motorsport with legendary corners like Copse and Maggotts.",
        "tire_info":     "High speed corners create high tire stress.",
        "weather_avg":   "18°C, high rain chance",
        "most_wins":     "Lewis Hamilton (8)",
        "color":         "#3671C6",
        "facts": [
            "Hosted first ever F1 World Championship race",
            "Maggotts-Becketts complex taken flat out",
            "British fans create incredible atmosphere",
            "Hamilton's record 8 wins here",
        ]
    },
}

# Add remaining circuits with basic data
REMAINING_CIRCUITS = {
    "Austrian Grand Prix": {
        "location": "Spielberg, Austria", "country": "🇦🇹",
        "circuit_name": "Red Bull Ring", "laps": 71, "distance_km": 306.5,
        "lap_length": 4.318, "type": "Permanent", "overtaking": "High",
        "drs_zones": 3, "first_gp": 1970, "color": "#E8002D",
        "lap_record": "1:05.619 (Bottas, 2020)",
        "description": "The Red Bull Ring nestled in the Austrian Alps. Short lap but high altitude and beautiful mountain scenery.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/RedBullRing.jpg/640px-RedBullRing.jpg",
        "facts": ["Shortest lap on calendar", "Stunning Alpine backdrop", "3 DRS zones = lots of overtaking"],
        "tire_info": "Low deg — 1-stop usually optimal.", "weather_avg": "22°C",
        "most_wins": "Michael Schumacher (3)", "map_url": "", "lap_length": 4.318,
    },
    "Belgian Grand Prix": {
        "location": "Spa-Francorchamps, Belgium", "country": "🇧🇪",
        "circuit_name": "Circuit de Spa-Francorchamps", "laps": 44, "distance_km": 308.1,
        "lap_length": 7.004, "type": "Permanent", "overtaking": "High",
        "drs_zones": 2, "first_gp": 1950, "color": "#FFD700",
        "lap_record": "1:46.286 (Bottas, 2018)",
        "description": "Spa is the greatest circuit in the world. Eau Rouge, Raidillon, Pouhon — legendary corners in a stunning Ardennes forest setting.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Spa-Francorchamps_2004.jpg/640px-Spa-Francorchamps_2004.jpg",
        "facts": ["Longest circuit on calendar at 7km", "Eau Rouge taken flat out", "Weather changes lap by lap"],
        "tire_info": "Variable weather makes strategy unpredictable.", "weather_avg": "18°C, high rain",
        "most_wins": "Michael Schumacher (6)", "map_url": "",
    },
    "Emilia Romagna Grand Prix": {
        "location": "Imola, Italy", "country": "🇮🇹",
        "circuit_name": "Autodromo Enzo e Dino Ferrari", "laps": 63, "distance_km": 309.3,
        "lap_length": 4.909, "type": "Permanent", "overtaking": "Low",
        "drs_zones": 2, "first_gp": 1980, "color": "#E8002D",
        "lap_record": "1:15.484 (Hamilton, 2020)",
        "description": "Imola is one of the most historic circuits in F1. Narrow, fast, and punishing with little margin for error.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Enzo_e_Dino_Ferrari_track_map.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Enzo_e_Dino_Ferrari_track_map.svg",
        "facts": ["Site of Ayrton Senna's fatal crash in 1994", "Very narrow — overtaking difficult", "Old-school circuit beloved by fans"],
        "tire_info": "Medium/Hard — abrasive surface.", "weather_avg": "18°C, moderate rain",
        "most_wins": "Michael Schumacher (7)", "color": "#E8002D",
    },
    "Hungarian Grand Prix": {
        "location": "Budapest, Hungary", "country": "🇭🇺",
        "circuit_name": "Hungaroring", "laps": 70, "distance_km": 306.6,
        "lap_length": 4.381, "type": "Permanent", "overtaking": "Very Low",
        "drs_zones": 1, "first_gp": 1986, "color": "#FF8000",
        "lap_record": "1:16.627 (Hamilton, 2020)",
        "description": "The Hungaroring is often called 'Monaco without the barriers'. Extremely tight and twisty, making overtaking almost impossible.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Hungaroring.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Hungaroring.svg",
        "facts": ["First GP behind Iron Curtain in 1986", "Very twisty — hard to overtake", "Qualifying position crucial"],
        "tire_info": "High deg — multiple tire strategies possible.", "weather_avg": "30°C, low rain",
        "most_wins": "Lewis Hamilton (8)", "color": "#FF8000",
    },
    "Dutch Grand Prix": {
        "location": "Zandvoort, Netherlands", "country": "🇳🇱",
        "circuit_name": "Circuit Zandvoort", "laps": 72, "distance_km": 306.6,
        "lap_length": 4.259, "type": "Permanent", "overtaking": "Low",
        "drs_zones": 2, "first_gp": 1952, "color": "#FF8000",
        "lap_record": "1:11.097 (Verstappen, 2023)",
        "description": "Zandvoort returned to F1 in 2021 with banked corners. The Dutch fans create an incredible orange atmosphere for Verstappen.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Circuit_Zandvoort_track_map.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Circuit_Zandvoort_track_map.svg",
        "facts": ["Banked corners unique in modern F1", "Verstappen's home race — orange army", "Short lap makes strategy complex"],
        "tire_info": "High deg — banking creates lateral tire load.", "weather_avg": "18°C, moderate rain",
        "most_wins": "Max Verstappen (3)", "color": "#FF8000",
    },
    "Italian Grand Prix": {
        "location": "Monza, Italy", "country": "🇮🇹",
        "circuit_name": "Autodromo Nazionale Monza", "laps": 53, "distance_km": 306.7,
        "lap_length": 5.793, "type": "Permanent", "overtaking": "High",
        "drs_zones": 2, "first_gp": 1922, "color": "#E8002D",
        "lap_record": "1:21.046 (Barrichello, 2004)",
        "description": "The Temple of Speed. Monza is the fastest circuit in F1 with minimal downforce setups and average speeds over 260km/h.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Nazionale_Monza.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Nazionale_Monza.svg",
        "facts": ["Oldest active circuit in F1", "Fastest average race speed", "Tifosi make Monza atmosphere electric"],
        "tire_info": "Low downforce — low deg, 1-stop typical.", "weather_avg": "22°C, low rain",
        "most_wins": "Lewis Hamilton (5)", "color": "#E8002D",
    },
    "Azerbaijan Grand Prix": {
        "location": "Baku, Azerbaijan", "country": "🇦🇿",
        "circuit_name": "Baku City Circuit", "laps": 51, "distance_km": 306.0,
        "lap_length": 6.003, "type": "Street", "overtaking": "High",
        "drs_zones": 2, "first_gp": 2016, "color": "#27F4D2",
        "lap_record": "1:43.009 (Leclerc, 2019)",
        "description": "The Baku City Circuit is a street race through ancient Azerbaijani architecture. Chaos is almost guaranteed with the long straight and narrow old town section.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Baku_City_Circuit_track_map.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Baku_City_Circuit_track_map.svg",
        "facts": ["Longest straight in F1 at 2.2km", "Narrow old town section is treacherous", "Safety car almost guaranteed"],
        "tire_info": "Low deg but unpredictable — safety car disrupts strategy.", "weather_avg": "22°C, low rain",
        "most_wins": "Sergio Perez (3)", "color": "#27F4D2",
    },
    "Singapore Grand Prix": {
        "location": "Singapore", "country": "🇸🇬",
        "circuit_name": "Marina Bay Street Circuit", "laps": 62, "distance_km": 306.1,
        "lap_length": 4.940, "type": "Street", "overtaking": "Low",
        "drs_zones": 3, "first_gp": 2008, "color": "#E8002D",
        "lap_record": "1:35.867 (Leclerc, 2023)",
        "description": "F1's only night race under 1500 floodlights. Singapore is a physically demanding street race through the city with humidity and heat.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Marina_Bay_Street_Circuit_2023.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Marina_Bay_Street_Circuit_2023.svg",
        "facts": ["F1's only night race", "Most physically demanding race on calendar", "Longest race by time — often hits 2hr limit"],
        "tire_info": "High deg — heat and humidity destroy tires.", "weather_avg": "32°C, high humidity",
        "most_wins": "Sebastian Vettel (5)", "color": "#E8002D",
    },
    "United States Grand Prix": {
        "location": "Austin, Texas, USA", "country": "🇺🇸",
        "circuit_name": "Circuit of the Americas", "laps": 56, "distance_km": 308.4,
        "lap_length": 5.513, "type": "Permanent", "overtaking": "High",
        "drs_zones": 2, "first_gp": 2012, "color": "#3671C6",
        "lap_record": "1:36.169 (Leclerc, 2019)",
        "description": "COTA is inspired by the world's greatest circuits. Turn 1 blind crest, Maggotts-inspired esses, and a stadium section make it a fan favourite.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Austin_circuit_2012.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Austin_circuit_2012.svg",
        "facts": ["Inspired by legendary circuits worldwide", "Turn 1 blind crest is spectacular", "Sprint race format in 2026"],
        "tire_info": "High deg — bumpy surface destroys tires.", "weather_avg": "25°C, moderate rain",
        "most_wins": "Lewis Hamilton (6)", "color": "#3671C6",
    },
    "Mexico City Grand Prix": {
        "location": "Mexico City, Mexico", "country": "🇲🇽",
        "circuit_name": "Autodromo Hermanos Rodriguez", "laps": 71, "distance_km": 305.4,
        "lap_length": 4.304, "type": "Permanent", "overtaking": "Medium",
        "drs_zones": 3, "first_gp": 1963, "color": "#27F4D2",
        "lap_record": "1:17.774 (Bottas, 2021)",
        "description": "At 2285m altitude Mexico City creates unique engine challenges. The thin air means huge top speeds but reduced downforce effectiveness.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Hermanos_Rodriguez_track_map.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Hermanos_Rodriguez_track_map.svg",
        "facts": ["Highest altitude race at 2285m", "Thin air equals massive top speeds", "Stadium section holds 100,000 fans"],
        "tire_info": "Low deg due to altitude — 1-stop typical.", "weather_avg": "20°C, afternoon rain risk",
        "most_wins": "Max Verstappen (4)", "color": "#27F4D2",
    },
    "São Paulo Grand Prix": {
        "location": "São Paulo, Brazil", "country": "🇧🇷",
        "circuit_name": "Autodromo Jose Carlos Pace (Interlagos)", "laps": 71, "distance_km": 305.9,
        "lap_length": 4.309, "type": "Permanent", "overtaking": "High",
        "drs_zones": 2, "first_gp": 1973, "color": "#229971",
        "lap_record": "1:10.540 (Rubens Barrichello, 2004)",
        "description": "Interlagos is one of the most beloved circuits in F1. Anti-clockwise layout, unpredictable weather, and passionate Brazilian fans create unforgettable races.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Jose_Carlos_Pace_track_map.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Autodromo_Jose_Carlos_Pace_track_map.svg",
        "facts": ["Anti-clockwise circuit", "Weather can change every lap", "Sprint race format in 2026", "Home of Senna and Piquet"],
        "tire_info": "Variable — rain often forces strategy changes.", "weather_avg": "25°C, high rain chance",
        "most_wins": "Michael Schumacher (4)", "color": "#229971",
    },
    "Las Vegas Grand Prix": {
        "location": "Las Vegas, Nevada, USA", "country": "🇺🇸",
        "circuit_name": "Las Vegas Street Circuit", "laps": 50, "distance_km": 309.9,
        "lap_length": 6.120, "type": "Street", "overtaking": "High",
        "drs_zones": 2, "first_gp": 2023, "color": "#C0C0C0",
        "lap_record": "1:35.490 (Leclerc, 2023)",
        "description": "Racing through the Las Vegas Strip at night past casinos and neon lights. One of F1's most spectacular backdrops.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Las_Vegas_Street_Circuit.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Las_Vegas_Street_Circuit.svg",
        "facts": ["Races past famous casinos on the Strip", "Night race under neon lights", "Newest street circuit (2023)"],
        "tire_info": "Cold track temps at night cause low grip.", "weather_avg": "10°C, very dry",
        "most_wins": "Carlos Sainz (1)", "color": "#C0C0C0",
    },
    "Qatar Grand Prix": {
        "location": "Lusail, Qatar", "country": "🇶🇦",
        "circuit_name": "Losail International Circuit", "laps": 57, "distance_km": 307.1,
        "lap_length": 5.380, "type": "Permanent", "overtaking": "Medium",
        "drs_zones": 2, "first_gp": 2004, "color": "#FFD700",
        "lap_record": "1:24.319 (Russell, 2023)",
        "description": "Losail is a flowing, high-speed circuit originally built for MotoGP. The sprint race format adds extra drama to the desert event.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Losail_International_Circuit_track_map.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Losail_International_Circuit_track_map.svg",
        "facts": ["Originally a MotoGP circuit", "Sprint race format in 2026", "Extreme heat and humidity challenge drivers"],
        "tire_info": "High deg — heat destroys tires rapidly.", "weather_avg": "35°C, very dry",
        "most_wins": "Max Verstappen (2)", "color": "#FFD700",
    },
    "Abu Dhabi Grand Prix": {
        "location": "Abu Dhabi, UAE", "country": "🇦🇪",
        "circuit_name": "Yas Marina Circuit", "laps": 58, "distance_km": 306.2,
        "lap_length": 5.281, "type": "Permanent", "overtaking": "Medium",
        "drs_zones": 2, "first_gp": 2009, "color": "#27F4D2",
        "lap_record": "1:26.103 (Leclerc, 2021)",
        "description": "The season finale. Yas Marina's revamped 2021 layout transformed it into a more exciting circuit. The day-to-night race under the lights is visually stunning.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Yas_Marina_Circuit_2021.svg",
        "map_url":   "https://commons.wikimedia.org/wiki/Special:FilePath/Yas_Marina_Circuit_2021.svg",
        "facts": ["Season finale every year since 2009", "Day-to-night race format", "2021 redesign massively improved racing"],
        "tire_info": "Low deg — 1-stop typical.", "weather_avg": "28°C, very dry",
        "most_wins": "Lewis Hamilton (5)", "color": "#27F4D2",
    },
}

# Merge all circuits
CIRCUIT_DATA.update(REMAINING_CIRCUITS)

# Add generic data for any circuit not in database
DEFAULT_CIRCUIT = {
    "location": "TBC", "country": "🏁",
    "circuit_name": "TBC", "laps": 55, "distance_km": 305.0,
    "lap_length": 5.5, "type": "Permanent", "overtaking": "Medium",
    "drs_zones": 2, "first_gp": 2000, "color": "#888899",
    "lap_record": "TBC", "description": "Circuit information coming soon.",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/F1_logo.svg/320px-F1_logo.svg.png",
    "map_url": "", "facts": [], "tire_info": "TBC", "weather_avg": "TBC",
    "most_wins": "TBC",
}


def _fallback_circuit_image(circuit_name: str) -> str:
    try:
        from .f1_assets import get_circuit_bg
        return get_circuit_bg(circuit_name)
    except Exception:
        return DEFAULT_CIRCUIT["image_url"]


def get_circuit_data(circuit_name: str) -> dict:
    """Get full circuit data — falls back to default if not found."""
    # Try exact match
    if circuit_name in CIRCUIT_DATA:
        return CIRCUIT_DATA[circuit_name]

    normalized_name = _normalize_circuit_name(circuit_name)

    # Try normalized exact match so accent/case differences still work.
    for key, data in CIRCUIT_DATA.items():
        if _normalize_circuit_name(key) == normalized_name:
            return data

    canonical_name = _CIRCUIT_ALIASES.get(normalized_name, circuit_name)
    if canonical_name in CIRCUIT_DATA:
        return CIRCUIT_DATA[canonical_name]

    # Conservative token matching helps inputs like "Monaco" without
    # accidentally matching every missing circuit to "Grand Prix".
    query_tokens = _meaningful_tokens(canonical_name)
    if query_tokens:
        for key, data in CIRCUIT_DATA.items():
            if query_tokens == _meaningful_tokens(key):
                return data

    return {
        **DEFAULT_CIRCUIT,
        "circuit_name": canonical_name,
        "image_url": _fallback_circuit_image(canonical_name),
    }


# ── LOCAL ASSET FILENAMES ─────────────────────────────────────────
# Maps circuit name → filename inside dashboard/assets/circuits/
CIRCUIT_LOCAL_IMAGES = {
    "Australian Grand Prix":    "australian.jpg",
    "Chinese Grand Prix":       "chinese.jpg",
    "Japanese Grand Prix":      "japanese.jpg",
    "Bahrain Grand Prix":       "bahrain.jpg",
    "Saudi Arabian Grand Prix": "saudi_2.jpg",
    "Miami Grand Prix":         "miami.jpg",
    "Emilia Romagna Grand Prix":"emilia.jpg",
    "Monaco Grand Prix":        "monaco.jpg",
    "Spanish Grand Prix":       "spanish.jpg",
    "Canadian Grand Prix":      "canadian.jpg",
    "Austrian Grand Prix":      "austrian.jpg",
    "British Grand Prix":       "british.jpg",
    "Belgian Grand Prix":       "belgian_2.jpg",
    "Hungarian Grand Prix":     "hungarian.jpg",
    "Dutch Grand Prix":         "dutch.jpg",
    "Italian Grand Prix":       "italian.jpg",
    "Azerbaijan Grand Prix":    "azerbaijan.jpg",
    "Singapore Grand Prix":     "singapore.jpg",
    "United States Grand Prix": "usa.jpg",
    "Mexico City Grand Prix":   "mexico.jpg",
    "São Paulo Grand Prix":     "brazil.jpg",
    "Las Vegas Grand Prix":     "lasvegas.jpg",
    "Abu Dhabi Grand Prix":     "abudhabi.jpg",
    # Qatar has no local image — falls back to image_url
}


def get_circuit_local_img(circuit_name: str) -> str:
    """Return local asset filename for circuit, or empty string if none."""
    if circuit_name in CIRCUIT_LOCAL_IMAGES:
        return CIRCUIT_LOCAL_IMAGES[circuit_name]
    # Try normalised match
    norm = _normalize_circuit_name(circuit_name)
    for key, fname in CIRCUIT_LOCAL_IMAGES.items():
        if _normalize_circuit_name(key) == norm:
            return fname
    return ""


def get_circuit_image_url(circuit_name: str) -> str:
    """Get circuit image URL."""
    data = get_circuit_data(circuit_name)
    return data.get("image_url", DEFAULT_CIRCUIT["image_url"])


def get_all_circuits() -> list:
    """Get list of all circuits with basic info."""
    return [
        {
            "name": name,
            "location": data.get("location", ""),
            "country": data.get("country", "🏁"),
            "laps": data.get("laps", 0),
            "type": data.get("type", ""),
        }
        for name, data in CIRCUIT_DATA.items()
    ]
