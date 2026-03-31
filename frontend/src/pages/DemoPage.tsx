import { useState } from 'react';
import {
  Play,
  RotateCcw,
  RefreshCw,
  CheckCircle,
  Loader2,
  AlertTriangle,
  MapPin,
  Activity,
  Trash2,
  Zap,
  Users,
  ShoppingCart,
  DollarSign,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { useStore } from '../hooks/useStore';
import * as api from '../lib/api';

/* ------------------------------------------------------------------ */
/*  Scenario definitions                                               */
/* ------------------------------------------------------------------ */

interface ScenarioDef {
  key: string;
  label: string;
  description: string;
  color: string;
}

const SCENARIOS: ScenarioDef[] = [
  {
    key: 'normal_day',
    label: 'Normal Day',
    description: 'Baseline. No alerts fire. Dashboard shows green.',
    color: 'border-l-emerald-500',
  },
  {
    key: 'dinner_rush',
    label: 'Dinner Rush',
    description: 'Order volume spikes 6-8 PM. Prep times rise. Rush alert triggers.',
    color: 'border-l-amber-500',
  },
  {
    key: 'refund_spike',
    label: 'Refund Spike',
    description: '3x normal refund rate. One employee flagged for 60% of refunds.',
    color: 'border-l-red-500',
  },
  {
    key: 'suspicious_punch',
    label: 'Suspicious Punch',
    description: 'Clock-in outside geofence. Device mismatch. Integrity flags.',
    color: 'border-l-red-500',
  },
  {
    key: 'understaffed',
    label: 'Understaffed',
    description: '2 staff for volume that needs 5. Critical understaffed alert.',
    color: 'border-l-amber-500',
  },
  {
    key: 'overstaffed',
    label: 'Overstaffed',
    description: '8 staff for volume that needs 3. Labor cost critical.',
    color: 'border-l-amber-500',
  },
  {
    key: 'ghost_shift',
    label: 'Ghost Shift',
    description: 'Employee clocked in with zero orders, no manager confirmation.',
    color: 'border-l-red-500',
  },
  {
    key: 'low_margin_mix',
    label: 'Low Margin Mix',
    description: 'High volume but concentrated in low-margin items.',
    color: 'border-l-blue-500',
  },
];

/* ------------------------------------------------------------------ */
/*  Utility                                                            */
/* ------------------------------------------------------------------ */

function formatLabel(key: string): string {
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

type CardStatus = 'idle' | 'loading' | 'success' | 'error';

interface CardState {
  status: CardStatus;
  message?: string;
}

export function DemoPage() {
  const store = useStore();

  const [cardStates, setCardStates] = useState<Record<string, CardState>>({});
  const [resetConfirm, setResetConfirm] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [recomputeLoading, setRecomputeLoading] = useState(false);
  const [lastResult, setLastResult] = useState<{
    scenario: string;
    created: number;
    updated: number;
    skipped: number;
  } | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  /* ---------- quick assessment state ---------- */
  const [qaName, setQaName] = useState('');
  const [qaStaff, setQaStaff] = useState('');
  const [qaOrders, setQaOrders] = useState('');
  const [qaTicket, setQaTicket] = useState('');
  const [qaLoading, setQaLoading] = useState(false);
  const [qaResult, setQaResult] = useState<any>(null);
  const [qaError, setQaError] = useState<string | null>(null);

  /* ---------- helpers ---------- */

  function setCard(key: string, state: CardState) {
    setCardStates((prev) => ({ ...prev, [key]: state }));
  }

  const activeLocation = store.locations.find(
    (l) => l.id === store.activeLocationId,
  );

  /* ---------- quick assessment ---------- */

  const qaValid =
    parseInt(qaStaff) > 0 && parseInt(qaOrders) > 0 && parseFloat(qaTicket) > 0;

  async function runQuickAssess() {
    if (!qaValid) return;
    setQaLoading(true);
    setQaError(null);
    setQaResult(null);
    setStatusMessage(null);

    try {
      const result = await api.quickAssess({
        staff_count: parseInt(qaStaff),
        orders_per_day: parseInt(qaOrders),
        avg_ticket: parseFloat(qaTicket),
        restaurant_name: qaName || undefined,
      });

      store.setActiveLocation(result.location_id);
      const locations = await api.getLocations();
      store.setLocations(locations);
      store.setDashboard(result.dashboard);
      setQaResult(result.dashboard);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Assessment failed';
      setQaError(msg);
    } finally {
      setQaLoading(false);
    }
  }

  /* ---------- scenario load ---------- */

  async function loadScenario(scenarioKey: string) {
    setCard(scenarioKey, { status: 'loading' });
    setStatusMessage(null);

    try {
      // 1. Reset existing data
      await api.demoReset();

      // 2. Load the scenario
      const loadResult = await api.demoLoadScenario(scenarioKey);
      const locationId: string =
        loadResult.location_id ?? loadResult.locationId ?? loadResult.id;

      // 3. Set active location in store
      store.setActiveLocation(locationId);

      // 4. Refresh locations list
      const locations = await api.getLocations();
      store.setLocations(locations);

      // 5. Recompute the dashboard
      await api.recompute(locationId);

      // 6. Fetch the updated dashboard
      const dashboard = await api.getDashboard(locationId);
      store.setDashboard(dashboard);

      // 7. Track ingestion summary
      const summary = loadResult.summary ?? loadResult.ingestion ?? loadResult;
      setLastResult({
        scenario: scenarioKey,
        created: summary.created ?? 0,
        updated: summary.updated ?? 0,
        skipped: summary.skipped ?? 0,
      });

      setCard(scenarioKey, { status: 'success', message: 'Loaded' });
      setStatusMessage(`"${formatLabel(scenarioKey)}" loaded successfully.`);

      // Clear success badge after 4s
      setTimeout(() => setCard(scenarioKey, { status: 'idle' }), 4000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load';
      setCard(scenarioKey, { status: 'error', message: msg });
      setStatusMessage(`Error: ${msg}`);
    }
  }

  /* ---------- reset ---------- */

  async function handleReset() {
    setResetLoading(true);
    setStatusMessage(null);
    try {
      await api.demoReset();
      store.setLocations([]);
      store.setActiveLocation(null);
      store.setDashboard(null);
      setLastResult(null);
      setStatusMessage('All data reset successfully.');
      setResetConfirm(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setStatusMessage(`Reset error: ${msg}`);
    } finally {
      setResetLoading(false);
    }
  }

  /* ---------- recompute ---------- */

  async function handleRecompute() {
    if (!store.activeLocationId) return;
    setRecomputeLoading(true);
    setStatusMessage(null);
    try {
      await api.recompute(store.activeLocationId);
      const dashboard = await api.getDashboard(store.activeLocationId);
      store.setDashboard(dashboard);
      setStatusMessage('Dashboard recomputed.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setStatusMessage(`Recompute error: ${msg}`);
    } finally {
      setRecomputeLoading(false);
    }
  }

  /* ---------- render ---------- */

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-lg sm:text-xl font-bold text-gray-900">Demo Controls</h1>
        <p className="text-sm text-gray-500 mt-1">
          Load pre-built scenarios to explore the dashboard in demo mode.
        </p>
      </div>

      {/* ============ SECTION 0: Quick Assessment ============ */}
      <section>
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-5 h-5 text-blue-600" />
            <h2 className="text-base font-bold text-gray-900">
              Walk-In Assessment
            </h2>
          </div>
          <p className="text-sm text-gray-500 mb-5">
            Ask 3 questions. Get instant operational insights.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 sm:gap-4">
            {/* Restaurant name */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Restaurant Name
              </label>
              <input
                type="text"
                value={qaName}
                onChange={(e) => setQaName(e.target.value)}
                placeholder="Optional"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              />
            </div>

            {/* Staff count */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                <Users className="w-3 h-3 inline mr-1" />
                Staff on shift
              </label>
              <input
                type="number"
                min="1"
                value={qaStaff}
                onChange={(e) => setQaStaff(e.target.value)}
                placeholder="e.g. 6"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              />
            </div>

            {/* Orders today */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                <ShoppingCart className="w-3 h-3 inline mr-1" />
                Avg daily orders
              </label>
              <input
                type="number"
                min="1"
                value={qaOrders}
                onChange={(e) => setQaOrders(e.target.value)}
                placeholder="e.g. 200"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              />
            </div>

            {/* Avg ticket */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                <DollarSign className="w-3 h-3 inline mr-1" />
                Average check
              </label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={qaTicket}
                onChange={(e) => setQaTicket(e.target.value)}
                placeholder="e.g. 18.50"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              />
            </div>
          </div>

          {/* Run button */}
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={runQuickAssess}
              disabled={!qaValid || qaLoading}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
            >
              {qaLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              {qaLoading ? 'Analyzing...' : 'Run Assessment'}
            </button>

            {qaError && (
              <span className="text-sm text-red-600 font-medium">
                {qaError}
              </span>
            )}
          </div>

          {/* Results */}
          {qaResult && (
            <div className="mt-5 pt-5 border-t border-blue-200">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-semibold text-gray-700">
                  Instant Snapshot
                </span>
                <span className="text-xs text-gray-400">
                  — click Dashboard in sidebar for full view
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {/* Status */}
                <div
                  className={`rounded-lg p-3 text-center ${
                    qaResult.status === 'green'
                      ? 'bg-emerald-50'
                      : qaResult.status === 'yellow'
                        ? 'bg-amber-50'
                        : qaResult.status === 'red'
                          ? 'bg-red-50'
                          : 'bg-gray-50'
                  }`}
                >
                  <div
                    className={`text-lg font-bold capitalize ${
                      qaResult.status === 'green'
                        ? 'text-emerald-700'
                        : qaResult.status === 'yellow'
                          ? 'text-amber-700'
                          : qaResult.status === 'red'
                            ? 'text-red-700'
                            : 'text-gray-600'
                    }`}
                  >
                    {qaResult.status}
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </div>
                </div>

                {/* Revenue */}
                <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                  <div className="text-lg font-bold text-gray-900">
                    $
                    {(qaResult.summary?.revenue_today ?? 0).toLocaleString(
                      undefined,
                      { maximumFractionDigits: 0 },
                    )}
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </div>
                </div>

                {/* Projected EOD */}
                <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                  <div className="text-lg font-bold text-gray-900">
                    $
                    {(
                      qaResult.summary?.projected_eod_revenue ?? 0
                    ).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Projected EOD
                  </div>
                </div>

                {/* Staffing */}
                <div
                  className={`rounded-lg p-3 text-center ${
                    qaResult.summary?.staffing_pressure === 'balanced'
                      ? 'bg-emerald-50'
                      : qaResult.summary?.staffing_pressure?.includes(
                            'critical',
                          )
                        ? 'bg-red-50'
                        : 'bg-amber-50'
                  }`}
                >
                  <div
                    className={`text-lg font-bold capitalize ${
                      qaResult.summary?.staffing_pressure === 'balanced'
                        ? 'text-emerald-700'
                        : qaResult.summary?.staffing_pressure?.includes(
                              'critical',
                            )
                          ? 'text-red-700'
                          : 'text-amber-700'
                    }`}
                  >
                    {(qaResult.summary?.staffing_pressure ?? 'n/a')
                      .replace(/_/g, ' ')}
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Staffing
                  </div>
                </div>

                {/* Labor Cost */}
                <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                  <div className="text-lg font-bold text-gray-900">
                    {((qaResult.staffing?.labor_cost_ratio ?? 0) * 100).toFixed(
                      1,
                    )}
                    %
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Labor Cost
                  </div>
                </div>

                {/* Orders / Hr */}
                <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                  <div className="text-lg font-bold text-gray-900">
                    {qaResult.throughput?.orders_per_hour ?? 0}
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Orders/Hr
                  </div>
                </div>
              </div>

              {/* Alerts summary */}
              {qaResult.alerts && qaResult.alerts.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {qaResult.alerts.map((a: any) => (
                    <span
                      key={a.id}
                      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
                        a.severity === 'critical'
                          ? 'bg-red-100 text-red-700'
                          : a.severity === 'warning'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      <AlertTriangle className="w-3 h-3" />
                      {a.title}
                    </span>
                  ))}
                </div>
              )}

              {/* Recommendations preview */}
              {qaResult.recommendations && qaResult.recommendations.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    Recommendations
                  </div>
                  <div className="space-y-1">
                    {qaResult.recommendations.slice(0, 3).map((r: any) => (
                      <div
                        key={r.id}
                        className="flex items-start gap-2 text-sm text-gray-700"
                      >
                        <ArrowRight className="w-3.5 h-3.5 mt-0.5 text-blue-500 shrink-0" />
                        <span>{r.title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* ============ SECTION 1: Scenario Loader ============ */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Scenario Loader
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          {SCENARIOS.map((s) => {
            const cs = cardStates[s.key] ?? { status: 'idle' as CardStatus };

            return (
              <div
                key={s.key}
                className={`
                  relative bg-white rounded-xl shadow-sm border border-gray-200
                  border-l-4 ${s.color}
                  flex flex-col justify-between p-4 sm:p-5
                  transition-shadow duration-200 hover:shadow-md
                `}
              >
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-900">
                    {s.label}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                    {s.description}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => loadScenario(s.key)}
                    disabled={cs.status === 'loading'}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
                  >
                    {cs.status === 'loading' ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                    {cs.status === 'loading' ? 'Loading...' : 'Load'}
                  </button>

                  {cs.status === 'success' && (
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-600 font-medium">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Loaded
                    </span>
                  )}

                  {cs.status === 'error' && (
                    <span
                      className="inline-flex items-center gap-1 text-xs text-red-600 font-medium truncate max-w-36"
                      title={cs.message}
                    >
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      {cs.message ?? 'Error'}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ============ SECTION 2: Quick Actions ============ */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Quick Actions
        </h2>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-5">
          <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4">
            {/* Reset All Data */}
            {!resetConfirm ? (
              <button
                onClick={() => setResetConfirm(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors duration-150 cursor-pointer"
              >
                <Trash2 className="w-4 h-4" />
                Reset All Data
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-red-600 font-medium">
                  Are you sure?
                </span>
                <button
                  onClick={handleReset}
                  disabled={resetLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors duration-150 cursor-pointer"
                >
                  {resetLoading && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  )}
                  Confirm Reset
                </button>
                <button
                  onClick={() => setResetConfirm(false)}
                  className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-150 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            )}

            {/* Recompute Dashboard */}
            <button
              onClick={handleRecompute}
              disabled={recomputeLoading || !store.activeLocationId}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
            >
              {recomputeLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Recompute Dashboard
            </button>
          </div>

          {/* Current status row */}
          <div className="mt-3 sm:mt-4 flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="font-medium text-gray-500">Location:</span>
              <span className="text-gray-900">
                {activeLocation?.name ?? 'None selected'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-400" />
              <span className="font-medium text-gray-500">Dashboard:</span>
              {store.dashboard ? (
                <span
                  className={`inline-flex items-center gap-1.5 capitalize font-medium ${
                    store.dashboard.status === 'green'
                      ? 'text-emerald-600'
                      : store.dashboard.status === 'yellow'
                        ? 'text-amber-600'
                        : store.dashboard.status === 'red'
                          ? 'text-red-600'
                          : 'text-gray-500'
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      store.dashboard.status === 'green'
                        ? 'bg-emerald-500'
                        : store.dashboard.status === 'yellow'
                          ? 'bg-amber-500'
                          : store.dashboard.status === 'red'
                            ? 'bg-red-500'
                            : 'bg-gray-400'
                    }`}
                  />
                  {store.dashboard.status}
                </span>
              ) : (
                <span className="text-gray-400">No data</span>
              )}
            </div>
          </div>

          {/* Status message toast */}
          {statusMessage && (
            <div
              className={`mt-3 text-sm font-medium px-3 py-2 rounded-lg ${
                statusMessage.startsWith('Error') || statusMessage.startsWith('Reset error')
                  ? 'bg-red-50 text-red-700'
                  : 'bg-emerald-50 text-emerald-700'
              }`}
            >
              {statusMessage}
            </div>
          )}
        </div>
      </section>

      {/* ============ SECTION 3: Pipeline Status ============ */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Pipeline Status
        </h2>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-5">
          {lastResult ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <RotateCcw className="w-4 h-4 text-gray-400" />
                <span className="font-medium text-gray-700">
                  Last loaded scenario:
                </span>
                <span className="text-gray-900 font-semibold">
                  {formatLabel(lastResult.scenario)}
                </span>
              </div>

              {/* Ingestion counts */}
              <div className="grid grid-cols-3 gap-2 sm:gap-4 max-w-full sm:max-w-md">
                <div className="bg-emerald-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-emerald-700">
                    {lastResult.created}
                  </div>
                  <div className="text-[11px] font-medium text-emerald-600 uppercase tracking-wider">
                    Created
                  </div>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-blue-700">
                    {lastResult.updated}
                  </div>
                  <div className="text-[11px] font-medium text-blue-600 uppercase tracking-wider">
                    Updated
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-600">
                    {lastResult.skipped}
                  </div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                    Skipped
                  </div>
                </div>
              </div>

              {/* Readiness from dashboard */}
              {store.dashboard?.readiness && (
                <div className="mt-2 pt-3 border-t border-gray-100">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium text-gray-500">
                      Readiness:
                    </span>
                    <span className="text-gray-900 font-medium">
                      {Math.round(store.dashboard.readiness.score * 100)}%
                    </span>
                    <span className="text-gray-400">|</span>
                    <span className="text-gray-500">
                      Completeness:{' '}
                      {Math.round(
                        store.dashboard.readiness.completeness * 100,
                      )}
                      %
                    </span>
                  </div>
                  {store.dashboard.readiness.missing.length > 0 && (
                    <div className="mt-1 text-xs text-amber-600">
                      Missing:{' '}
                      {store.dashboard.readiness.missing.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400">
              No scenario loaded yet. Choose a scenario above to get started.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
