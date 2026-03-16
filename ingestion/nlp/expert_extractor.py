"""
ingestion/nlp/expert_extractor.py
Extracts structured F1 insights from natural language text.

Input:  Raw text (article, tweet, quote, commentary)
Output: Structured ExpertPrediction records

Uses:
  - Rule-based NER (no heavy model required)
  - Keyword sentiment scoring
  - Confidence scoring from linguistic cues
  - Optional: spaCy / transformers if installed
"""

import re
import os
import sys
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── ENTITY DICTIONARIES ──────────────────────────────────────────

DRIVER_ENTITIES = {
    "russell": "George Russell",       "george russell": "George Russell",
    "antonelli": "Kimi Antonelli",     "kimi antonelli": "Kimi Antonelli",
    "leclerc": "Charles Leclerc",      "charles leclerc": "Charles Leclerc",
    "hamilton": "Lewis Hamilton",      "lewis hamilton": "Lewis Hamilton",
    "norris": "Lando Norris",          "lando norris": "Lando Norris",
    "piastri": "Oscar Piastri",        "oscar piastri": "Oscar Piastri",
    "verstappen": "Max Verstappen",    "max verstappen": "Max Verstappen",
    "hadjar": "Isack Hadjar",
    "bearman": "Oliver Bearman",       "ollie bearman": "Oliver Bearman",
    "ocon": "Esteban Ocon",
    "gasly": "Pierre Gasly",
    "colapinto": "Franco Colapinto",
    "hulkenberg": "Nico Hulkenberg",   "hülkenberg": "Nico Hulkenberg",
    "bortoleto": "Gabriel Bortoleto",
    "lindblad": "Arvid Lindblad",
    "lawson": "Liam Lawson",
    "alonso": "Fernando Alonso",       "fernando alonso": "Fernando Alonso",
    "stroll": "Lance Stroll",
    "albon": "Alexander Albon",        "alex albon": "Alexander Albon",
    "sainz": "Carlos Sainz",
    "perez": "Sergio Perez",           "checo": "Sergio Perez",
    "bottas": "Valtteri Bottas",
}

TEAM_ENTITIES = {
    "mercedes": "Mercedes",  "silver arrows": "Mercedes",  "merc": "Mercedes",
    "ferrari": "Ferrari",    "scuderia": "Ferrari",         "prancing horse": "Ferrari",
    "mclaren": "McLaren",    "woking": "McLaren",
    "red bull": "Red Bull",  "redbull": "Red Bull",         "rbr": "Red Bull",
    "aston martin": "Aston Martin",
    "alpine": "Alpine",
    "haas": "Haas",
    "williams": "Williams",
    "racing bulls": "Racing Bulls",   "rb": "Racing Bulls",  "visa cash app": "Racing Bulls",
    "audi": "Audi",
    "cadillac": "Cadillac",
}

CIRCUIT_TYPE_KEYWORDS = {
    "high_downforce":  ["monaco", "singapore", "hungary", "budapest", "imola", "slow", "twisty", "technical"],
    "power":           ["monza", "spa", "baku", "las vegas", "high speed", "top speed", "low downforce"],
    "balanced":        ["silverstone", "barcelona", "suzuka", "austin", "shanghai", "balanced"],
    "street":          ["street circuit", "city", "walls", "barriers", "narrow"],
}

PREDICTION_KEYWORDS = {
    "qualifying":  ["pole", "qualifying", "one lap", "grid", "q3", "front row"],
    "race":        ["race", "win", "victory", "podium", "finish", "championship"],
    "strategy":    ["strategy", "pit stop", "tyre", "tire", "undercut", "overcut", "degradation"],
    "tire":        ["compound", "soft", "medium", "hard", "tyre life", "degradation"],
}

POSITIVE_WORDS = [
    "strong", "dominant", "excellent", "fastest", "favorite", "favourite",
    "challenging", "competitive", "ahead", "lead", "win", "victory",
    "podium", "pole", "impressive", "brilliant", "great", "solid",
    "confident", "advantage", "edge", "better", "best", "top",
]

NEGATIVE_WORDS = [
    "struggle", "weak", "poor", "slow", "behind", "difficult",
    "challenging", "problem", "issue", "unreliable", "fragile",
    "disappointed", "worst", "bad", "concern", "worry", "doubt",
]

CONFIDENCE_BOOSTERS = {
    "certain": 0.95, "definitely": 0.92, "clearly": 0.88, "obviously": 0.85,
    "should": 0.75, "will": 0.80, "expect": 0.70, "predict": 0.72,
    "could": 0.55, "might": 0.50, "may": 0.50, "possibly": 0.45,
    "perhaps": 0.40, "unlikely": 0.25, "doubt": 0.20,
}


class ExpertExtractor:

    def __init__(self):
        self._spacy_nlp = None
        self._try_load_spacy()

    def _try_load_spacy(self):
        try:
            import spacy
            self._spacy_nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy loaded — using NER for entity extraction")
        except Exception:
            logger.info("spaCy not available — using rule-based entity extraction")

    def extract(self, text: str, source: str = "Unknown",
                source_url: str = None, race_weekend: str = None) -> dict:
        """
        Main extraction method.
        Returns structured dict matching ExpertPrediction schema.
        """
        text_lower = text.lower()

        drivers    = self._extract_drivers(text_lower)
        teams      = self._extract_teams(text_lower)
        circuit_type = self._classify_circuit_type(text_lower)
        pred_type  = self._classify_prediction_type(text_lower)
        sentiment, sentiment_score = self._analyze_sentiment(text_lower)
        confidence = self._estimate_confidence(text_lower, sentiment_score)
        entities   = self._extract_all_entities(text)

        # Primary driver and team
        driver_name = drivers[0] if drivers else None
        team_name = teams[0] if teams else self._infer_team_from_driver(driver_name)

        # Generate normalized prediction text
        prediction_text = self._generate_prediction_text(
            text, driver_name, team_name, pred_type, sentiment
        )

        return {
            "driver_name":      driver_name,
            "team_name":        team_name,
            "circuit_type":     circuit_type,
            "prediction_type":  pred_type,
            "prediction_text":  prediction_text,
            "raw_text":         text[:1000],
            "source":           source,
            "source_url":       source_url,
            "sentiment":        sentiment,
            "sentiment_score":  round(sentiment_score, 3),
            "confidence_score": round(confidence, 3),
            "entities":         entities,
            "race_weekend":     race_weekend,
        }

    def _extract_drivers(self, text: str) -> list:
        found = []
        for key, full_name in DRIVER_ENTITIES.items():
            if key in text and full_name not in found:
                found.append(full_name)
        return found

    def _extract_teams(self, text: str) -> list:
        found = []
        for key, team_name in TEAM_ENTITIES.items():
            if key in text and team_name not in found:
                found.append(team_name)
        return found

    def _infer_team_from_driver(self, driver: str) -> Optional[str]:
        DRIVER_TEAM = {
            "George Russell": "Mercedes",    "Kimi Antonelli": "Mercedes",
            "Charles Leclerc": "Ferrari",    "Lewis Hamilton": "Ferrari",
            "Lando Norris": "McLaren",       "Oscar Piastri": "McLaren",
            "Max Verstappen": "Red Bull",    "Isack Hadjar": "Red Bull",
            "Oliver Bearman": "Haas",        "Esteban Ocon": "Haas",
            "Pierre Gasly": "Alpine",        "Franco Colapinto": "Alpine",
            "Nico Hulkenberg": "Audi",       "Gabriel Bortoleto": "Audi",
            "Arvid Lindblad": "Racing Bulls","Liam Lawson": "Racing Bulls",
            "Fernando Alonso": "Aston Martin","Lance Stroll": "Aston Martin",
            "Alexander Albon": "Williams",   "Carlos Sainz": "Williams",
            "Sergio Perez": "Cadillac",      "Valtteri Bottas": "Cadillac",
        }
        return DRIVER_TEAM.get(driver)

    def _classify_circuit_type(self, text: str) -> str:
        scores = {}
        for ctype, keywords in CIRCUIT_TYPE_KEYWORDS.items():
            scores[ctype] = sum(1 for kw in keywords if kw in text)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "balanced"

    def _classify_prediction_type(self, text: str) -> str:
        scores = {}
        for ptype, keywords in PREDICTION_KEYWORDS.items():
            scores[ptype] = sum(1 for kw in keywords if kw in text)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "race"

    def _analyze_sentiment(self, text: str) -> tuple:
        pos = sum(1 for w in POSITIVE_WORDS if w in text)
        neg = sum(1 for w in NEGATIVE_WORDS if w in text)
        total = pos + neg
        if total == 0:
            return "neutral", 0.0
        score = (pos - neg) / total
        if score > 0.2:
            return "positive", score
        elif score < -0.2:
            return "negative", score
        return "neutral", score

    def _estimate_confidence(self, text: str, sentiment_score: float) -> float:
        base = 0.6
        for word, boost in CONFIDENCE_BOOSTERS.items():
            if word in text:
                base = (base + boost) / 2
                break
        # Adjust for sentiment strength
        base = min(0.95, base + abs(sentiment_score) * 0.15)
        return base

    def _extract_all_entities(self, text: str) -> dict:
        text_lower = text.lower()
        return {
            "drivers": self._extract_drivers(text_lower),
            "teams": self._extract_teams(text_lower),
            "numbers": re.findall(r'\b\d+\.?\d*\b', text),
            "lap_times": re.findall(r'\d:\d{2}\.\d+', text),
            "positions": re.findall(r'[Pp]\d{1,2}', text),
        }

    def _generate_prediction_text(self, raw: str, driver: str,
                                   team: str, pred_type: str, sentiment: str) -> str:
        subject = driver or team or "Unknown driver"
        if sentiment == "positive":
            if pred_type == "qualifying":
                return f"{subject} expected to show strong qualifying performance"
            elif pred_type == "race":
                return f"{subject} predicted to be competitive for race victory or podium"
            elif pred_type == "strategy":
                return f"{subject} likely has strong strategic options this weekend"
            else:
                return f"{subject} expected to perform well"
        elif sentiment == "negative":
            if pred_type == "qualifying":
                return f"{subject} may struggle in qualifying"
            else:
                return f"{subject} faces challenges this weekend"
        else:
            return f"{subject} performance unclear — mixed signals from analysts"


def extract_from_text(text: str, source: str = "Manual",
                      race_weekend: str = None) -> dict:
    """Convenience function — no class instantiation needed."""
    extractor = ExpertExtractor()
    return extractor.extract(text, source=source, race_weekend=race_weekend)


def batch_extract(texts: list, source: str = "Batch") -> list:
    """Extract from a list of text snippets."""
    extractor = ExpertExtractor()
    results = []
    for i, item in enumerate(texts):
        text = item if isinstance(item, str) else item.get("text", "")
        src = item.get("source", source) if isinstance(item, dict) else source
        url = item.get("url") if isinstance(item, dict) else None
        rw  = item.get("race_weekend") if isinstance(item, dict) else None
        result = extractor.extract(text, source=src, source_url=url, race_weekend=rw)
        results.append(result)
    return results


if __name__ == "__main__":
    samples = [
        "McLaren appears extremely strong at high-downforce circuits and Norris could challenge for pole at Monaco.",
        "Mercedes have clearly found a significant power unit advantage in 2026. Russell will definitely win again.",
        "Ferrari's new aero package looks great at Suzuka — Leclerc should challenge at the front in Japan.",
        "Verstappen is struggling with the new regulations, Red Bull seem to have a fundamental issue with the energy deployment system.",
        "Hamilton brings 20 years of Shanghai experience. He might just upset the Mercedes cars on strategy.",
    ]

    extractor = ExpertExtractor()
    print("\n=== Expert Insight Extraction Demo ===\n")
    for text in samples:
        result = extractor.extract(text, source="Demo")
        print(f"Input: {text[:80]}...")
        print(f"  Driver:      {result['driver_name']}")
        print(f"  Team:        {result['team_name']}")
        print(f"  Prediction:  {result['prediction_text']}")
        print(f"  Sentiment:   {result['sentiment']} ({result['sentiment_score']:+.2f})")
        print(f"  Confidence:  {result['confidence_score']:.2f}")
        print(f"  Circuit type:{result['circuit_type']}")
        print()
