import { useEffect, useState, useCallback } from 'react';
import {
  ShieldAlert,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  Search,
  FileText,
  X,
} from 'lucide-react';
import { useStore } from '../hooks/useStore';
import { Card } from '../components/shared/Card';
import { StatusBadge } from '../components/shared/StatusBadge';
import { EmptyState } from '../components/shared/EmptyState';
import { getIntegrityFlags, reviewIntegrityFlag } from '../lib/api';
import type { IntegrityFlag } from '../types/api';

type TabStatus = 'open' | 'under_review' | 'confirmed' | 'dismissed';

function severityVariant(severity: string): 'green' | 'yellow' | 'red' | 'blue' | 'gray' {
  const s = severity.toLowerCase();
  if (s === 'critical' || s === 'high') return 'red';
  if (s === 'medium' || s === 'warning') return 'yellow';
  if (s === 'low' || s === 'info') return 'blue';
  return 'gray';
}

const TABS: { id: TabStatus; label: string }[] = [
  { id: 'open', label: 'Open' },
  { id: 'under_review', label: 'Under Review' },
  { id: 'confirmed', label: 'Confirmed' },
  { id: 'dismissed', label: 'Dismissed' },
];

export function IntegrityPage() {
  const store = useStore();
  const [tab, setTab] = useState<TabStatus>('open');
  const [flags, setFlags] = useState<IntegrityFlag[]>([]);
  const [loading, setLoading] = useState(false);
  const [actioning, setActioning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Review form state
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [reviewStatus, setReviewStatus] = useState<'confirmed' | 'dismissed'>('confirmed');
  const [reviewNotes, setReviewNotes] = useState('');

  const locId = store.activeLocationId;

  const fetchFlags = useCallback(async () => {
    if (!locId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getIntegrityFlags(locId, tab);
      setFlags(data as IntegrityFlag[]);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load integrity flags');
    } finally {
      setLoading(false);
    }
  }, [locId, tab]);

  useEffect(() => {
    fetchFlags();
  }, [fetchFlags]);

  const handleReview = async () => {
    if (!reviewingId) return;
    setActioning(reviewingId);
    try {
      await reviewIntegrityFlag(reviewingId, {
        status: reviewStatus,
        notes: reviewNotes || undefined,
      });
      setReviewingId(null);
      setReviewNotes('');
      await fetchFlags();
    } catch (e: any) {
      setError(e.message ?? 'Failed to review flag');
    } finally {
      setActioning(null);
    }
  };

  const openReview = (flagId: string) => {
    setReviewingId(flagId);
    setReviewStatus('confirmed');
    setReviewNotes('');
  };

  if (!locId) {
    return (
      <EmptyState
        icon={<ShieldAlert className="w-12 h-12" />}
        title="Select a location"
        description="Choose a location to view its integrity flags."
      />
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Integrity</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Fraud detection and data integrity monitoring
          </p>
        </div>
        <button
          onClick={fetchFlags}
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
      {!loading && flags.length === 0 && (
        <EmptyState
          icon={<ShieldAlert className="w-12 h-12" />}
          title={`No ${tab.replace(/_/g, ' ')} flags`}
          description={
            tab === 'open'
              ? 'No integrity concerns detected. The system is monitoring continuously.'
              : `No flags with status "${tab.replace(/_/g, ' ')}" found.`
          }
        />
      )}

      {/* Flags */}
      {!loading && flags.length > 0 && (
        <div className="space-y-3">
          {flags.map((flag) => (
            <Card key={flag.id} title={flag.title} className="overflow-hidden">
              <div className="space-y-3">
                {/* Badges row */}
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge variant={severityVariant(flag.severity)} size="md">
                    {flag.severity}
                  </StatusBadge>
                  <StatusBadge variant="gray" size="sm">
                    {flag.flag_type}
                  </StatusBadge>
                  <StatusBadge
                    variant={
                      flag.status === 'open'
                        ? 'red'
                        : flag.status === 'under_review'
                          ? 'yellow'
                          : flag.status === 'confirmed'
                            ? 'red'
                            : 'gray'
                    }
                    size="sm"
                  >
                    {flag.status.replace(/_/g, ' ')}
                  </StatusBadge>
                </div>

                {/* Risk Score Meter */}
                {flag.fraud_risk_score != null && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-500">Fraud Risk Score</span>
                      <span
                        className={`text-xs font-bold ${
                          flag.fraud_risk_score > 0.7
                            ? 'text-red-600'
                            : flag.fraud_risk_score > 0.4
                              ? 'text-amber-600'
                              : 'text-emerald-600'
                        }`}
                      >
                        {(flag.fraud_risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          flag.fraud_risk_score > 0.7
                            ? 'bg-red-500'
                            : flag.fraud_risk_score > 0.4
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                        }`}
                        style={{ width: `${flag.fraud_risk_score * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Confidence */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Confidence:</span>
                  <span className="text-xs font-semibold text-gray-700">
                    {(flag.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Message */}
                {flag.message && (
                  <p className="text-sm text-gray-600">{flag.message}</p>
                )}

                {/* Evidence Preview */}
                {flag.evidence_json && Object.keys(flag.evidence_json).length > 0 && (
                  <details className="group">
                    <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      Evidence ({Object.keys(flag.evidence_json).length} fields)
                    </summary>
                    <pre className="mt-2 text-xs text-gray-600 bg-gray-50 rounded-lg px-2 sm:px-3 py-2 overflow-x-auto max-h-40 max-w-[calc(100vw-4rem)]">
                      {JSON.stringify(flag.evidence_json, null, 2)}
                    </pre>
                  </details>
                )}

                {/* Timestamps */}
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
                  <span>Created: {new Date(flag.created_at).toLocaleString()}</span>
                  {flag.resolved_at && (
                    <span>Resolved: {new Date(flag.resolved_at).toLocaleString()}</span>
                  )}
                </div>

                {/* Review Button / Inline Form */}
                {(flag.status === 'open' || flag.status === 'under_review') && (
                  <>
                    {reviewingId === flag.id ? (
                      <div className="border border-gray-200 rounded-lg p-3 sm:p-4 bg-gray-50 space-y-3">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">Review Flag</p>
                          <button
                            onClick={() => setReviewingId(null)}
                            className="text-gray-400 hover:text-gray-600 cursor-pointer"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Status Selection */}
                        <div className="flex gap-2">
                          <button
                            onClick={() => setReviewStatus('confirmed')}
                            className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors duration-150 cursor-pointer ${
                              reviewStatus === 'confirmed'
                                ? 'bg-red-100 text-red-700 border-2 border-red-300'
                                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                            }`}
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            Confirm
                          </button>
                          <button
                            onClick={() => setReviewStatus('dismissed')}
                            className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors duration-150 cursor-pointer ${
                              reviewStatus === 'dismissed'
                                ? 'bg-gray-200 text-gray-800 border-2 border-gray-400'
                                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                            }`}
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            Dismiss
                          </button>
                        </div>

                        {/* Notes */}
                        <textarea
                          value={reviewNotes}
                          onChange={(e) => setReviewNotes(e.target.value)}
                          placeholder="Add review notes (optional)"
                          rows={2}
                          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        />

                        {/* Submit */}
                        <button
                          onClick={handleReview}
                          disabled={actioning === flag.id}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 transition-colors duration-150 cursor-pointer disabled:opacity-50"
                        >
                          {actioning === flag.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CheckCircle className="w-3.5 h-3.5" />
                          )}
                          Submit Review
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => openReview(flag.id)}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-white border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors duration-150 cursor-pointer shadow-sm"
                      >
                        <Search className="w-3.5 h-3.5" />
                        Review
                      </button>
                    )}
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
