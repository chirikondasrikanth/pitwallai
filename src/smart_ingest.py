"""
smart_ingest.py — Universal F1 Race Data Parser
Accepts: CSV, Excel, JSON, PDF, Image (OCR), plain text, paste
Auto-detects format → extracts → normalizes → maps to F1 schema.
"""

import os, io, re, json, logging
import pandas as pd
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# ── Driver→Team lookup (2026 grid + historical) ──────────────────
DRIVER_TEAM_MAP = {
    "george russell":"Mercedes",    "russell":"Mercedes",
    "kimi antonelli":"Mercedes",    "antonelli":"Mercedes",
    "charles leclerc":"Ferrari",    "leclerc":"Ferrari",
    "lewis hamilton":"Ferrari",     "hamilton":"Ferrari",
    "lando norris":"McLaren",       "norris":"McLaren",
    "oscar piastri":"McLaren",      "piastri":"McLaren",
    "max verstappen":"Red Bull",    "verstappen":"Red Bull",
    "isack hadjar":"Red Bull",      "hadjar":"Red Bull",
    "oliver bearman":"Haas",        "bearman":"Haas",
    "esteban ocon":"Haas",          "ocon":"Haas",
    "pierre gasly":"Alpine",        "gasly":"Alpine",
    "franco colapinto":"Alpine",    "colapinto":"Alpine",
    "nico hulkenberg":"Audi",       "hulkenberg":"Audi",    "hulk":"Audi",
    "gabriel bortoleto":"Audi",     "bortoleto":"Audi",
    "arvid lindblad":"Racing Bulls","lindblad":"Racing Bulls",
    "liam lawson":"Racing Bulls",   "lawson":"Racing Bulls",
    "fernando alonso":"Aston Martin","alonso":"Aston Martin",
    "lance stroll":"Aston Martin",  "stroll":"Aston Martin",
    "alexander albon":"Williams",   "albon":"Williams",
    "carlos sainz":"Williams",      "sainz":"Williams",
    "sergio perez":"Cadillac",      "perez":"Cadillac",     "checo":"Cadillac",
    "valtteri bottas":"Cadillac",   "bottas":"Cadillac",
    # 2024/2025
    "jack doohan":"Alpine",         "doohan":"Alpine",
    "yuki tsunoda":"Racing Bulls",  "tsunoda":"Racing Bulls",
    "zhou guanyu":"Kick Sauber",    "zhou":"Kick Sauber",
    "kevin magnussen":"Haas",       "magnussen":"Haas",
    "logan sargeant":"Williams",    "sargeant":"Williams",
    "daniel ricciardo":"Racing Bulls","ricciardo":"Racing Bulls",
    "sergio perez":"Red Bull",
}

DRIVER_ABBREVS = {
    "rus":"George Russell","ant":"Kimi Antonelli","lec":"Charles Leclerc",
    "ham":"Lewis Hamilton","nor":"Lando Norris",  "pia":"Oscar Piastri",
    "ver":"Max Verstappen","had":"Isack Hadjar",  "bea":"Oliver Bearman",
    "oco":"Esteban Ocon",  "gas":"Pierre Gasly",  "col":"Franco Colapinto",
    "hul":"Nico Hulkenberg","bor":"Gabriel Bortoleto","lin":"Arvid Lindblad",
    "law":"Liam Lawson",   "alo":"Fernando Alonso","str":"Lance Stroll",
    "alb":"Alexander Albon","sai":"Carlos Sainz", "per":"Sergio Perez",
    "bot":"Valtteri Bottas","tsu":"Yuki Tsunoda", "ric":"Daniel Ricciardo",
    "mag":"Kevin Magnussen","doo":"Jack Doohan",  "zho":"Zhou Guanyu",
}

TEAM_ALIASES = {
    "redbull":"Red Bull","rb":"Red Bull","red bull racing":"Red Bull",
    "scuderia ferrari":"Ferrari","ferrari hp":"Ferrari",
    "mercedes amg":"Mercedes","amg":"Mercedes",
    "mclaren f1":"McLaren","mclaren mercedes":"McLaren",
    "aston martin f1":"Aston Martin","aston":"Aston Martin",
    "bt alpine":"Alpine","alpine f1":"Alpine",
    "stake f1":"Kick Sauber","kick sauber":"Kick Sauber","sauber":"Kick Sauber",
    "racing bulls":"Racing Bulls","rb f1":"Racing Bulls","alphatauri":"Racing Bulls","scuderia alphatauri":"Racing Bulls",
    "haas f1":"Haas","moneygram haas":"Haas",
    "williams racing":"Williams","williams f1":"Williams",
    "cadillac f1":"Cadillac","andretti cadillac":"Cadillac",
    "audi f1":"Audi","audi ag":"Audi",
}

CIRCUIT_ALIASES = {
    "australia":"Australian Grand Prix","melbourne":"Australian Grand Prix","albert park":"Australian Grand Prix",
    "china":"Chinese Grand Prix","shanghai":"Chinese Grand Prix",
    "japan":"Japanese Grand Prix","suzuka":"Japanese Grand Prix",
    "bahrain":"Bahrain Grand Prix","sakhir":"Bahrain Grand Prix",
    "saudi":"Saudi Arabian Grand Prix","jeddah":"Saudi Arabian Grand Prix",
    "miami":"Miami Grand Prix",
    "imola":"Emilia Romagna Grand Prix","emilia":"Emilia Romagna Grand Prix",
    "monaco":"Monaco Grand Prix","monte carlo":"Monaco Grand Prix",
    "canada":"Canadian Grand Prix","montreal":"Canadian Grand Prix",
    "spain":"Spanish Grand Prix","barcelona":"Spanish Grand Prix",
    "austria":"Austrian Grand Prix","spielberg":"Austrian Grand Prix","red bull ring":"Austrian Grand Prix",
    "britain":"British Grand Prix","silverstone":"British Grand Prix","uk":"British Grand Prix",
    "hungary":"Hungarian Grand Prix","budapest":"Hungarian Grand Prix","hungaroring":"Hungarian Grand Prix",
    "belgium":"Belgian Grand Prix","spa":"Belgian Grand Prix",
    "netherlands":"Dutch Grand Prix","zandvoort":"Dutch Grand Prix","dutch":"Dutch Grand Prix",
    "italy":"Italian Grand Prix","monza":"Italian Grand Prix",
    "azerbaijan":"Azerbaijan Grand Prix","baku":"Azerbaijan Grand Prix",
    "singapore":"Singapore Grand Prix","marina bay":"Singapore Grand Prix",
    "usa":"United States Grand Prix","austin":"United States Grand Prix","cota":"United States Grand Prix",
    "mexico":"Mexico City Grand Prix","mexico city":"Mexico City Grand Prix",
    "brazil":"São Paulo Grand Prix","interlagos":"São Paulo Grand Prix","sao paulo":"São Paulo Grand Prix",
    "las vegas":"Las Vegas Grand Prix","vegas":"Las Vegas Grand Prix",
    "qatar":"Qatar Grand Prix","lusail":"Qatar Grand Prix",
    "abu dhabi":"Abu Dhabi Grand Prix","yas marina":"Abu Dhabi Grand Prix",
}

COL_ALIASES = {
    "pos":"finish_position","position":"finish_position","result":"finish_position",
    "race_position":"finish_position","final_pos":"finish_position","p":"finish_position",
    "classified_position":"finish_position","finishing_position":"finish_position",
    "grid":"qualifying_position","qual":"qualifying_position","qualifying":"qualifying_position",
    "start":"qualifying_position","start_position":"qualifying_position","q":"qualifying_position",
    "name":"driver","pilot":"driver","racer":"driver",
    "constructor":"team","car":"team","entrant":"team",
    "gp":"circuit","race":"circuit","grand_prix":"circuit","event":"circuit",
    "year":"season",
    "stops":"pit_stops","pitstops":"pit_stops","pit_stop_count":"pit_stops",
    "pts":"points","point":"points",
    "tyre":"tire_strategy","tyres":"tire_strategy","strategy":"tire_strategy",
    "conditions":"weather","wx":"weather",
    "incident":"incidents","crash":"incidents","dnf_flag":"incidents",
    "penalty":"penalties",
}

POINTS_MAP = {1:25,2:18,3:15,4:12,5:10,6:8,7:6,8:4,9:2,10:1}


# ═══════════════════════════════════════════════════════
# FORMAT DETECTION
# ═══════════════════════════════════════════════════════

def detect_format(filename: str, raw_bytes: bytes) -> str:
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".csv":                       return "csv"
    if ext in [".xlsx",".xls",".xlsm"]:    return "excel"
    if ext == ".json":                      return "json"
    if ext == ".pdf":                       return "pdf"
    if ext in [".png",".jpg",".jpeg",".webp",".bmp",".tiff"]: return "image"
    if ext in [".txt",".md"]:              return "text"
    if raw_bytes[:4] == b"%PDF":           return "pdf"
    if raw_bytes[:2] == b"PK":             return "excel"
    try:
        snippet = raw_bytes[:500].decode("utf-8", errors="ignore").strip()
        if snippet.startswith("{") or snippet.startswith("["): return "json"
    except Exception:
        pass
    return "text"


# ═══════════════════════════════════════════════════════
# FORMAT PARSERS
# ═══════════════════════════════════════════════════════

def parse_csv(raw_bytes: bytes) -> pd.DataFrame:
    for sep in [",",";","\t","|"]:
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), sep=sep, engine="python")
            if len(df.columns) >= 2: return df
        except Exception:
            continue
    raise ValueError("Cannot parse CSV — try comma, semicolon, or tab separated")


def parse_excel(raw_bytes: bytes) -> pd.DataFrame:
    xl = pd.ExcelFile(io.BytesIO(raw_bytes))
    best = None
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        if best is None or len(df) > len(best):
            best = df
    if best is None:
        raise ValueError("No data found in Excel file")
    return best


def parse_json(raw_bytes: bytes) -> pd.DataFrame:
    data = json.loads(raw_bytes.decode("utf-8"))
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        for key in ["results","races","data","entries","drivers","classification","standings"]:
            if key in data and isinstance(data[key], list):
                return pd.DataFrame(data[key])
        if all(isinstance(v, dict) for v in data.values()):
            return pd.DataFrame(list(data.values()))
        return pd.DataFrame([data])
    raise ValueError("Unrecognized JSON structure")


def parse_pdf(raw_bytes: bytes) -> pd.DataFrame:
    try:
        import fitz
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return parse_freetext(text)
    except ImportError:
        raise ImportError("Install pymupdf: pip install pymupdf")


def parse_image(raw_bytes: bytes) -> pd.DataFrame:
    # Try pytesseract
    try:
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(io.BytesIO(raw_bytes)))
        return parse_freetext(text)
    except ImportError:
        pass
    # Try easyocr
    try:
        import easyocr
        import numpy as np
        from PIL import Image
        arr = np.array(Image.open(io.BytesIO(raw_bytes)))
        reader = easyocr.Reader(["en"], verbose=False)
        text = "\n".join(r[1] for r in reader.readtext(arr))
        return parse_freetext(text)
    except ImportError:
        pass
    raise RuntimeError(
        "Image OCR needs pytesseract or easyocr.\n"
        "pip install pytesseract   (+ install Tesseract app)\n"
        "pip install easyocr\n\n"
        "Or copy-paste the text from the image into the PASTE tab."
    )


def parse_freetext(text: str) -> pd.DataFrame:
    """
    Extracts race results from any free text:
    - Pasted results tables
    - Race reports / articles
    - OCR from screenshots
    - Leaderboard text
    """
    rows = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Detect circuit and season from header lines
    circuit = "Unknown Grand Prix"
    season = 2026
    for line in lines[:20]:
        ll = line.lower()
        for alias, name in CIRCUIT_ALIASES.items():
            if alias in ll:
                circuit = name
                break
        m = re.search(r"\b(202[3-9])\b", line)
        if m:
            season = int(m.group(1))

    skip_words = {"driver","team","pos","position","grid","points","pts","lap","time","gap","constructor"}

    for line in lines:
        # Skip obvious headers/separators
        clean = line.lower().strip("- =|")
        if not clean or clean in skip_words:
            continue
        if sum(1 for w in clean.split() if w in skip_words) >= 2:
            continue

        # Extract all numbers from line
        nums = re.findall(r"\b\d{1,2}\b", line)

        # Try to find driver name
        driver_found = None
        team_found = None

        # Check 3-letter abbreviations
        for token in line.upper().split():
            token_clean = re.sub(r"[^A-Z]","",token).lower()
            if token_clean in DRIVER_ABBREVS:
                full_name = DRIVER_ABBREVS[token_clean]
                driver_found = full_name
                team_found = DRIVER_TEAM_MAP.get(full_name.lower())
                break

        # Check full/partial names
        if not driver_found:
            for dk, tv in DRIVER_TEAM_MAP.items():
                parts = dk.split()
                # Full name or last name match
                if dk in line.lower() or (len(parts) > 1 and parts[-1] in line.lower()):
                    driver_found = dk.title()
                    team_found = tv
                    break

        if not driver_found or not nums:
            continue

        valid_pos = [int(n) for n in nums if 1 <= int(n) <= 22]
        if not valid_pos:
            continue

        finish_pos = valid_pos[0]
        qual_pos = valid_pos[1] if len(valid_pos) >= 2 else finish_pos
        pts_candidates = [int(n) for n in nums if 0 <= int(n) <= 26]
        points = pts_candidates[-1] if pts_candidates else POINTS_MAP.get(finish_pos, 0)

        rows.append({
            "driver": driver_found,
            "team": team_found or "Unknown",
            "finish_position": finish_pos,
            "qualifying_position": qual_pos,
            "points": points,
            "circuit": circuit,
            "season": season,
        })

    if not rows:
        raise ValueError(
            "Could not find driver names + positions in this text.\n"
            "Tip: Make sure driver names like 'Russell', 'Hamilton', or '3-letter codes' "
            "like RUS/HAM appear alongside position numbers."
        )

    df = pd.DataFrame(rows).drop_duplicates(subset=["driver"])
    return df


# ═══════════════════════════════════════════════════════
# NORMALIZERS
# ═══════════════════════════════════════════════════════

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str).str.strip().str.lower()
        .str.replace(r"[\s\-\/\\]","_",regex=True)
        .str.replace(r"[^\w]","",regex=True)
    )
    df.rename(columns={k:v for k,v in COL_ALIASES.items() if k in df.columns}, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def normalize_driver_names(df: pd.DataFrame) -> pd.DataFrame:
    if "driver" not in df.columns:
        return df
    def fix(name):
        if not isinstance(name, str): return str(name)
        key = name.strip().lower()
        # Full name
        if key in DRIVER_TEAM_MAP: return key.title()
        # 3-letter abbrev
        if key in DRIVER_ABBREVS: return DRIVER_ABBREVS[key]
        # Last name
        for dk in DRIVER_TEAM_MAP:
            parts = dk.split()
            if len(parts) > 1 and parts[-1] == key:
                return dk.title()
        return name.strip().title()
    df["driver"] = df["driver"].apply(fix)
    return df


def fill_teams(df: pd.DataFrame) -> pd.DataFrame:
    if "team" not in df.columns:
        df["team"] = "Unknown"
    def get_team(row):
        raw = str(row.get("team","")).strip().lower()
        if raw and raw not in ["unknown","nan",""]:
            if raw in TEAM_ALIASES: return TEAM_ALIASES[raw]
            return str(row["team"]).strip().title()
        key = str(row.get("driver","")).lower()
        return DRIVER_TEAM_MAP.get(key, "Unknown")
    df["team"] = df.apply(get_team, axis=1)
    return df


def normalize_circuit(df: pd.DataFrame) -> pd.DataFrame:
    if "circuit" not in df.columns:
        return df
    def fix(val):
        if not isinstance(val, str): return "Unknown Grand Prix"
        key = val.strip().lower()
        if key in CIRCUIT_ALIASES: return CIRCUIT_ALIASES[key]
        for alias, full in CIRCUIT_ALIASES.items():
            if alias in key: return full
        return val.strip().title()
    df["circuit"] = df["circuit"].apply(fix)
    return df


def fill_defaults(df: pd.DataFrame) -> pd.DataFrame:
    if "season" not in df.columns:      df["season"] = 2026
    if "round" not in df.columns:       df["round"] = 99
    if "circuit" not in df.columns:     df["circuit"] = "Unknown Grand Prix"
    if "location" not in df.columns:
        df["location"] = df["circuit"].str.replace(" Grand Prix","",regex=False).str.strip()
    if "weather" not in df.columns:     df["weather"] = "Dry"
    if "tire_strategy" not in df.columns: df["tire_strategy"] = "2-Stop"
    if "pit_stops" not in df.columns:   df["pit_stops"] = 2
    if "incidents" not in df.columns:   df["incidents"] = 0
    if "penalties" not in df.columns:   df["penalties"] = 0

    if "finish_position" not in df.columns:
        df["finish_position"] = range(1, len(df)+1)
    else:
        df["finish_position"] = pd.to_numeric(df["finish_position"], errors="coerce").fillna(20).clip(1,22).astype(int)

    if "qualifying_position" not in df.columns:
        df["qualifying_position"] = df["finish_position"]
    else:
        df["qualifying_position"] = pd.to_numeric(df["qualifying_position"], errors="coerce").fillna(df["finish_position"]).clip(1,22).astype(int)

    if "pole_position" not in df.columns:
        df["pole_position"] = (df["qualifying_position"] == 1).astype(int)
    if "points" not in df.columns:
        df["points"] = df["finish_position"].apply(lambda x: POINTS_MAP.get(int(x),0))
    else:
        df["points"] = pd.to_numeric(df["points"], errors="coerce").fillna(0).astype(float)
    if "podium" not in df.columns:
        df["podium"] = (df["finish_position"] <= 3).astype(int)
    if "win" not in df.columns:
        df["win"] = (df["finish_position"] == 1).astype(int)
    if "dnf" not in df.columns:
        df["dnf"] = 0
    return df


# ═══════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════

def smart_parse(uploaded_file) -> tuple:
    """
    Master parser. Takes Streamlit UploadedFile or (filename, bytes).
    Returns: (dataframe, format_detected, warnings_list)
    """
    warnings_out = []
    if hasattr(uploaded_file, "name"):
        filename = uploaded_file.name
        raw_bytes = uploaded_file.read()
    else:
        filename, raw_bytes = uploaded_file

    fmt = detect_format(filename, raw_bytes)
    logger.info(f"Format detected: {fmt} | File: {filename}")

    if fmt == "csv":       df = parse_csv(raw_bytes)
    elif fmt == "excel":   df = parse_excel(raw_bytes)
    elif fmt == "json":    df = parse_json(raw_bytes)
    elif fmt == "pdf":     df = parse_pdf(raw_bytes)
    elif fmt == "image":   df = parse_image(raw_bytes)
    else:                  df = parse_freetext(raw_bytes.decode("utf-8", errors="ignore"))

    df = normalize_df(df, warnings_out)
    return df, fmt, warnings_out


def normalize_df(df: pd.DataFrame, warnings_out: list = None) -> pd.DataFrame:
    if warnings_out is None: warnings_out = []
    df = normalize_columns(df)
    df = normalize_driver_names(df)
    df = fill_teams(df)
    df = normalize_circuit(df)
    df = fill_defaults(df)
    unknown = df[df["team"] == "Unknown"]["driver"].tolist()
    if unknown:
        warnings_out.append(f"⚠️ Could not find teams for: {', '.join(str(x) for x in unknown[:5])}")
    return df


def preview_parsed(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["driver","team","finish_position","qualifying_position",
            "circuit","season","weather","points","tire_strategy","pit_stops"]
    return df[[c for c in cols if c in df.columns]].copy()