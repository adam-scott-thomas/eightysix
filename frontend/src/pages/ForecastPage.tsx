import { useState, useCallback } from 'react';
import {
  Calendar,
  TrendingUp,
  Users,
  AlertTriangle,
  ShoppingCart,
  Loader2,
  RefreshCw,
  MapPin,
  Zap,
} from 'lucide-react';
import { useStore } from '../hooks/useStore';
import * as api from '../lib/api';
import { Card } from '../components/shared/Card';
import { StatusBadge } from '../components/shared/StatusBadge';
import { EmptyState } from '../components/shared/EmptyState';

interface ForecastDay {
  target_date: string;
  horizon_days: number;
  expected_sales: number;
  expected_orders: number;
  sales_low: number;
  sales_high: number;
  confidence_level: number;
  orders_by_channel: Record<string, number>;
  daypart: Record<string, { sales: number; orders: number }>;
  labor_hours: Record<string, number>;
  top_skus: { item_name: string; expected_units: number; category: string }[];
  risk_flags: { flag: string; message: string; severity: string }[];
  explanation: string;
  purchasing: { item: string; adjustment_pct: number; reason: string }[];
}

const fmt = (n: number) =>
  n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
const fmtD = (n: number) =>
  n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtPct = (n: number) => `${(n * 100).toFixed(0)}%`;

const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDate(iso: string) {
  const d = new Date(iso + 'T12:00:00');
  return `${DOW[d.getDay()]} ${MONTH[d.getMonth()]} ${d.getDate()}`;
}

function severityColor(sev: string) {
  if (sev === 'warning') return 'text-amber-600 bg-amber-50 border-amber-200';
  if (sev === 'info') return 'text-blue-600 bg-blue-50 border-blue-200';
  return 'text-red-600 bg-red-50 border-red-200';
}

export function ForecastPage() {
  const store = useStore();
  const [forecasts, setForecasts] = useState<ForecastDay[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<ForecastDay | null>(null);
  const [view, setView] = useState<'week1' | 'week2' | 'week3_4'>('week1');

  const locId = store.activeLocationId;

  const handleGenerate = useCallback(async () => {
    if (!locId) return;
    setLoading(true);
    setError(null);
    try {
      // Backfill aggregates first, then generate
      await api.backfillAggregates(locId, 56);
      const res = await api.generateForecast(locId, 28);
      setForecasts(res.forecasts || []);
      if (res.forecasts?.length > 0) {
        setSelectedDay(res.forecasts[0]);
      }
    } catch (e: any) {
      setError(e.message || 'Forecast generation failed');
    } finally {
      setLoading(false);
    }
  }, [locId]);

  const handleLoad = useCallback(async () => {
    if (!locId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getForecast(locId);
      setForecasts(res.forecasts || []);
      if (res.forecasts?.length > 0) {
        setSelectedDay(res.forecasts[0]);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [locId]);

  if (!locId) {
    return (
      <EmptyState
        icon={<MapPin className="w-12 h-12" />}
        title="Select a location"
        description="Choose a location from the header to view forecasts."
      />
    );
  }

  // Split forecasts into time horizons
  const week1 = forecasts.filter((f) => f.horizon_days <= 7);
  const week2 = forecasts.filter((f) => f.horizon_days > 7 && f.horizon_days <= 14);
  const week3_4 = forecasts.filter((f) => f.horizon_days > 14);

  const visibleDays = view === 'week1' ? week1 : view === 'week2' ? week2 : week3_4;

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Forecast</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {forecasts.length > 0
              ? `${forecasts.length}-day forecast • baseline_v1`
              : 'Generate a forecast to see predictions'}
          </p>
        </div>
        <div className="flex gap-2">
          {forecasts.length === 0 && (
            <button
              onClick={handleLoad}
              disabled={loading}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 cursor-pointer"
            >
              Load Latest
            </button>
          )}
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {loading ? 'Generating...' : 'Generate Forecast'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {forecasts.length === 0 && !loading && (
        <EmptyState
          icon={<Calendar className="w-12 h-12" />}
          title="No forecast yet"
          description="Click 'Generate Forecast' to create a 28-day forecast. It will backfill historical aggregates and run the baseline model."
        />
      )}

      {forecasts.length > 0 && (
        <>
          {/* Horizon tabs */}
          <div className="flex bg-gray-100 rounded-lg p-1 w-fit">
            {[
              { id: 'week1' as const, label: 'Week 1', count: week1.length },
              { id: 'week2' as const, label: 'Week 2', count: week2.length },
              { id: 'week3_4' as const, label: 'Weeks 3-4', count: week3_4.length },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => { setView(tab.id); setSelectedDay(null); }}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
                  view === tab.id
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>

          {/* Forecast strip — one card per day */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {visibleDays.map((day) => {
              const isSelected = selectedDay?.target_date === day.target_date;
              const hasRisk = day.risk_flags.length > 0;
              return (
                <button
                  key={day.target_date}
                  onClick={() => setSelectedDay(day)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500'
                      : hasRisk
                        ? 'border-amber-200 bg-amber-50/50 hover:border-amber-300'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <p className="text-xs font-medium text-gray-500">{formatDate(day.target_date)}</p>
                  <p className="text-lg font-bold text-gray-900 mt-1">${fmt(day.expected_sales)}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    ${fmt(day.sales_low)} – ${fmt(day.sales_high)}
                  </p>
                  <div className="flex items-center gap-1 mt-2">
                    <ShoppingCart className="w-3 h-3 text-gray-400" />
                    <span className="text-xs text-gray-600">{day.expected_orders} orders</span>
                  </div>
                  {hasRisk && (
                    <div className="mt-2">
                      <StatusBadge variant={day.risk_flags[0].severity === 'warning' ? 'yellow' : 'blue'} size="sm">
                        {day.risk_flags[0].flag.replace(/_/g, ' ')}
                      </StatusBadge>
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Detail panel for selected day */}
          {selectedDay && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Left: Sales + explanation */}
              <div className="space-y-4">
                <Card title={formatDate(selectedDay.target_date)} icon={<Calendar className="w-4 h-4" />}>
                  {/* Sales range */}
                  <div className="mb-4">
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-gray-900">${fmtD(selectedDay.expected_sales)}</span>
                      <span className="text-sm text-gray-400">expected</span>
                    </div>
                    {/* Confidence band bar */}
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>${fmt(selectedDay.sales_low)}</span>
                        <span>{fmtPct(selectedDay.confidence_level)} confidence</span>
                        <span>${fmt(selectedDay.sales_high)}</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-300 via-blue-500 to-blue-300 rounded-full"
                          style={{
                            marginLeft: `${((selectedDay.sales_low / selectedDay.sales_high) * 100) * 0.4}%`,
                            width: `${100 - ((selectedDay.sales_low / selectedDay.sales_high) * 100) * 0.4}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Explanation */}
                  {selectedDay.explanation && (
                    <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-800 border border-blue-100">
                      <Zap className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
                      {selectedDay.explanation}
                    </div>
                  )}

                  {/* Orders by channel */}
                  {Object.keys(selectedDay.orders_by_channel).length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Orders by Channel
                      </p>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(selectedDay.orders_by_channel).map(([ch, count]) => (
                          <div key={ch} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                            <span className="text-sm text-gray-600 capitalize">{ch.replace(/_/g, ' ')}</span>
                            <span className="text-sm font-semibold text-gray-900">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Daypart breakdown */}
                  {Object.keys(selectedDay.daypart).length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Daypart Forecast
                      </p>
                      <div className="space-y-1.5">
                        {Object.entries(selectedDay.daypart).map(([dp, vals]) => (
                          <div key={dp} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                            <span className="text-sm text-gray-600 capitalize">{dp}</span>
                            <div className="text-right">
                              <span className="text-sm font-semibold text-gray-900">${fmt(vals.sales)}</span>
                              <span className="text-xs text-gray-400 ml-2">{vals.orders} orders</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>

                {/* Risk flags */}
                {selectedDay.risk_flags.length > 0 && (
                  <Card title="Risk Flags" icon={<AlertTriangle className="w-4 h-4" />}>
                    <div className="space-y-2">
                      {selectedDay.risk_flags.map((flag, i) => (
                        <div
                          key={i}
                          className={`p-3 rounded-lg border text-sm ${severityColor(flag.severity)}`}
                        >
                          <span className="font-medium capitalize">{flag.flag.replace(/_/g, ' ')}:</span>{' '}
                          {flag.message}
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </div>

              {/* Right: Labor + Purchasing + Top SKUs */}
              <div className="space-y-4">
                {/* Labor recommendation */}
                {Object.keys(selectedDay.labor_hours).length > 0 && (
                  <Card title="Recommended Labor Hours" icon={<Users className="w-4 h-4" />}>
                    <div className="space-y-2">
                      {Object.entries(selectedDay.labor_hours)
                        .filter(([role]) => role !== 'total')
                        .map(([role, hours]) => (
                          <div key={role} className="flex items-center gap-3">
                            <span className="text-sm text-gray-600 capitalize w-20">{role}</span>
                            <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                              <div
                                className="h-full bg-blue-500 rounded-full"
                                style={{
                                  width: `${Math.min((hours / (selectedDay.labor_hours.total || 1)) * 100, 100)}%`,
                                }}
                              />
                            </div>
                            <span className="text-sm font-semibold text-gray-900 w-12 text-right">{hours}h</span>
                          </div>
                        ))}
                      <div className="pt-2 border-t border-gray-100 flex justify-between">
                        <span className="text-sm font-medium text-gray-700">Total</span>
                        <span className="text-sm font-bold text-gray-900">{selectedDay.labor_hours.total}h</span>
                      </div>
                    </div>
                  </Card>
                )}

                {/* Purchasing signals */}
                {selectedDay.purchasing.length > 0 && (
                  <Card title="Purchasing Signals" icon={<TrendingUp className="w-4 h-4" />}>
                    <div className="space-y-1.5">
                      {selectedDay.purchasing.map((p, i) => (
                        <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                          <span className="text-sm text-gray-700 font-medium">{p.item}</span>
                          <div className="flex items-center gap-2">
                            <StatusBadge
                              variant={p.adjustment_pct > 0 ? 'yellow' : 'green'}
                              size="sm"
                            >
                              {p.adjustment_pct > 0 ? '+' : ''}{p.adjustment_pct}%
                            </StatusBadge>
                            <span className="text-xs text-gray-400">{p.reason}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Top SKU demand */}
                {selectedDay.top_skus.length > 0 && (
                  <Card title="Top Item Demand" icon={<ShoppingCart className="w-4 h-4" />}>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-xs text-gray-400 uppercase tracking-wide">
                            <th className="pb-2 font-medium">Item</th>
                            <th className="pb-2 font-medium text-right">Expected</th>
                            <th className="pb-2 font-medium text-right">Category</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {selectedDay.top_skus.slice(0, 15).map((sku) => (
                            <tr key={sku.item_name}>
                              <td className="py-1.5 text-gray-900 font-medium truncate max-w-[160px]">
                                {sku.item_name}
                              </td>
                              <td className="py-1.5 text-right text-gray-600">{sku.expected_units} units</td>
                              <td className="py-1.5 text-right">
                                <span className="text-xs text-gray-400">{sku.category}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
