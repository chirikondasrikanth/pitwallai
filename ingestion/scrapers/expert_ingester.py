"""
ingestion/scrapers/expert_ingester.py
Ingests expert opinions, articles, and social media commentary into the DB.
Uses the NLP ExpertExtractor to convert raw text to structured predictions.
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ingestion.db.schema import (
    init_db, get_session, get_engine,
    Driver, Race, ExpertPrediction, IngestionLog
)
from ingestion.nlp.expert_extractor import ExpertExtractor, batch_extract

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


class ExpertIngester:

    def __init__(self, db_url: str = None):
        self.engine    = init_db(get_engine(db_url))
        self.session   = get_session(self.engine)
        self.extractor = ExpertExtractor()

    def _get_driver_id(self, name: str) -> Optional[int]:
        if not name:
            return None
        obj = self.session.query(Driver).filter_by(full_name=name).first()
        return obj.id if obj else None

    def _get_race_id(self, race_weekend: str, season: int = 2026) -> Optional[int]:
        if not race_weekend:
            return None
        race = self.session.query(Race).filter(
            Race.season == season,
            Race.race_name.ilike(f"%{race_weekend}%")
        ).first()
        return race.id if race else None

    def ingest_text(self, text: str, source: str = "Manual",
                    source_url: str = None, race_weekend: str = None,
                    season: int = 2026) -> dict:
        """
        Extract structured prediction from raw text and save to DB.
        """
        start = time.time()
        try:
            extracted = self.extractor.extract(
                text, source=source,
                source_url=source_url,
                race_weekend=race_weekend
            )

            driver_id = self._get_driver_id(extracted.get("driver_name"))
            race_id   = self._get_race_id(race_weekend, season)

            pred = ExpertPrediction(
                race_id          = race_id,
                driver_id        = driver_id,
                source           = source,
                source_url       = source_url,
                raw_text         = text[:1000],
                driver_name      = extracted["driver_name"],
                team_name        = extracted["team_name"],
                circuit_type     = extracted["circuit_type"],
                prediction_type  = extracted["prediction_type"],
                prediction_text  = extracted["prediction_text"],
                sentiment        = extracted["sentiment"],
                sentiment_score  = extracted["sentiment_score"],
                confidence_score = extracted["confidence_score"],
                entities         = extracted["entities"],
                race_weekend     = race_weekend,
            )

            self.session.add(pred)
            self.session.commit()

            logger.info(f"  Ingested expert insight: {extracted['driver_name']} | "
                        f"{extracted['sentiment']} | conf={extracted['confidence_score']:.2f}")

            return {
                "success": True,
                "extracted": extracted,
                "duration": round(time.time()-start, 3)
            }

        except Exception as e:
            self.session.rollback()
            logger.error(f"Expert ingestion failed: {e}")
            return {"success": False, "error": str(e)}

    def ingest_batch(self, items: list, season: int = 2026) -> dict:
        """
        Ingest a list of expert texts.
        Each item can be a plain string or dict with keys:
          text, source, source_url, race_weekend
        """
        results = {"success": 0, "failed": 0, "total": len(items)}

        for item in items:
            if isinstance(item, str):
                r = self.ingest_text(item, season=season)
            else:
                r = self.ingest_text(
                    item.get("text",""),
                    source=item.get("source","Unknown"),
                    source_url=item.get("url"),
                    race_weekend=item.get("race_weekend"),
                    season=season
                )
            if r.get("success"):
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Batch ingestion: {results['success']}/{results['total']} succeeded")
        return results

    def get_predictions(self, driver_name: str = None,
                         race_weekend: str = None,
                         min_confidence: float = 0.0) -> list:
        """Query stored expert predictions with filters."""
        query = self.session.query(ExpertPrediction)
        if driver_name:
            query = query.filter(ExpertPrediction.driver_name.ilike(f"%{driver_name}%"))
        if race_weekend:
            query = query.filter(ExpertPrediction.race_weekend.ilike(f"%{race_weekend}%"))
        if min_confidence > 0:
            query = query.filter(ExpertPrediction.confidence_score >= min_confidence)
        results = query.order_by(ExpertPrediction.ingested_at.desc()).all()
        return [{
            "driver":     r.driver_name,
            "team":       r.team_name,
            "prediction": r.prediction_text,
            "sentiment":  r.sentiment,
            "confidence": r.confidence_score,
            "source":     r.source,
            "weekend":    r.race_weekend,
            "ingested":   str(r.ingested_at)[:19],
        } for r in results]

    def get_driver_sentiment_summary(self, race_weekend: str = None) -> dict:
        """
        Aggregate expert sentiments per driver.
        Returns: {driver: {avg_confidence, sentiment_breakdown, prediction_count}}
        """
        query = self.session.query(ExpertPrediction)
        if race_weekend:
            query = query.filter(ExpertPrediction.race_weekend.ilike(f"%{race_weekend}%"))

        records = query.all()
        summary = {}

        for r in records:
            if not r.driver_name:
                continue
            if r.driver_name not in summary:
                summary[r.driver_name] = {
                    "predictions": 0,
                    "avg_confidence": 0,
                    "total_sentiment": 0,
                    "positive": 0, "negative": 0, "neutral": 0,
                }
            s = summary[r.driver_name]
            s["predictions"] += 1
            s["avg_confidence"] += r.confidence_score or 0
            s["total_sentiment"] += r.sentiment_score or 0
            s[r.sentiment or "neutral"] += 1

        for driver, s in summary.items():
            n = s["predictions"]
            s["avg_confidence"] = round(s["avg_confidence"] / n, 3)
            s["avg_sentiment"]  = round(s["total_sentiment"] / n, 3)
            del s["total_sentiment"]

        return dict(sorted(summary.items(),
                           key=lambda x: x[1]["avg_confidence"], reverse=True))


# ─── SAMPLE DATA FOR TESTING ──────────────────────────────────────
SAMPLE_EXPERT_INSIGHTS = [
    {
        "text": "Mercedes have clearly found a significant power unit advantage in 2026. Russell will definitely win again in China — he's been fastest in every session.",
        "source": "Sky Sports F1",
        "race_weekend": "Chinese Grand Prix",
    },
    {
        "text": "McLaren appears extremely strong at high-downforce circuits and Norris could challenge for pole at Monaco. The MCL40 has the best mechanical grip on the grid.",
        "source": "The Race",
        "race_weekend": "Monaco Grand Prix",
    },
    {
        "text": "Ferrari's new aero package looks great at Suzuka. Leclerc should challenge at the front in Japan — his lap in Q3 was exceptional.",
        "source": "Autosport",
        "race_weekend": "Japanese Grand Prix",
    },
    {
        "text": "Verstappen is struggling with the new 2026 regulations. Red Bull seem to have a fundamental issue with their energy deployment system. Could be a long season.",
        "source": "RacingNews365",
        "race_weekend": "Australian Grand Prix",
    },
    {
        "text": "Hamilton brings 20 years of Shanghai experience. He might just upset the Mercedes cars on strategy in China. Ferrari's start procedure has been incredible.",
        "source": "BBC Sport",
        "race_weekend": "Chinese Grand Prix",
    },
    {
        "text": "Kimi Antonelli is the real deal. Youngest ever pole in Shanghai. This kid is going to be a world champion — possibly this year if Mercedes keeps this pace.",
        "source": "F1.com",
        "race_weekend": "Chinese Grand Prix",
    },
    {
        "text": "Aston Martin is clearly struggling at the start of 2026. Alonso can't do miracles with a car that's a second off the pace. The AMR26 needs significant upgrades.",
        "source": "Motorsport.com",
        "race_weekend": "Chinese Grand Prix",
    },
]


if __name__ == "__main__":
    from ingestion.db.seeder import seed_all

    ingester = ExpertIngester()
    seed_all(ingester.session)

    print("\n=== Ingesting Expert Insights ===")
    result = ingester.ingest_batch(SAMPLE_EXPERT_INSIGHTS)
    print(f"Batch result: {result}")

    print("\n=== Driver Sentiment Summary (Chinese GP) ===")
    summary = ingester.get_driver_sentiment_summary("Chinese Grand Prix")
    for driver, data in list(summary.items())[:5]:
        print(f"  {driver:<22} | conf={data['avg_confidence']:.2f} | "
              f"+{data['positive']} -{data['negative']} ={data['neutral']} | "
              f"n={data['predictions']}")

    print("\n=== All Predictions for Russell ===")
    preds = ingester.get_predictions(driver_name="Russell")
    for p in preds:
        print(f"  [{p['confidence']:.2f}] {p['prediction']} — {p['source']}")
