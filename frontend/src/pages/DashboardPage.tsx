import { useCallback } from 'react';
import {
  DollarSign,
  TrendingUp,
  Users,
  AlertTriangle,
  Zap,
  UserCheck,
  UtensilsCrossed,
  ShieldAlert,
  MapPin,
  BarChart3,
  Bell,
  Paperclip,
} from 'lucide-react';
import { useStore } from '../hooks/useStore';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import * as api from '../lib/api';
import { Card } from '../components/shared/Card';
import { Metric } from '../components/shared/Metric';
import { StatusBadge } from '../components/shared/StatusBadge';
import { EmptyState } from '../components/shared/EmptyState';
import { BacklogGauge } from '../components/dashboard/BacklogGauge';
import { LaborGauge } from '../components/dashboard/LaborGauge';
import { MenuChart } from '../components/dashboard/MenuChart';

/* -- Formatters -- */
const fmt = (n: number) =>
  n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;
const fmtTime = (s: number) => `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;

function pressureBadge(pressure: string) {
  const p = pressure.toLowerCase();
  if (p === 'low' || p === 'normal') return <StatusBadge variant="green">{pressure}</StatusBadge>;
  if (p === 'moderate' || p === 'medium') return <StatusBadge variant="yellow">{pressure}</StatusBadge>;
  return <StatusBadge variant="red">{pressure}</StatusBadge>;
}

function marginBadge(band: string | null) {
  if (!band) return null;
  const b = band.toLowerCase();
  if (b === 'high' || b === 'good') return <StatusBadge variant="green">{band}</StatusBadge>;
  if (b === 'medium' || b === 'moderate') return <StatusBadge variant="yellow">{band}</StatusBadge>;
  if (b === 'low' || b === 'poor') return <StatusBadge variant="red">{band}</StatusBadge>;
  return <StatusBadge variant="gray">{band}</StatusBadge>;
}

function severityVariant(severity: string): 'green' | 'yellow' | 'red' | 'blue' | 'gray' {
  const s = severity.toLowerCase();
  if (s === 'critical' || s === 'high') return 'red';
  if (s === 'medium' || s === 'warning') return 'yellow';
  if (s === 'low' || s === 'info') return 'blue';
  return 'gray';
}

export function DashboardPage() {
  const store = useStore();

  /* Auto-refresh every 60 seconds */
  const refreshDashboard = useCallback(() => {
    if (store.activeLocationId) {
      api
        .getDashboard(store.activeLocationId)
        .then(store.setDashboard)
        .catch(() => {});
    }
  }, [store.activeLocationId]);

  useAutoRefresh(refreshDashboard, 60000, !!store.activeLocationId);

  /* No location selected */
  if (!store.activeLocationId) {
    return (
      <EmptyState
        icon={<MapPin className="w-12 h-12" />}
        title="Select a location"
        description="Choose a location from the header to view its dashboard."
      />
    );
  }

  /* No dashboard snapshot yet */
  if (!store.dashboard) {
    return (
      <EmptyState
        icon={<BarChart3 className="w-12 h-12" />}
        title="No snapshot yet"
        description="Click Recompute to generate the first dashboard snapshot for this location."
      />
    );
  }

  const d = store.dashboard;

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Snapshot time + overall status */}
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Snapshot at {new Date(d.snapshot_at).toLocaleTimeString()}
          </p>
        </div>
        <StatusBadge
          variant={d.status === 'green' ? 'green' : d.status === 'yellow' ? 'yellow' : 'red'}
          size="md"
        >
          {d.status.charAt(0).toUpperCase() + d.status.slice(1)}
        </StatusBadge>
      </div>

      {/* -- Row 1: Summary strip -- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card title="Revenue Today" icon={<DollarSign className="w-4 h-4" />}>
          <Metric label="Earned" value={`$${fmt(d.summary.revenue_today)}`} variant="success" />
        </Card>
        <Card title="Projected EOD" icon={<TrendingUp className="w-4 h-4" />}>
          <Metric label="Forecast" value={`$${fmt(d.summary.projected_eod_revenue)}`} />
        </Card>
        <Card title="Active Staff" icon={<Users className="w-4 h-4" />}>
          <Metric label="On shift" value={d.summary.active_staff} />
          <div className="mt-2">{pressureBadge(d.summary.staffing_pressure)}</div>
        </Card>
        <Card
          title="Estimated Loss"
          icon={<AlertTriangle className="w-4 h-4" />}
          status={d.summary.estimated_loss > 0 ? 'red' : null}
        >
          <Metric
            label="Today"
            value={`$${fmt(d.summary.estimated_loss)}`}
            variant={d.summary.estimated_loss > 0 ? 'danger' : 'default'}
          />
        </Card>
      </div>

      {/* -- Row 2: Throughput + Staffing -- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Throughput */}
        <Card title="Throughput" icon={<Zap className="w-4 h-4" />}>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <Metric label="Orders / Hour" value={d.throughput.orders_per_hour} />
            <Metric label="Avg Ticket" value={`$${fmt(d.throughput.avg_ticket)}`} />
            <Metric label="Avg Prep Time" value={fmtTime(d.throughput.avg_prep_time_seconds)} />
          </div>
          {/* Backlog Risk Gauge */}
          <div className="flex items-center justify-center pt-3 border-t border-gray-100">
            <BacklogGauge value={d.throughput.backlog_risk} />
          </div>
        </Card>

        {/* Staffing */}
        <Card title="Staffing" icon={<UserCheck className="w-4 h-4" />}>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <Metric label="Active Shifts" value={d.staffing.active_shifts} />
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500 mb-1">
                Pressure
              </p>
              {pressureBadge(d.staffing.staffing_pressure)}
            </div>
            <Metric
              label="Sales / Labor Hr"
              value={`$${fmt(d.staffing.sales_per_labor_hour)}`}
            />
            <Metric
              label="Labor Cost Est."
              value={`$${fmt(d.staffing.labor_cost_estimate)}`}
            />
          </div>
          {/* Labor Cost Ratio Gauge */}
          <div className="flex items-center justify-center pt-3 border-t border-gray-100">
            <LaborGauge value={d.staffing.labor_cost_ratio} />
          </div>
          {d.staffing.discrepancy_warning && (
            <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {d.staffing.discrepancy_warning}
            </p>
          )}
        </Card>
      </div>

      {/* -- Row 3: Menu Performance + Leakage -- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Menu Performance */}
        <Card title="Menu Performance" icon={<UtensilsCrossed className="w-4 h-4" />}>
          {/* Top Sellers Chart */}
          {d.menu.top_sellers.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Top Sellers
              </p>
              <MenuChart items={d.menu.top_sellers} />
              {/* Table detail below chart */}
              <div className="overflow-x-auto mt-3">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 uppercase tracking-wide">
                      <th className="pb-2 font-medium">Item</th>
                      <th className="pb-2 font-medium text-right">Units</th>
                      <th className="pb-2 font-medium text-right">Revenue</th>
                      <th className="pb-2 font-medium text-right">Margin</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {d.menu.top_sellers.map((item) => (
                      <tr key={item.item_name}>
                        <td className="py-1.5 text-gray-900 font-medium truncate max-w-[140px]">
                          {item.item_name}
                        </td>
                        <td className="py-1.5 text-right text-gray-600">{item.units_sold}</td>
                        <td className="py-1.5 text-right text-gray-600">${fmt(item.revenue)}</td>
                        <td className="py-1.5 text-right">{marginBadge(item.margin_band)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Workhorse Items */}
          {d.menu.workhorse_items.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Workhorse Items
              </p>
              <div className="flex flex-wrap gap-1.5">
                {d.menu.workhorse_items.map((item) => (
                  <StatusBadge key={item.item_name} variant="yellow" size="sm">
                    {item.item_name} ({item.units_sold})
                  </StatusBadge>
                ))}
              </div>
            </div>
          )}

          {/* Attach Suggestions */}
          {d.menu.attach_rate_suggestions.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                <Paperclip className="w-3 h-3 inline mr-1" />
                Attach Suggestions
              </p>
              <ul className="space-y-1.5">
                {d.menu.attach_rate_suggestions.map((s, i) => (
                  <li key={i} className="text-xs text-gray-600 bg-gray-50 rounded-lg px-3 py-2">
                    <span className="font-medium text-gray-900">{s.anchor_item}</span>
                    {' + '}
                    <span className="font-medium text-blue-600">{s.suggested_item}</span>
                    {s.message && <span className="text-gray-500 ml-1">&mdash; {s.message}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {d.menu.top_sellers.length === 0 && d.menu.workhorse_items.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-4">No menu data available</p>
          )}
        </Card>

        {/* Leakage */}
        <Card
          title="Leakage"
          icon={<AlertTriangle className="w-4 h-4" />}
          status={d.leakage.spike_detected ? 'red' : null}
        >
          <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-4">
            <Metric
              label="Refunds"
              value={`$${fmt(d.leakage.refund_total)}`}
              variant={d.leakage.refund_total > 0 ? 'danger' : 'default'}
            />
            <Metric
              label="Comps"
              value={`$${fmt(d.leakage.comp_total)}`}
              variant={d.leakage.comp_total > 0 ? 'warning' : 'default'}
            />
            <Metric
              label="Voids"
              value={`$${fmt(d.leakage.void_total)}`}
              variant={d.leakage.void_total > 0 ? 'warning' : 'default'}
            />
          </div>
          <div className="flex items-center gap-3 pt-3 border-t border-gray-100 mb-3">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Refund Rate
            </span>
            <span
              className={`text-sm font-bold ${
                d.leakage.refund_rate < 0.03
                  ? 'text-emerald-600'
                  : d.leakage.refund_rate < 0.06
                    ? 'text-amber-600'
                    : 'text-red-600'
              }`}
            >
              {fmtPct(d.leakage.refund_rate)}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {d.leakage.spike_detected && (
              <StatusBadge variant="red" size="md">
                Spike Detected
              </StatusBadge>
            )}
            {d.leakage.suspicious_employee && (
              <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
                <ShieldAlert className="w-3 h-3" />
                Suspicious: {d.leakage.suspicious_employee}
              </span>
            )}
          </div>
        </Card>
      </div>

      {/* -- Row 4: Alerts & Recommendations -- */}
      <Card title="Alerts & Recommendations" icon={<Bell className="w-4 h-4" />}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {/* Alerts */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
              Active Alerts ({d.alerts.length})
            </p>
            {d.alerts.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">No active alerts</p>
            ) : (
              <ul className="space-y-2">
                {d.alerts.map((a) => (
                  <li
                    key={a.id}
                    className="flex items-start gap-2 bg-gray-50 rounded-lg px-3 py-2"
                  >
                    <StatusBadge variant={severityVariant(a.severity)}>
                      {a.severity}
                    </StatusBadge>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">{a.title}</p>
                      {a.triggered_at && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          {new Date(a.triggered_at).toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Recommendations */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
              Pending Recommendations ({d.recommendations.length})
            </p>
            {d.recommendations.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">No pending recommendations</p>
            ) : (
              <ul className="space-y-2">
                {d.recommendations.map((r) => (
                  <li
                    key={r.id}
                    className="flex items-start gap-2 bg-gray-50 rounded-lg px-3 py-2"
                  >
                    <StatusBadge variant="blue">{r.category}</StatusBadge>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">{r.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {(r.confidence * 100).toFixed(0)}% confidence
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </Card>

      {/* -- Row 5: Integrity (conditional) -- */}
      {d.integrity.flags.length > 0 && (
        <Card
          title="Integrity"
          icon={<ShieldAlert className="w-4 h-4" />}
          status={d.integrity.highest_risk_score > 0.7 ? 'red' : d.integrity.highest_risk_score > 0.4 ? 'yellow' : null}
        >
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <Metric label="Open Flags" value={d.integrity.flags_open} variant="danger" />
            <Metric
              label="Highest Risk"
              value={fmtPct(d.integrity.highest_risk_score)}
              variant={
                d.integrity.highest_risk_score > 0.7
                  ? 'danger'
                  : d.integrity.highest_risk_score > 0.4
                    ? 'warning'
                    : 'default'
              }
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 uppercase tracking-wide">
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Severity</th>
                  <th className="pb-2 font-medium">Confidence</th>
                  <th className="pb-2 font-medium">Title</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {d.integrity.flags.map((f) => (
                  <tr key={f.id}>
                    <td className="py-2 text-gray-600">{f.flag_type}</td>
                    <td className="py-2">
                      <StatusBadge variant={severityVariant(f.severity)}>{f.severity}</StatusBadge>
                    </td>
                    <td className="py-2 text-gray-600">{fmtPct(f.confidence)}</td>
                    <td className="py-2 text-gray-900 font-medium truncate max-w-[200px]">
                      {f.title}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
