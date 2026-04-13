import { useState } from 'react';
import { read, utils } from 'xlsx';
import { uploadFiles, type UploadResponse } from '../lib/api';

interface Props {
  onAnalyze: (result: UploadResponse, restaurantName: string) => void;
  onBack: () => void;
}

interface DemoFile {
  label: string;
  tag: string;
  description: string;
  filename: string;
}

const DEMO_FILES: DemoFile[] = [
  {
    label: 'March 2026 — Standard',
    tag: 'Clean data',
    description:
      'A typical month at a casual-dining restaurant. Normal sales, labor, and refund patterns across 5 report types.',
    filename: 'restaurant_march_2026.xlsx',
  },
  {
    label: 'March 2026 — Stress Test',
    tag: 'Red flags inside',
    description:
      'Same restaurant, but with suspicious patterns — high refund volume, overtime anomalies, and cost irregularities.',
    filename: 'restaurant_adversarial_march_2026.xlsx',
  },
];

type SheetData = {
  name: string;
  headers: string[];
  rows: unknown[][];
  rowCount: number;
};

export function DemoDataPage({ onAnalyze, onBack }: Props) {
  const [activeFile, setActiveFile] = useState<number | null>(null);
  const [activeSheet, setActiveSheet] = useState(0);
  const [sheets, setSheets] = useState<SheetData[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [fileBlob, setFileBlob] = useState<Blob | null>(null);

  const loadFile = async (index: number) => {
    if (activeFile === index) {
      setActiveFile(null);
      setSheets([]);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const base = import.meta.env.BASE_URL;
      const res = await fetch(
        `${base}demo-data/${DEMO_FILES[index].filename}`,
      );
      if (!res.ok) throw new Error('File not found');
      const buf = await res.arrayBuffer();
      setFileBlob(
        new Blob([buf], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }),
      );

      const wb = read(new Uint8Array(buf), { type: 'array', cellDates: true });
      const parsed: SheetData[] = wb.SheetNames.map((name) => {
        const ws = wb.Sheets[name];
        const json = utils.sheet_to_json<unknown[]>(ws, {
          header: 1,
          defval: '',
        });
        const headers = (json[0] as string[] || []).map(String);
        const rows = json.slice(1);
        return { name, headers, rows, rowCount: rows.length };
      });
      setSheets(parsed);
      setActiveFile(index);
      setActiveSheet(0);
    } catch {
      setError('Failed to load demo file.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (activeFile === null || !fileBlob) return;
    const url = URL.createObjectURL(fileBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = DEMO_FILES[activeFile].filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleAnalyze = async () => {
    if (activeFile === null || !fileBlob) return;
    setAnalyzing(true);
    setError('');
    try {
      const file = new File([fileBlob], DEMO_FILES[activeFile].filename, {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const result = await uploadFiles([file], 'Demo Restaurant');
      onAnalyze(result, 'Demo Restaurant');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Analysis failed.';
      setError(msg);
      setAnalyzing(false);
    }
  };

  const currentSheet = sheets[activeSheet];

  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-16">
      <div className="max-w-5xl w-full">
        <button
          onClick={onBack}
          className="text-gray-500 hover:text-white text-sm mb-6 cursor-pointer"
        >
          &larr; Back
        </button>

        <h2 className="text-2xl font-bold mb-2">Demo Data</h2>
        <p className="text-gray-400 text-sm mb-8">
          Inspect sample restaurant data, then run the analysis to see what
          EightySix finds.
        </p>

        {/* File cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          {DEMO_FILES.map((f, i) => (
            <button
              key={i}
              onClick={() => loadFile(i)}
              disabled={loading}
              className={`text-left p-5 rounded-xl border transition-all cursor-pointer ${
                activeFile === i
                  ? 'border-amber-500 bg-amber-500/10'
                  : 'border-gray-700 bg-gray-900 hover:border-gray-500'
              } ${loading ? 'opacity-50 cursor-wait' : ''}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-white">{f.label}</span>
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    i === 0
                      ? 'bg-green-900/50 text-green-400'
                      : 'bg-red-900/50 text-red-400'
                  }`}
                >
                  {f.tag}
                </span>
              </div>
              <div className="text-sm text-gray-400 mb-3">{f.description}</div>
              <div className="text-xs text-gray-500">
                5 sheets &middot; XLSX &middot;{' '}
                {i === 0 ? '~400 rows' : '~440 rows'}
              </div>
            </button>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm mb-4">
            {error}
          </div>
        )}

        {/* Data inspector */}
        {activeFile !== null && sheets.length > 0 && (
          <div className="border border-gray-700 rounded-xl overflow-hidden">
            {/* Sheet tabs */}
            <div className="flex border-b border-gray-700 bg-gray-900 overflow-x-auto">
              {sheets.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setActiveSheet(i)}
                  className={`px-4 py-2.5 text-sm whitespace-nowrap transition-colors cursor-pointer border-b-2 ${
                    activeSheet === i
                      ? 'text-amber-400 border-amber-400 bg-gray-800'
                      : 'text-gray-400 hover:text-white border-transparent'
                  }`}
                >
                  {s.name}
                  <span className="ml-1.5 text-xs text-gray-600">
                    {s.rowCount}
                  </span>
                </button>
              ))}
            </div>

            {/* Data table */}
            {currentSheet && (
              <div className="overflow-auto max-h-[28rem]">
                <table className="w-full text-sm border-collapse">
                  <thead className="sticky top-0 z-10">
                    <tr className="bg-gray-800">
                      <th className="px-3 py-2 text-left text-[10px] font-medium text-gray-500 w-10">
                        #
                      </th>
                      {currentSheet.headers.map((h, i) => (
                        <th
                          key={i}
                          className="px-3 py-2 text-left text-xs font-medium text-gray-300 whitespace-nowrap"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {currentSheet.rows.map((row, ri) => (
                      <tr
                        key={ri}
                        className="hover:bg-gray-900/60 transition-colors"
                      >
                        <td className="px-3 py-1.5 text-[10px] text-gray-600 tabular-nums">
                          {ri + 1}
                        </td>
                        {currentSheet.headers.map((_, ci) => (
                          <td
                            key={ci}
                            className="px-3 py-1.5 text-gray-300 whitespace-nowrap tabular-nums"
                          >
                            {formatCell((row as unknown[])[ci])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 p-4 border-t border-gray-700 bg-gray-900">
              <button
                onClick={handleDownload}
                className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:border-white hover:text-white text-sm transition-colors cursor-pointer"
              >
                Download XLSX
              </button>
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className={`px-6 py-2 rounded-lg font-bold text-sm transition-colors cursor-pointer ${
                  analyzing
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-amber-500 hover:bg-amber-400 text-black'
                }`}
              >
                {analyzing ? 'Analyzing...' : 'Run Analysis on This File'}
              </button>
              {analyzing && (
                <span className="text-xs text-gray-500">
                  Uploading to the analysis engine...
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === '') return '';
  if (value instanceof Date) {
    return value.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  }
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return '';
    if (Number.isInteger(value) && Math.abs(value) < 1e6)
      return value.toLocaleString();
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}
