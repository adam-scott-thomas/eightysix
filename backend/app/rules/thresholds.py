"""All configurable thresholds in one place. Override per location via config."""
from dataclasses import dataclass, field


@dataclass
class StaffingThresholds:
    critical_understaffed_oplh: float = 15.0  # orders_per_labor_hour >
    understaffed_oplh: float = 10.0
    balanced_upper_oplh: float = 10.0
    balanced_lower_oplh: float = 4.0
    overstaffed_oplh: float = 4.0
    critical_overstaffed_oplh: float = 2.0


@dataclass
class LaborThresholds:
    healthy_ratio: float = 0.30
    warning_ratio: float = 0.35
    # > warning_ratio = critical


@dataclass
class LeakageThresholds:
    normal_refund_rate: float = 0.03
    spike_refund_rate: float = 0.06
    # > spike = critical
    suspicious_employee_concentration: float = 0.40  # 40% of refunds


@dataclass
class RushThresholds:
    backlog_risk_critical: float = 0.8
    backlog_risk_warning: float = 0.6
    prep_time_rise_alert_pct: float = 0.20  # 20% increase


@dataclass
class IntegrityThresholds:
    review_score: float = 0.5
    high_confidence_score: float = 0.8
    geofence_weight: float = 0.5
    device_mismatch_weight: float = 0.3
    staff_discrepancy_weight: float = 0.2


@dataclass
class Thresholds:
    staffing: StaffingThresholds = field(default_factory=StaffingThresholds)
    labor: LaborThresholds = field(default_factory=LaborThresholds)
    leakage: LeakageThresholds = field(default_factory=LeakageThresholds)
    rush: RushThresholds = field(default_factory=RushThresholds)
    integrity: IntegrityThresholds = field(default_factory=IntegrityThresholds)


# Global default — can be overridden per location later
DEFAULT_THRESHOLDS = Thresholds()


def merge_thresholds(overrides: dict | None) -> Thresholds:
    """Merge per-location threshold overrides with defaults.

    overrides format: {"staffing": {"critical_understaffed_oplh": 20}, "labor": {"warning_ratio": 0.32}}
    """
    if not overrides:
        return DEFAULT_THRESHOLDS

    from dataclasses import asdict
    t = Thresholds()

    for section_name in ("staffing", "labor", "leakage", "rush", "integrity"):
        section_overrides = overrides.get(section_name, {})
        if section_overrides:
            section = getattr(t, section_name)
            for key, value in section_overrides.items():
                if hasattr(section, key):
                    setattr(section, key, value)

    return t
