import { useState } from 'react';
import { confirmAndAnalyze, type UploadResponse, type OwnerReport } from '../lib/api';

interface Props {
  uploadResult: UploadResponse;
  onComplete: (report: OwnerReport, explanation: string, internal: Record<string, unknown>) => void;
  onBack: () => void;
}

const TYPE_LABELS: Record<string, string> = {
  sales_summary: 'Sales Summary',
  sales_by_hour: 'Sales by Hour',
  labor_summary: 'Labor Report',
  punches: 'Time Clock Punches',
  schedule: 'Schedule',
  refunds_voids_comps: 'Refunds / Voids / Comps',
  menu_mix: 'Menu Mix',
  employee_roster: 'Employee Roster',
  unknown: 'Unknown',
};

export function ConfirmPage({ uploadResult, onComplete, onBack }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    setLoading(true);
    setError('');
    try {
      // Accept all as-is for now
      const corrections = uploadResult.confirmations.map((c) => ({
        sheet: c.sheet,
        type: 'confirm' as const,
      }));
      const result = await confirmAndAnalyze(uploadResult.session_id, corrections);
      onComplete(result.report, result.explanation, result.internal);
    } catch (e: any) {
      setError(e.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-16">
      <div className="max-w-2xl w-full">
        <button onClick={onBack} className="text-gray-500 hover:text-white text-sm mb-6 cursor-pointer">
          &larr; Back
        </button>

        <h2 className="text-2xl font-bold mb-2">Confirm file classifications</h2>
        <p className="text-gray-400 text-sm mb-6">
          We identified your files but need confirmation on a few. Review and adjust if needed.
        </p>

        {/* Completeness bar */}
        <div className="mb-8">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Data completeness</span>
            <span>{uploadResult.data_completeness}/100</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full transition-all"
              style={{ width: `${uploadResult.data_completeness}%` }}
            />
          </div>
        </div>

        {/* Classifications */}
        <div className="space-y-3">
          {uploadResult.classifications.map((clf, i) => {
            const needsConfirm = uploadResult.confirmations.some(
              (c) => c.sheet === (clf.sheet ? `${clf.file}:${clf.sheet}` : clf.file)
            );

            return (
              <div
                key={i}
                className={`p-4 rounded-xl border ${
                  needsConfirm ? 'border-amber-600 bg-amber-900/10' : 'border-gray-800 bg-gray-900'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium text-sm">{clf.file}</div>
                    {clf.sheet && <div className="text-xs text-gray-500">Sheet: {clf.sheet}</div>}
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      clf.confidence >= 0.8
                        ? 'bg-green-900/50 text-green-400'
                        : clf.confidence >= 0.5
                        ? 'bg-amber-900/50 text-amber-400'
                        : 'bg-red-900/50 text-red-400'
                    }`}
                  >
                    {(clf.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="text-sm text-gray-300 mb-2">
                  Detected as: <span className="font-semibold text-white">{TYPE_LABELS[clf.predicted_type] || clf.predicted_type}</span>
                </div>

                {clf.columns.length > 0 && (
                  <div className="text-xs text-gray-500">
                    Mapped: {clf.columns.map((c) => `${c.raw} -> ${c.mapped_to}`).join(', ')}
                  </div>
                )}

                <div className="text-xs text-gray-600 mt-1">{clf.row_count} rows</div>
              </div>
            );
          })}
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleConfirm}
          disabled={loading}
          className={`mt-8 w-full py-3 rounded-lg font-bold text-lg transition-colors cursor-pointer ${
            loading ? 'bg-gray-800 text-gray-600 cursor-not-allowed' : 'bg-amber-500 hover:bg-amber-400 text-black'
          }`}
        >
          {loading ? 'Running analysis...' : 'Looks good — run analysis'}
        </button>
      </div>
    </div>
  );
}
