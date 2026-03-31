import { useState } from 'react';
import type { OwnerReport } from '../lib/api';

interface Props {
  report: OwnerReport;
  explanation: string;
  internalReport: Record<string, unknown> | null;
  onReset: () => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  overstaffing: 'Overstaffing on low-volume shifts',
  refund_abuse: 'Unusual refund and comp concentration',
  ghost_labor: 'Ghost or low-productivity labor',
  menu_mix_margin_leak: 'Menu mix margin leakage',
  understaffing: 'Understaffing during peak periods',
};

const CONFIDENCE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  high: { bg: 'bg-green-900/30', text: 'text-green-400', label: 'High confidence' },
  medium: { bg: 'bg-amber-900/30', text: 'text-amber-400', label: 'Medium confidence' },
  low: { bg: 'bg-red-900/30', text: 'text-red-400', label: 'Low confidence' },
};

function formatMoney(n: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
}

export function ResultsPage({ report, explanation, internalReport, onReset }: Props) {
  const [showInternal, setShowInternal] = useState(false);
  const conf = CONFIDENCE_STYLES[report.confidence] || CONFIDENCE_STYLES.low;

  return (
    <div className="min-h-screen px-6 py-16">
      <div className="max-w-2xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="w-14 h-14 bg-amber-500 rounded-xl flex items-center justify-center mx-auto mb-6">
            <span className="text-2xl font-black text-white">86</span>
          </div>

          <h1 className="text-xl text-gray-400 mb-2">Estimated annual leakage</h1>
          <div className="text-6xl sm:text-7xl font-black text-white tracking-tight mb-2">
            {formatMoney(report.estimated_annual_leakage)}
          </div>
          <div className="text-lg text-gray-500">
            ~{formatMoney(report.average_monthly_leakage)} / month
          </div>

          {report.date_range_start && report.date_range_end && (
            <div className="mt-3 text-sm text-gray-600">
              Based on {report.days_covered} days of data ({report.date_range_start} to {report.date_range_end})
            </div>
          )}
        </div>

        {/* Top categories */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Biggest sources
          </h2>
          <div className="space-y-3">
            {report.top_categories.map((cat, i) => {
              const pct = report.estimated_annual_leakage > 0
                ? (cat.estimated_annual_impact / report.estimated_annual_leakage) * 100
                : 0;

              return (
                <div key={i} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-amber-400">{i + 1}</span>
                      <span className="text-sm font-medium">
                        {CATEGORY_LABELS[cat.category] || cat.category}
                      </span>
                    </div>
                    <span className="font-bold">{formatMoney(cat.estimated_annual_impact)}</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Confidence */}
        <div className={`${conf.bg} rounded-xl p-4 border border-gray-800 mb-8`}>
          <div className={`text-sm font-semibold ${conf.text} mb-1`}>
            {conf.label}
          </div>
          <p className="text-sm text-gray-400">
            {report.confidence === 'high' && 'Strong data coverage across multiple report types.'}
            {report.confidence === 'medium' && 'Decent coverage but additional data would sharpen estimates.'}
            {report.confidence === 'low' && 'Limited data available. These are preliminary estimates.'}
          </p>
        </div>

        {/* Explanation */}
        {explanation && (
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 mb-8">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">What we found</h3>
            <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
              {explanation}
            </div>
          </div>
        )}

        {/* CTAs */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
          <button
            onClick={() => setShowInternal(!showInternal)}
            className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            {showInternal ? 'Hide' : 'View'} methodology
          </button>
          <a
            href="mailto:adam@adamscottthomas.com?subject=EightySix%20Full%20Audit%20Request"
            className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors text-center"
          >
            Request full audit
          </a>
          <a
            href="mailto:adam@adamscottthomas.com?subject=EightySix%20Walkthrough"
            className="px-4 py-2.5 bg-amber-500 hover:bg-amber-400 text-black rounded-lg text-sm font-bold transition-colors text-center"
          >
            Book walkthrough
          </a>
        </div>

        {/* Internal report */}
        {showInternal && internalReport && (
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 mb-8">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Internal analysis detail</h3>
            <pre className="text-xs text-gray-400 overflow-x-auto max-h-96">
              {JSON.stringify(internalReport, null, 2)}
            </pre>
          </div>
        )}

        {/* Reset */}
        <div className="text-center">
          <button
            onClick={onReset}
            className="text-sm text-gray-500 hover:text-white transition-colors cursor-pointer"
          >
            Analyze another restaurant
          </button>
        </div>
      </div>
    </div>
  );
}
