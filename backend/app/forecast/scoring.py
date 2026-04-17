"""Scoring framework — WAPE, MAE, bias, interval coverage, model score, promotion.

Score by horizon bucket, not one blended number, because a 3-day forecast
and a 28-day forecast are not the same species.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.forecast import BacktestSnapshot, HorizonBucket, HorizonScore


# ── Launch gate targets ────────────────────────────────────────────────────

LAUNCH_GATES = {
    HorizonBucket.d1_7: {
        "sales_wape": 0.15,
        "orders_wape": 0.12,
        "labor_wmae": 4.0,  # hours/day
        "abs_bias": 0.05,
    },
    HorizonBucket.d8_14: {
        "sales_wape": 0.18,
        "orders_wape": 0.15,
        "labor_wmae": 5.0,
        "abs_bias": 0.06,
    },
    HorizonBucket.d15_28: {
        "sales_wape": 0.22,
        "orders_wape": 0.20,
        "labor_wmae": 6.5,
        "abs_bias": 0.08,
    },
}

# Interval coverage target range
INTERVAL_COVERAGE_MIN = 0.75
INTERVAL_COVERAGE_MAX = 0.90

# Bucket weights for overall score
BUCKET_WEIGHTS = {
    HorizonBucket.d1_7: 0.50,
    HorizonBucket.d8_14: 0.30,
    HorizonBucket.d15_28: 0.20,
}

# Component weights within a bucket
COMPONENT_WEIGHTS = {
    "sales": 0.35,
    "orders": 0.25,
    "labor": 0.20,
    "bias": 0.10,
    "interval": 0.10,
}


# ── Metric functions ───────────────────────────────────────────────────────


def wape(predictions: list[float], actuals: list[float]) -> float:
    """Weighted Absolute Percentage Error = sum(|pred - actual|) / sum(actual)."""
    total_actual = sum(actuals)
    if total_actual == 0:
        return 0.0
    return sum(abs(p - a) for p, a in zip(predictions, actuals)) / total_actual


def mae(predictions: list[float], actuals: list[float]) -> float:
    """Mean Absolute Error."""
    if not predictions:
        return 0.0
    return sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)


def weighted_mae(
    predictions: list[float],
    actuals: list[float],
    underpredict_weight: float = 1.75,
    overpredict_weight: float = 1.00,
) -> float:
    """Weighted MAE where underprediction is penalized harder.

    labor_error_weight =
        pred < actual ? 1.75 : 1.00
    """
    if not predictions:
        return 0.0
    total = 0.0
    for p, a in zip(predictions, actuals):
        error = abs(p - a)
        weight = underpredict_weight if p < a else overpredict_weight
        total += error * weight
    return total / len(predictions)


def bias(predictions: list[float], actuals: list[float]) -> float:
    """Bias = sum(pred - actual) / sum(actual). Positive = overpredicting."""
    total_actual = sum(actuals)
    if total_actual == 0:
        return 0.0
    return sum(p - a for p, a in zip(predictions, actuals)) / total_actual


def interval_coverage(
    actuals: list[float],
    lows: list[float],
    highs: list[float],
) -> float:
    """Fraction of actuals that fall within [low, high] band."""
    if not actuals:
        return 0.0
    hits = sum(1 for a, lo, hi in zip(actuals, lows, highs) if lo <= a <= hi)
    return hits / len(actuals)


def channel_mix_error(
    pred_shares: list[dict[str, float]],
    actual_shares: list[dict[str, float]],
) -> float:
    """Sum of absolute share-point deltas / 2, averaged across days."""
    if not pred_shares:
        return 0.0
    total = 0.0
    for pred, actual in zip(pred_shares, actual_shares):
        all_channels = set(pred.keys()) | set(actual.keys())
        day_error = sum(abs(pred.get(c, 0) - actual.get(c, 0)) for c in all_channels) / 2
        total += day_error
    return total / len(pred_shares)


def daypart_mix_error(
    pred_shares: list[dict[str, float]],
    actual_shares: list[dict[str, float]],
) -> float:
    """Same as channel_mix_error but for dayparts."""
    return channel_mix_error(pred_shares, actual_shares)


# ── Score component ────────────────────────────────────────────────────────


def score_component(actual_metric: float, target: float) -> float:
    """Normalize a metric to 0-100 relative to its launch gate target.

    score = max(0, min(100, 100 * (1 - actual / target)))
    A score of 100 means the metric is 0 (perfect).
    A score of 0 means the metric equals or exceeds the target (at gate).
    """
    if target == 0:
        return 100.0 if actual_metric == 0 else 0.0
    return max(0.0, min(100.0, 100.0 * (1.0 - actual_metric / target)))


def interval_score(coverage: float) -> float:
    """Score interval coverage. Target range: 75%-90%.

    Too low = bands too tight. Too high = bands too lazy.
    """
    if INTERVAL_COVERAGE_MIN <= coverage <= INTERVAL_COVERAGE_MAX:
        return 100.0
    if coverage < INTERVAL_COVERAGE_MIN:
        # Penalty scales with how far below min
        return max(0.0, 100.0 * (coverage / INTERVAL_COVERAGE_MIN))
    # Above max — bands are too wide
    excess = coverage - INTERVAL_COVERAGE_MAX
    return max(0.0, 100.0 * (1.0 - excess / (1.0 - INTERVAL_COVERAGE_MAX)))


# ── Horizon bucket scoring ─────────────────────────────────────────────────


@dataclass
class BucketEvalData:
    """Raw evaluation data for one horizon bucket."""
    sales_preds: list[float]
    sales_actuals: list[float]
    sales_lows: list[float]
    sales_highs: list[float]
    orders_preds: list[float]
    orders_actuals: list[float]
    orders_lows: list[float]
    orders_highs: list[float]
    labor_preds: list[float]
    labor_actuals: list[float]
    labor_lows: list[float]
    labor_highs: list[float]
    channel_pred_shares: list[dict[str, float]]
    channel_actual_shares: list[dict[str, float]]
    daypart_pred_shares: list[dict[str, float]]
    daypart_actual_shares: list[dict[str, float]]


def score_bucket(bucket: HorizonBucket, data: BucketEvalData) -> HorizonScore:
    """Score one horizon bucket."""
    gates = LAUNCH_GATES[bucket]

    s_wape = wape(data.sales_preds, data.sales_actuals)
    o_wape = wape(data.orders_preds, data.orders_actuals)
    l_wmae = weighted_mae(data.labor_preds, data.labor_actuals)
    b = abs(bias(data.sales_preds, data.sales_actuals))
    ic = interval_coverage(data.sales_actuals, data.sales_lows, data.sales_highs)
    ch_err = channel_mix_error(data.channel_pred_shares, data.channel_actual_shares)
    dp_err = daypart_mix_error(data.daypart_pred_shares, data.daypart_actual_shares)

    sales_sc = score_component(s_wape, gates["sales_wape"])
    orders_sc = score_component(o_wape, gates["orders_wape"])
    labor_sc = score_component(l_wmae, gates["labor_wmae"])
    bias_sc = score_component(b, gates["abs_bias"])
    int_sc = interval_score(ic)

    bucket_sc = (
        COMPONENT_WEIGHTS["sales"] * sales_sc
        + COMPONENT_WEIGHTS["orders"] * orders_sc
        + COMPONENT_WEIGHTS["labor"] * labor_sc
        + COMPONENT_WEIGHTS["bias"] * bias_sc
        + COMPONENT_WEIGHTS["interval"] * int_sc
    )

    return HorizonScore(
        bucket=bucket,
        sales_wape=round(s_wape, 4),
        orders_wape=round(o_wape, 4),
        labor_wmae=round(l_wmae, 2),
        bias=round(bias(data.sales_preds, data.sales_actuals), 4),
        interval_coverage=round(ic, 4),
        channel_mix_error=round(ch_err, 4),
        daypart_mix_error=round(dp_err, 4),
        score_0_to_100=round(bucket_sc, 1),
    )


def overall_model_score(bucket_scores: dict[HorizonBucket, HorizonScore]) -> float:
    """Roll up bucket scores to overall.

    overall = 0.50 * d1_7 + 0.30 * d8_14 + 0.20 * d15_28
    """
    total = 0.0
    for bucket, weight in BUCKET_WEIGHTS.items():
        if bucket in bucket_scores:
            total += weight * bucket_scores[bucket].score_0_to_100
    return round(total, 1)


# ── Champion/challenger promotion ──────────────────────────────────────────


def should_promote(
    challenger_scores: dict[HorizonBucket, HorizonScore],
    champion_scores: dict[HorizonBucket, HorizonScore],
    challenger_overall: float,
    champion_overall: float,
) -> tuple[bool, list[str]]:
    """Determine if a challenger model should replace the champion.

    Promotion rules:
    1. Overall model score higher by >= 5 points
    2. Sales WAPE better in at least 2 of 3 horizon buckets
    3. Labor error not worse
    4. Bias stays within launch gate
    5. (Explanation fidelity — checked separately, not here)
    """
    reasons: list[str] = []

    # Rule 1: Overall score improvement
    if challenger_overall - champion_overall < 5.0:
        reasons.append(
            f"overall score gap {challenger_overall - champion_overall:.1f} < 5.0 required"
        )

    # Rule 2: Sales WAPE better in >= 2 of 3 buckets
    buckets_better = 0
    for bucket in HorizonBucket:
        if bucket in challenger_scores and bucket in champion_scores:
            if challenger_scores[bucket].sales_wape < champion_scores[bucket].sales_wape:
                buckets_better += 1
    if buckets_better < 2:
        reasons.append(f"sales WAPE better in only {buckets_better}/3 buckets (need >= 2)")

    # Rule 3: Labor error not worse in any bucket
    for bucket in HorizonBucket:
        if bucket in challenger_scores and bucket in champion_scores:
            if challenger_scores[bucket].labor_wmae > champion_scores[bucket].labor_wmae * 1.05:
                reasons.append(
                    f"labor error worse in {bucket.value}: "
                    f"{challenger_scores[bucket].labor_wmae:.2f} vs {champion_scores[bucket].labor_wmae:.2f}"
                )
                break

    # Rule 4: Bias within launch gate
    for bucket in HorizonBucket:
        if bucket in challenger_scores:
            gate = LAUNCH_GATES[bucket]["abs_bias"]
            if abs(challenger_scores[bucket].bias) > gate:
                reasons.append(
                    f"bias {challenger_scores[bucket].bias:.4f} exceeds gate {gate} in {bucket.value}"
                )
                break

    promoted = len(reasons) == 0
    return promoted, reasons
