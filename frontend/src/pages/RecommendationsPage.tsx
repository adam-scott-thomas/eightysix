import { useEffect, useState, useCallback } from 'react';
import {
  Lightbulb,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { useStore } from '../hooks/useStore';
import { Card } from '../components/shared/Card';
import { StatusBadge } from '../components/shared/StatusBadge';
import { EmptyState } from '../components/shared/EmptyState';
import {
  getRecommendations,
  applyRecommendation,
  dismissRecommendation,
} from '../lib/api';
import type { Recommendation } from '../types/api';

type TabStatus = 'pending' | 'applied' | 'dismissed' | 'expired';

function categoryVariant(category: string): 'green' | 'yellow' | 'red' | 'blue' | 'gray' {
  const c = category.toLowerCase();
  if (c === 'revenue' || c === 'sales' || c === 'upsell') return 'green';
  if (c === 'staffing' || c === 'labor') return 'blue';
  if (c === 'cost' || c === 'waste' || c === 'leakage') return 'red';
  if (c === 'menu' || c === 'operations') return 'yellow';
  return 'gray';
}

const TABS: { id: TabStatus; label: string }[] = [
  { id: 'pending', label: 'Pending' },
  { id: 'applied', label: 'Applied' },
  { id: 'dismissed', label: 'Dismissed' },
  { id: 'expired', label: 'Expired' },
];

export function RecommendationsPage() {
  const store = useStore();
  const [tab, setTab] = useState<TabStatus>('pending');
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [actioning, setActioning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const locId = store.activeLocationId;

  const fetchRecs = useCallback(async () => {
    if (!locId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getRecommendations(locId, tab);
      setRecs(data as Recommendation[]);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }, [locId, tab]);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  const handleApply = async (id: string) => {
    setActioning(id);
    try {
      await applyRecommendation(id);
      await fetchRecs();
    } catch (e: any) {
      setError(e.message ?? 'Failed to apply recommendation');
    } finally {
      setActioning(null);
    }
  };

  const handleDismiss = async (id: string) => {
    setActioning(id);
    try {
      await dismissRecommendation(id);
      await fetchRecs();
    } catch (e: any) {
      setError(e.message ?? 'Failed to dismiss recommendation');
    } finally {
      setActioning(null);
    }
  };

  if (!locId) {
    return (
      <EmptyState
        icon={<Lightbulb className="w-12 h-12" />}
        title="Select a location"
        description="Choose a location to view its recommendations."
      />
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Recommendations</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            AI-generated actions to improve operations
          </p>
        </div>
        <button
          onClick={fetchRecs}
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
      {!loading && recs.length === 0 && (
        <EmptyState
          icon={<Sparkles className="w-12 h-12" />}
          title={`No ${tab} recommendations`}
          description={
            tab === 'pending'
              ? 'No recommendations at this time. Recompute the dashboard to generate new ones.'
              : `No ${tab} recommendations found.`
          }
        />
      )}

      {/* Recommendation Cards */}
      {!loading && recs.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
          {recs.map((rec) => (
            <Card key={rec.id} title={rec.title} className="flex flex-col">
              <div className="flex-1">
                {/* Badges */}
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <StatusBadge variant={categoryVariant(rec.category)} size="md">
                    {rec.category}
                  </StatusBadge>
                  <StatusBadge variant="gray" size="sm">
                    {rec.status}
                  </StatusBadge>
                </div>

                {/* Reason */}
                <p className="text-sm text-gray-600 mb-3">{rec.reason}</p>

                {/* Action Description */}
                {rec.action_description && (
                  <div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 mb-3">
                    <p className="text-xs font-medium text-blue-700 flex items-center gap-1 mb-1">
                      <ArrowRight className="w-3 h-3" />
                      Suggested Action
                    </p>
                    <p className="text-sm text-blue-800">{rec.action_description}</p>
                  </div>
                )}

                {/* Confidence Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-500">Confidence</span>
                    <span className="text-xs font-semibold text-gray-700">
                      {(rec.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        rec.confidence >= 0.8
                          ? 'bg-emerald-500'
                          : rec.confidence >= 0.5
                            ? 'bg-amber-500'
                            : 'bg-gray-400'
                      }`}
                      style={{ width: `${rec.confidence * 100}%` }}
                    />
                  </div>
                </div>

                {/* Impact Preview */}
                {rec.estimated_impact && Object.keys(rec.estimated_impact).length > 0 && (
                  <div className="bg-gray-50 rounded-lg px-3 py-2 mb-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">Estimated Impact</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-1">
                      {Object.entries(rec.estimated_impact).map(([key, value]) => (
                        <span key={key} className="text-xs text-gray-700">
                          <span className="font-medium capitalize">
                            {key.replace(/_/g, ' ')}:
                          </span>{' '}
                          {typeof value === 'number'
                            ? value.toLocaleString('en-US', {
                                minimumFractionDigits: 0,
                                maximumFractionDigits: 2,
                              })
                            : String(value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400 mb-3">
                  <span>Created: {new Date(rec.created_at).toLocaleString()}</span>
                  {rec.expires_at && (
                    <span>Expires: {new Date(rec.expires_at).toLocaleString()}</span>
                  )}
                  {rec.applied_at && (
                    <span>Applied: {new Date(rec.applied_at).toLocaleString()}</span>
                  )}
                  {rec.dismissed_at && (
                    <span>Dismissed: {new Date(rec.dismissed_at).toLocaleString()}</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              {rec.status === 'pending' && (
                <div className="flex flex-col sm:flex-row gap-2 pt-3 border-t border-gray-100">
                  <button
                    onClick={() => handleApply(rec.id)}
                    disabled={actioning === rec.id}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 transition-colors duration-150 cursor-pointer disabled:opacity-50"
                  >
                    {actioning === rec.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle className="w-3.5 h-3.5" />
                    )}
                    Apply
                  </button>
                  <button
                    onClick={() => handleDismiss(rec.id)}
                    disabled={actioning === rec.id}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-white border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors duration-150 cursor-pointer disabled:opacity-50"
                  >
                    {actioning === rec.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5" />
                    )}
                    Dismiss
                  </button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
