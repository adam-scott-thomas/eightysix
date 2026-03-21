import { useEffect, useState, useCallback } from 'react';
import { Bell, CheckCircle, Eye, Loader2, RefreshCw } from 'lucide-react';
import { useStore } from '../hooks/useStore';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { Card } from '../components/shared/Card';
import { StatusBadge } from '../components/shared/StatusBadge';
import { EmptyState } from '../components/shared/EmptyState';
import { getAlerts, acknowledgeAlert, resolveAlert } from '../lib/api';
import type { Alert } from '../types/api';

type TabStatus = 'active' | 'acknowledged' | 'resolved';

function severityVariant(severity: string): 'green' | 'yellow' | 'red' | 'blue' | 'gray' {
  const s = severity.toLowerCase();
  if (s === 'critical' || s === 'high') return 'red';
  if (s === 'medium' || s === 'warning') return 'yellow';
  if (s === 'low' || s === 'info') return 'blue';
  return 'gray';
}

const TABS: { id: TabStatus; label: string }[] = [
  { id: 'active', label: 'Active' },
  { id: 'acknowledged', label: 'Acknowledged' },
  { id: 'resolved', label: 'Resolved' },
];

export function AlertsPage() {
  const store = useStore();
  const [tab, setTab] = useState<TabStatus>('active');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [actioning, setActioning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const locId = store.activeLocationId;

  const fetchAlerts = useCallback(async () => {
    if (!locId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAlerts(locId, tab);
      setAlerts(data as Alert[]);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, [locId, tab]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  useAutoRefresh(fetchAlerts, 30000, !!locId);

  const handleAcknowledge = async (id: string) => {
    setActioning(id);
    try {
      await acknowledgeAlert(id);
      await fetchAlerts();
    } catch (e: any) {
      setError(e.message ?? 'Failed to acknowledge alert');
    } finally {
      setActioning(null);
    }
  };

  const handleResolve = async (id: string) => {
    setActioning(id);
    try {
      await resolveAlert(id);
      await fetchAlerts();
    } catch (e: any) {
      setError(e.message ?? 'Failed to resolve alert');
    } finally {
      setActioning(null);
    }
  };

  if (!locId) {
    return (
      <EmptyState
        icon={<Bell className="w-12 h-12" />}
        title="Select a location"
        description="Choose a location to view its alerts."
      />
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Alerts</h1>
          <p className="text-xs text-gray-500 mt-0.5">Monitor and manage operational alerts</p>
        </div>
        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="inline-flex items-center gap-1.5 sm:gap-2 rounded-lg bg-white border border-gray-200 px-2.5 sm:px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors duration-150 cursor-pointer disabled:opacity-50 shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="overflow-x-auto -mx-3 px-3 sm:mx-0 sm:px-0">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 sm:px-4 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer whitespace-nowrap ${
                tab === t.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
        </div>
      )}

      {/* Empty */}
      {!loading && alerts.length === 0 && (
        <EmptyState
          icon={<CheckCircle className="w-12 h-12" />}
          title={`No ${tab} alerts`}
          description={
            tab === 'active'
              ? 'All clear! No active alerts for this location.'
              : `No ${tab} alerts found.`
          }
        />
      )}

      {/* Alert List */}
      {!loading && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Card key={alert.id} title={alert.title} className="overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <StatusBadge variant={severityVariant(alert.severity)} size="md">
                      {alert.severity}
                    </StatusBadge>
                    <StatusBadge variant="gray" size="sm">
                      {alert.alert_type}
                    </StatusBadge>
                    <StatusBadge
                      variant={
                        alert.status === 'active'
                          ? 'red'
                          : alert.status === 'acknowledged'
                            ? 'yellow'
                            : 'green'
                      }
                      size="sm"
                    >
                      {alert.status}
                    </StatusBadge>
                  </div>
                  {alert.message && (
                    <p className="text-sm text-gray-600 mb-2">{alert.message}</p>
                  )}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
                    {alert.triggered_at && (
                      <span>Triggered: {new Date(alert.triggered_at).toLocaleString()}</span>
                    )}
                    {alert.acknowledged_at && (
                      <span>Acknowledged: {new Date(alert.acknowledged_at).toLocaleString()}</span>
                    )}
                    {alert.resolved_at && (
                      <span>Resolved: {new Date(alert.resolved_at).toLocaleString()}</span>
                    )}
                    {alert.ttl_minutes != null && (
                      <span>TTL: {alert.ttl_minutes}m</span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                {(alert.status === 'active' || alert.status === 'acknowledged') && (
                  <div className="flex flex-col sm:flex-row gap-2 shrink-0 w-full sm:w-auto">
                    {alert.status === 'active' && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={actioning === alert.id}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors duration-150 cursor-pointer disabled:opacity-50"
                      >
                        {actioning === alert.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Eye className="w-3.5 h-3.5" />
                        )}
                        Acknowledge
                      </button>
                    )}
                    <button
                      onClick={() => handleResolve(alert.id)}
                      disabled={actioning === alert.id}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-100 transition-colors duration-150 cursor-pointer disabled:opacity-50"
                    >
                      {actioning === alert.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <CheckCircle className="w-3.5 h-3.5" />
                      )}
                      Resolve
                    </button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
