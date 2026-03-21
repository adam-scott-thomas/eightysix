export interface Location {
  id: string;
  name: string;
  timezone: string;
  business_hours_json: Record<string, { open: string; close: string }> | null;
  default_hourly_rate: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardSnapshot {
  snapshot_at: string;
  status: 'green' | 'yellow' | 'red';
  readiness: {
    score: number;
    completeness: number;
    missing: string[];
  };
  summary: {
    revenue_today: number;
    projected_eod_revenue: number;
    active_staff: number;
    staffing_pressure: string;
    estimated_loss: number;
  };
  throughput: {
    orders_per_hour: number;
    avg_ticket: number;
    avg_prep_time_seconds: number;
    backlog_risk: number;
  };
  staffing: {
    active_shifts: number;
    staffing_pressure: string;
    sales_per_labor_hour: number;
    labor_cost_ratio: number;
    labor_cost_estimate: number;
    discrepancy_warning: string | null;
  };
  menu: {
    top_sellers: MenuPerformanceItem[];
    bottom_sellers: MenuPerformanceItem[];
    workhorse_items: MenuPerformanceItem[];
    attach_rate_suggestions: AttachSuggestion[];
  };
  leakage: {
    refund_total: number;
    comp_total: number;
    void_total: number;
    refund_rate: number;
    spike_detected: boolean;
    suspicious_employee: string | null;
  };
  integrity: {
    flags_open: number;
    highest_risk_score: number;
    flags: IntegrityFlagSummary[];
  };
  alerts: AlertSummary[];
  recommendations: RecommendationSummary[];
}

export interface MenuPerformanceItem {
  item_name: string;
  units_sold: number;
  revenue: number;
  margin_band: string | null;
}

export interface AttachSuggestion {
  anchor_item: string;
  suggested_item: string;
  message: string;
}

export interface AlertSummary {
  id: string;
  alert_type: string;
  severity: string;
  status: string;
  title: string;
  message: string | null;
  triggered_at: string | null;
}

export interface Alert extends AlertSummary {
  location_id: string;
  evidence_json: Record<string, unknown> | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  ttl_minutes: number | null;
}

export interface RecommendationSummary {
  id: string;
  category: string;
  title: string;
  reason: string;
  action_description: string | null;
  confidence: number;
  estimated_impact: Record<string, unknown> | null;
}

export interface Recommendation extends RecommendationSummary {
  location_id: string;
  alert_id: string | null;
  status: string;
  expires_at: string | null;
  created_at: string;
  applied_at: string | null;
  dismissed_at: string | null;
}

export interface IntegrityFlagSummary {
  id: string;
  flag_type: string;
  severity: string;
  confidence: number;
  title: string;
  fraud_risk_score: number | null;
}

export interface IntegrityFlag extends IntegrityFlagSummary {
  location_id: string;
  employee_id: string | null;
  shift_id: string | null;
  status: string;
  message: string | null;
  evidence_json: Record<string, unknown>;
  created_at: string;
  resolved_at: string | null;
}

export interface Readiness {
  status: 'ready' | 'partial' | 'insufficient';
  completeness_score: number;
  missing_domains: string[];
  available_quick_wins: string[];
}

export interface IngestionSummary {
  created: number;
  updated: number;
  skipped: number;
}

export type AppMode = 'demo' | 'live';
