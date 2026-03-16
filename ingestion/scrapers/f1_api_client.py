"""
ingestion/scrapers/f1_api_client.py
Fetches F1 race data from OpenF1 and Ergast APIs.

Methods used by AutoSync:
  get_completed_races_this_season(season) -> list[int]  (round numbers)
  fetch_and_format_for_platform(season, round_number)   -> pd.DataFrame
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
CACHE_DIR  = os.path.join(BASE_DIR, "data", "api_cache")

OPENF1_BASE = "https://api.openf1.org/v1"
ERGAST_BASE = "http://ergast.com/api/f1"

POINTS_MAP = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}

TEAM_MAP = {
    "mclaren": "McLaren", "mercedes": "Mercedes", "ferrari": "Ferrari",
    "red bull": "Red Bull", "red bull racing": "Red Bull",
    "aston martin": "Aston Martin", "alpine": "Alpine",
    "haas": "Haas", "haas f1 team": "Haas",
    "williams": "Williams", "racing bulls": "Racing Bulls",
    "rb": "Racing Bulls", "visa cash app rb": "Racing Bulls",
    "audi": "Audi", "cadillac": "Cadillac",
    "kick sauber": "Kick Sauber", "sauber": "Kick Sauber",
}


class F1APIClient:

    def __init__(self, timeout: int = 10):
        self.timeout   = timeout
        self.session   = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_completed_races_this_season(self, season: int) -> list:
        """Return sorted list of round numbers that are completed (race date <= today)."""
        try:
            rounds = self._ergast_schedule(season)
            today  = date.today()
            return sorted(
                r["round"] for r in rounds
                if r.get("date") and date.fromisoformat(r["date"]) <= today
            )
        except Exception as e:
            logger.warning(f"Could not fetch schedule for {season}: {e}")
            return []

    def fetch_and_format_for_platform(self, season: int, round_number: int) -> pd.DataFrame:
        """
        Fetch race results for (season, round_number) and return a DataFrame
        in the platform column format:
          season, round, circuit, location, driver, team,
          qualifying_position, pole_position, finish_position,
          weather, tire_strategy, pit_stops, incidents, penalties,
          points, podium, win
        """
        cache_key = f"{season}_r{round_number:02d}_results.json"
        cached    = self._cache_read(cache_key)

        if cached:
            logger.info(f"  Using cached data for {season} R{round_number}")
            return self._format_df(cached, season, round_number)

        # Try Ergast first (reliable historical data)
        data = self._ergast_results(season, round_number)
        if data:
            self._cache_write(cache_key, data)
            return self._format_df(data, season, round_number)

        # Fall back to OpenF1 (real-time, 2023+)
        data = self._openf1_results(season, round_number)
        if data:
            self._cache_write(cache_key, data)
            return self._format_df(data, season, round_number)

        logger.warning(f"No data found for {season} R{round_number} from any source")
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Ergast API
    # ------------------------------------------------------------------

    def _ergast_schedule(self, season: int) -> list:
        url  = f"{ERGAST_BASE}/{season}.json?limit=30"
        resp = self._get(url)
        if not resp:
            return []
        races = resp.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return [
            {"round": int(r["round"]), "date": r.get("date", ""), "name": r.get("raceName", "")}
            for r in races
        ]

    def _ergast_results(self, season: int, round_number: int) -> Optional[dict]:
        url  = f"{ERGAST_BASE}/{season}/{round_number}/results.json"
        resp = self._get(url)
        if not resp:
            return None
        races = resp.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            return None

        race  = races[0]
        rows  = []
        for r in race.get("Results", []):
            driver_name = f"{r['Driver']['givenName']} {r['Driver']['familyName']}"
            team_raw    = r.get("Constructor", {}).get("name", "")
            team        = TEAM_MAP.get(team_raw.lower(), team_raw.title())
            pos         = self._safe_int(r.get("position"))
            grid        = self._safe_int(r.get("grid"))
            pts         = float(r.get("points", POINTS_MAP.get(pos, 0) if pos else 0))
            status      = r.get("status", "Finished")
            dnf         = 0 if status == "Finished" else 1

            rows.append({
                "driver":               driver_name,
                "team":                 team,
                "finish_position":      pos,
                "qualifying_position":  grid,
                "points":               pts,
                "dnf":                  dnf,
                "circuit":              race.get("raceName", ""),
                "location":             race.get("Circuit", {}).get("Location", {}).get("locality", ""),
            })

        return {"rows": rows, "circuit": race.get("raceName", ""), "location": race.get("Circuit", {}).get("Location", {}).get("locality", "")}

    # ------------------------------------------------------------------
    # OpenF1 API
    # ------------------------------------------------------------------

    def _openf1_results(self, season: int, round_number: int) -> Optional[dict]:
        # Get session key for the race session
        url  = f"{OPENF1_BASE}/sessions?year={season}&session_name=Race&meeting_key=latest"
        # Try by round via meeting
        meet_url = f"{OPENF1_BASE}/meetings?year={season}"
        resp     = self._get(meet_url)
        if not resp or not isinstance(resp, list) or len(resp) < round_number:
            return None

        meetings = sorted(resp, key=lambda m: m.get("date_start", ""))
        if round_number > len(meetings):
            return None

        meeting    = meetings[round_number - 1]
        meeting_key = meeting.get("meeting_key")
        circuit    = meeting.get("meeting_official_name", meeting.get("meeting_name", ""))
        location   = meeting.get("location", "")

        sess_url = f"{OPENF1_BASE}/sessions?meeting_key={meeting_key}&session_name=Race"
        sess_resp = self._get(sess_url)
        if not sess_resp or not isinstance(sess_resp, list) or not sess_resp:
            return None

        session_key = sess_resp[0].get("session_key")

        pos_url  = f"{OPENF1_BASE}/position?session_key={session_key}&position%3C=20"
        pos_resp = self._get(pos_url)
        if not pos_resp or not isinstance(pos_resp, list):
            return None

        # Get final position per driver
        final_pos = {}
        for p in pos_resp:
            drv = p.get("driver_number")
            if drv:
                final_pos[drv] = p  # last entry wins (most recent)

        # Get driver info
        drv_url  = f"{OPENF1_BASE}/drivers?session_key={session_key}"
        drv_resp = self._get(drv_url) or []
        drv_map  = {d.get("driver_number"): d for d in drv_resp if isinstance(d, dict)}

        rows = []
        for drv_num, pos_data in final_pos.items():
            drv_info    = drv_map.get(drv_num, {})
            driver_name = drv_info.get("full_name", f"Driver #{drv_num}")
            team_raw    = drv_info.get("team_name", "")
            team        = TEAM_MAP.get(team_raw.lower(), team_raw.title())
            pos         = self._safe_int(pos_data.get("position"))
            pts         = POINTS_MAP.get(pos, 0) if pos else 0

            rows.append({
                "driver":               driver_name,
                "team":                 team,
                "finish_position":      pos,
                "qualifying_position":  None,
                "points":               float(pts),
                "dnf":                  0,
                "circuit":              circuit,
                "location":             location,
            })

        return {"rows": rows, "circuit": circuit, "location": location}

    # ------------------------------------------------------------------
    # DataFrame formatter
    # ------------------------------------------------------------------

    def _format_df(self, data: dict, season: int, round_number: int) -> pd.DataFrame:
        rows    = data.get("rows", [])
        circuit = data.get("circuit", "")
        location = data.get("location", "")

        records = []
        for r in rows:
            pos      = r.get("finish_position")
            grid     = r.get("qualifying_position")
            is_pole  = 1 if grid == 1 else 0
            is_podium = 1 if pos and pos <= 3 and not r.get("dnf") else 0
            is_win    = 1 if pos == 1 and not r.get("dnf") else 0

            records.append({
                "season":               season,
                "round":                round_number,
                "circuit":              r.get("circuit", circuit),
                "location":             r.get("location", location),
                "driver":               r.get("driver", ""),
                "team":                 r.get("team", ""),
                "qualifying_position":  grid,
                "pole_position":        is_pole,
                "finish_position":      pos,
                "weather":              "Dry",
                "tire_strategy":        "2-Stop",
                "pit_stops":            2,
                "incidents":            0,
                "penalties":            0,
                "points":               r.get("points", 0),
                "podium":               is_podium,
                "win":                  is_win,
            })

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get(self, url: str):
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug(f"GET {url} failed: {e}")
            return None

    def _cache_read(self, key: str):
        path = os.path.join(CACHE_DIR, key)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _cache_write(self, key: str, data):
        path = os.path.join(CACHE_DIR, key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @staticmethod
    def _safe_int(val) -> Optional[int]:
        try:
            return int(float(val)) if val is not None and str(val) not in ("nan", "") else None
        except (ValueError, TypeError):
            return None
