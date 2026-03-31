// In production under /demo/, API is at /demo/api/v1
// In dev, proxy handles it at /api/v1
const BASE = import.meta.env.PROD ? '/demo/api/v1' : '/api/v1';

export interface Classification {
  file: string;
  sheet: string | null;
  predicted_type: string;
  confidence: number;
  signals: string[];
  columns: { raw: string; mapped_to: string; confidence: number }[];
  row_count: number;
}

export interface Confirmation {
  sheet: string;
  type: 'classification' | 'mapping';
  current: string;
  confidence: number;
  alternatives: string[];
  columns: { raw_name: string; mapped_to: string; confidence: number; method: string }[];
}

export interface OwnerReport {
  date_range_start: string | null;
  date_range_end: string | null;
  days_covered: number;
  estimated_annual_leakage: number;
  average_monthly_leakage: number;
  top_categories: { category: string; estimated_annual_impact: number }[];
  confidence: string;
}

export interface UploadResponse {
  session_id: string;
  classifications: Classification[];
  data_completeness: number;
  needs_confirmation: boolean;
  confirmations: Confirmation[];
  report?: OwnerReport;
  explanation?: string;
  internal?: Record<string, unknown>;
}

export interface AnalyzeResponse {
  session_id?: string;
  report: OwnerReport;
  explanation: string;
  internal: Record<string, unknown>;
  text_summary?: string;
}

export async function uploadFiles(
  files: File[],
  restaurantName: string,
): Promise<UploadResponse> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  form.append('restaurant_name', restaurantName);

  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function confirmAndAnalyze(
  sessionId: string,
  corrections: Record<string, unknown>[] = [],
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append('session_id', sessionId);
  form.append('corrections', JSON.stringify(corrections));

  const res = await fetch(`${BASE}/confirm`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

export interface LeadData {
  name: string;
  email: string;
  phone: string;
  restaurant_name: string;
  address: string;
  top_concerns: string[];
  estimated_leakage: number;
}

export async function submitLead(lead: LeadData): Promise<void> {
  const res = await fetch(`${BASE}/leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lead),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Submission failed');
  }
}

export async function quickAnalyze(
  files: File[],
  restaurantName: string,
): Promise<AnalyzeResponse> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  form.append('restaurant_name', restaurantName);

  const res = await fetch(`${BASE}/analyze`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}
