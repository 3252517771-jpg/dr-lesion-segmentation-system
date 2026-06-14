from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.stats_service import StatsService


stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.get("/overview")
def overview():
    return jsonify(StatsService.overview())


@stats_bp.get("/lesions")
def lesions():
    return jsonify(StatsService.lesion_frequencies())


@stats_bp.get("/trend")
def trend():
    return jsonify(StatsService.trend(days=request.args.get("days", 30, type=int)))
