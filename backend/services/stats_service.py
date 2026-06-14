from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from database.models import Diagnosis, Patient


LESION_CLASSES = ("HE", "EX", "MA", "SE")


class StatsService:
    @staticmethod
    def overview() -> dict:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        return {
            "total_diagnoses": Diagnosis.query.filter_by(is_deleted=False).count(),
            "today_diagnoses": Diagnosis.query.filter(
                Diagnosis.is_deleted.is_(False),
                Diagnosis.created_at >= today_start,
            ).count(),
            "total_patients": Patient.query.filter_by(is_deleted=False).count(),
        }

    @staticmethod
    def lesion_frequencies() -> dict:
        diagnoses = Diagnosis.query.filter_by(is_deleted=False).all()
        present_counts = {lesion: 0 for lesion in LESION_CLASSES}
        total_counts = {lesion: 0 for lesion in LESION_CLASSES}
        total_areas = {lesion: 0.0 for lesion in LESION_CLASSES}
        total = max(len(diagnoses), 1)
        for diagnosis in diagnoses:
            lesion_counts = diagnosis.lesion_counts or {}
            lesion_areas = diagnosis.lesion_areas or {}
            for lesion in LESION_CLASSES:
                lesion_count = int(lesion_counts.get(lesion, 0) or 0)
                if lesion_count > 0:
                    present_counts[lesion] += 1
                total_counts[lesion] += lesion_count
                total_areas[lesion] += float(lesion_areas.get(lesion, 0.0) or 0.0)
        return {
            "lesion_frequencies": [
                {
                    "lesion_type": lesion,
                    "count": present_counts[lesion],
                    "percentage": round(present_counts[lesion] / total * 100.0, 2),
                    "total_count": total_counts[lesion],
                    "total_area": round(total_areas[lesion], 4),
                }
                for lesion in LESION_CLASSES
            ]
        }

    @staticmethod
    def trend(days: int = 30) -> dict:
        days = min(max(days, 1), 180)
        start_date = date.today() - timedelta(days=days - 1)
        buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: {lesion: [] for lesion in LESION_CLASSES})
        diagnoses = Diagnosis.query.filter(
            Diagnosis.is_deleted.is_(False),
            Diagnosis.created_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
        ).all()
        for diagnosis in diagnoses:
            key = diagnosis.created_at.date().isoformat()
            lesion_areas = diagnosis.lesion_areas or {}
            for lesion in LESION_CLASSES:
                buckets[key][lesion].append(float(lesion_areas.get(lesion, 0.0)))

        dates = [(start_date + timedelta(days=offset)).isoformat() for offset in range(days)]
        trend_points = []
        for item_date in dates:
            point = {"date": item_date}
            for lesion in LESION_CLASSES:
                values = buckets[item_date][lesion]
                point[lesion] = round(sum(values) / len(values), 4) if values else 0
            trend_points.append(point)
        return {"dates": dates, "trend": trend_points}
