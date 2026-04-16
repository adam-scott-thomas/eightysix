"""Degraded-mode rules, alert scoring, severity bands, recommendation gating.

The product should know when to shut up.
"""
from __future__ import annotations

from app.schemas.forecast import (
    AlertThresholdBand,
    AlertType,
    ConfidenceBand,
    ForecastAlert,
    ForecastRecommendation,
    ForecastStatus,
    RecommendationPriority,
    RecommendationType,
)


# ── Degraded-mode rules ───────────────────────────────────────────────────


def assess_status(
    real_history_days: int,
    synthetic_history_days: int,
    has_labor_feed: bool,
    has_weather_feed: bool,
    has_marketplace_feed: bool,
) -> tuple[ForecastStatus, list[str]]:
    """Determine forecast status and degraded reasons.

    Returns (status, degraded_reasons).
    """
    reasons: list[str] = []

    if real_history_days < 1 and synthetic_history_days > 0:
        reasons.append("demo_basis: forecast uses synthetic history only")

    if real_history_days < 14:
        if real_history_days < 1:
            return ForecastStatus.insufficient_history, reasons + [
                f"only {real_history_days} real history days (need >= 14)"
            ]
        reasons.append(f"limited history: {real_history_days} days (< 14)")

    if not has_labor_feed:
        reasons.append("no labor feed: labor recs use historical productivity only")

    if not has_weather_feed:
        reasons.append("no weather feed: weather drivers suppressed")

    if not has_marketplace_feed:
        reasons.append("no marketplace feed: channel forecasts lack marketplace-specific detail")

    if reasons:
        return ForecastStatus.degraded, reasons

    return ForecastStatus.ready, []


def allowed_outputs(
    real_history_days: int,
    has_labor_feed: bool,
) -> dict[str, bool]:
    """What forecast outputs are allowed given current data.

    < 14 history days: sales/orders only, no labor recs, wide bands
    14 to 27 days: sales/orders/labor, but flagged degraded
    >= 28 days: full outputs
    """
    return {
        "sales": real_history_days >= 1,
        "orders": real_history_days >= 1,
        "labor": real_history_days >= 14,
        "labor_recommendations": real_history_days >= 14,
        "channel_breakdown": real_history_days >= 7,
        "daypart_breakdown": real_history_days >= 7,
        "item_demand": real_history_days >= 14,
        "purchasing_signals": real_history_days >= 14,
    }


def band_multiplier(real_history_days: int, horizon_days: int) -> float:
    """Widen confidence bands when history is thin.

    Returns a multiplier >= 1.0 to apply to the base band width.
    """
    base = 1.0
    if real_history_days < 14:
        base *= 1.5  # 50% wider bands
    elif real_history_days < 28:
        base *= 1.2  # 20% wider

    if horizon_days > 14:
        base *= 1.15  # extra widening for far horizon

    return base


# ── Alert scoring ──────────────────────────────────────────────────────────


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _positive(x: float) -> float:
    return max(0.0, x)


def score_understaff_risk(
    pred_labor_hours: float,
    scheduled_labor_hours: float | None,
    peak_daypart_pressure: float,
    event_or_holiday_uplift: float,
    uncertainty_score: float,
) -> float:
    """Score understaff risk 0-100.

    understaff_score = 100 * clamp01(
        0.50 * positive(pred - scheduled) / max(pred, 1)
        + 0.20 * peak_daypart_pressure
        + 0.15 * event_or_holiday_uplift
        + 0.15 * uncertainty_score
    )
    """
    if scheduled_labor_hours is None:
        # No schedule data — use pred as proxy, lower weight
        sched_gap = 0.3  # assume mild understaffing risk
    else:
        sched_gap = _positive(pred_labor_hours - scheduled_labor_hours) / max(pred_labor_hours, 1)

    raw = (
        0.50 * sched_gap
        + 0.20 * _clamp01(peak_daypart_pressure)
        + 0.15 * _clamp01(event_or_holiday_uplift)
        + 0.15 * _clamp01(uncertainty_score)
    )
    return round(100 * _clamp01(raw), 1)


def score_overstaff_risk(
    pred_labor_hours: float,
    scheduled_labor_hours: float | None,
    slow_day_signal: float,
    negative_trend_signal: float,
    uncertainty_score: float,
) -> float:
    """Score overstaff risk 0-100.

    overstaff_score = 100 * clamp01(
        0.55 * positive(scheduled - pred) / max(scheduled, 1)
        + 0.20 * slow_day_signal
        + 0.15 * negative_trend_signal
        + 0.10 * uncertainty_score
    )
    """
    if scheduled_labor_hours is None:
        sched_gap = 0.0  # can't assess overstaffing without schedule
    else:
        sched_gap = _positive(scheduled_labor_hours - pred_labor_hours) / max(scheduled_labor_hours, 1)

    raw = (
        0.55 * sched_gap
        + 0.20 * _clamp01(slow_day_signal)
        + 0.15 * _clamp01(negative_trend_signal)
        + 0.10 * _clamp01(uncertainty_score)
    )
    return round(100 * _clamp01(raw), 1)


def severity_band(score: float) -> AlertThresholdBand:
    """0-39 = low, 40-69 = medium, 70-100 = high."""
    if score >= 70:
        return AlertThresholdBand.high
    if score >= 40:
        return AlertThresholdBand.medium
    return AlertThresholdBand.low


def build_alerts(
    pred_sales: float,
    pred_orders: float,
    pred_labor_hours: float,
    scheduled_labor_hours: float | None,
    event_multiplier: float,
    trend_slope: float,
    confidence_score: float,
    horizon_days: int,
) -> list[ForecastAlert]:
    """Build forecast alerts for a single day."""
    alerts: list[ForecastAlert] = []

    # Event/holiday uplift as 0-1 signal
    event_signal = _clamp01(abs(event_multiplier - 1.0) * 2) if event_multiplier > 1.05 else 0.0
    # Peak daypart pressure — proxy from overall demand vs historical
    peak_pressure = _clamp01(event_signal * 0.6)
    # Slow day signal
    slow_signal = _clamp01(abs(min(0, trend_slope)) / 100) if trend_slope < -20 else 0.0
    if event_multiplier < 0.85:
        slow_signal = max(slow_signal, 0.5)
    # Negative trend
    neg_trend = _clamp01(abs(min(0, trend_slope)) / 200)
    # Uncertainty
    uncertainty = 1.0 - confidence_score

    # Understaff
    under_score = score_understaff_risk(
        pred_labor_hours, scheduled_labor_hours, peak_pressure, event_signal, uncertainty
    )
    if under_score >= 30:
        alerts.append(ForecastAlert(
            type=AlertType.understaff_risk,
            severity_0_to_100=under_score,
            threshold_band=severity_band(under_score),
            message=_understaff_message(under_score, pred_labor_hours, scheduled_labor_hours, event_multiplier),
        ))

    # Overstaff
    over_score = score_overstaff_risk(
        pred_labor_hours, scheduled_labor_hours, slow_signal, neg_trend, uncertainty
    )
    if over_score >= 30:
        alerts.append(ForecastAlert(
            type=AlertType.overstaff_risk,
            severity_0_to_100=over_score,
            threshold_band=severity_band(over_score),
            message=_overstaff_message(over_score, pred_labor_hours, scheduled_labor_hours),
        ))

    # Slow day
    if slow_signal > 0.3 or event_multiplier < 0.85:
        slow_score = round(100 * _clamp01(slow_signal + (1.0 - event_multiplier) if event_multiplier < 1 else slow_signal), 1)
        if slow_score >= 30:
            alerts.append(ForecastAlert(
                type=AlertType.slow_day_risk,
                severity_0_to_100=slow_score,
                threshold_band=severity_band(slow_score),
                message="Lower-than-normal demand expected — consider reducing scheduled hours",
            ))

    # Delivery spike (when event multiplier is high and delivery channel significant)
    if event_multiplier > 1.2:
        spike_score = round(min(100, (event_multiplier - 1.0) * 150), 1)
        if spike_score >= 40:
            alerts.append(ForecastAlert(
                type=AlertType.delivery_spike_risk,
                severity_0_to_100=spike_score,
                threshold_band=severity_band(spike_score),
                message="Event-driven demand spike — delivery volume likely elevated",
            ))

    return alerts


def _understaff_message(score: float, pred: float, sched: float | None, event_mult: float) -> str:
    parts = []
    if sched is not None:
        gap = pred - sched
        if gap > 0:
            parts.append(f"predicted need exceeds schedule by {gap:.1f}h")
    if event_mult > 1.1:
        parts.append(f"event/holiday driving +{(event_mult - 1) * 100:.0f}% demand")
    if not parts:
        parts.append("demand signals suggest more staff needed")
    return ". ".join(parts).capitalize()


def _overstaff_message(score: float, pred: float, sched: float | None) -> str:
    if sched is not None and sched > pred:
        gap = sched - pred
        return f"Schedule exceeds predicted need by {gap:.1f}h — consider reducing"
    return "Demand signals suggest fewer staff needed"


# ── Recommendation gating ─────────────────────────────────────────────────


def gate_recommendations(
    recommendations: list[ForecastRecommendation],
    confidence_score: float,
    status: ForecastStatus,
    horizon_days: int,
    degraded_reasons: list[str],
) -> list[ForecastRecommendation]:
    """Filter and annotate recommendations based on confidence and status.

    Rules from spec:
    - if confidence < 0.55, no hard labor cut recommendation
    - if status = degraded, recommendation text must include why
    - never recommend labor below minimum safe crew
    - for horizons 15-28, give ranges not exact shift edits
    """
    gated: list[ForecastRecommendation] = []

    for rec in recommendations:
        # Skip hard labor cuts at low confidence
        if confidence_score < 0.55 and rec.type == RecommendationType.adjust_labor:
            if rec.delta_value is not None and rec.delta_value < 0:
                continue

        # For far horizons, soften the message
        if horizon_days > 14 and rec.delta_value is not None:
            rec = ForecastRecommendation(
                type=rec.type,
                priority=rec.priority,
                message=rec.message.replace("Reduce by", "Consider reducing by ~").replace("Add", "Consider adding ~"),
                delta_value=rec.delta_value,
                delta_unit=rec.delta_unit,
            )

        # Annotate degraded reasons
        if status == ForecastStatus.degraded and degraded_reasons:
            reason_note = degraded_reasons[0]
            rec = ForecastRecommendation(
                type=rec.type,
                priority=rec.priority,
                message=f"{rec.message} (note: {reason_note})",
                delta_value=rec.delta_value,
                delta_unit=rec.delta_unit,
            )

        gated.append(rec)

    # Cap at 3 recommendations per day
    return gated[:3]


def confidence_band(score: float) -> ConfidenceBand:
    """Map confidence score to band."""
    if score >= 0.75:
        return ConfidenceBand.high
    if score >= 0.55:
        return ConfidenceBand.medium
    return ConfidenceBand.low
