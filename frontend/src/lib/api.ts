const BASE = '';

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json();
}

// -- Locations --
export const getLocations = () => request<any[]>('/api/v1/locations');
export const createLocation = (data: any) =>
  request<any>('/api/v1/locations', { method: 'POST', body: JSON.stringify(data) });

// -- Dashboard --
export const getDashboard = (locId: string) =>
  request<any>(`/api/v1/locations/${locId}/dashboard/current`);
export const getReadiness = (locId: string) =>
  request<any>(`/api/v1/locations/${locId}/dashboard/readiness`);
export const getTimeline = (locId: string, hours = 12) =>
  request<any[]>(`/api/v1/locations/${locId}/dashboard/timeline?hours=${hours}`);
export const recompute = (locId: string) =>
  request<any>(`/api/v1/locations/${locId}/dashboard/recompute`, { method: 'POST' });

// -- Alerts --
export const getAlerts = (locId: string, status = 'active') =>
  request<any[]>(`/api/v1/locations/${locId}/alerts?status=${status}`);
export const acknowledgeAlert = (id: string) =>
  request<any>(`/api/v1/alerts/${id}/acknowledge`, { method: 'PATCH' });
export const resolveAlert = (id: string) =>
  request<any>(`/api/v1/alerts/${id}/resolve`, { method: 'PATCH' });

// -- Recommendations --
export const getRecommendations = (locId: string, status = 'pending') =>
  request<any[]>(`/api/v1/locations/${locId}/recommendations?status=${status}`);
export const applyRecommendation = (id: string) =>
  request<any>(`/api/v1/recommendations/${id}/apply`, { method: 'PATCH' });
export const dismissRecommendation = (id: string) =>
  request<any>(`/api/v1/recommendations/${id}/dismiss`, { method: 'PATCH' });

// -- Integrity --
export const getIntegrityFlags = (locId: string, status = 'open') =>
  request<any[]>(`/api/v1/locations/${locId}/integrity-flags?status=${status}`);
export const reviewIntegrityFlag = (id: string, data: { status: string; notes?: string }) =>
  request<any>(`/api/v1/integrity-flags/${id}/review`, { method: 'PATCH', body: JSON.stringify(data) });

// -- Data input (live mode) --
export const bulkEmployees = (locId: string, data: any[]) =>
  request<any>(`/api/v1/locations/${locId}/employees/bulk`, { method: 'POST', body: JSON.stringify(data) });
export const bulkMenuItems = (locId: string, data: any[]) =>
  request<any>(`/api/v1/locations/${locId}/menu-items/bulk`, { method: 'POST', body: JSON.stringify(data) });
export const bulkOrders = (locId: string, data: any[]) =>
  request<any>(`/api/v1/locations/${locId}/orders/bulk`, { method: 'POST', body: JSON.stringify(data) });
export const bulkShifts = (locId: string, data: any[]) =>
  request<any>(`/api/v1/locations/${locId}/shifts/bulk`, { method: 'POST', body: JSON.stringify(data) });

// -- Read data --
export const getEmployees = (locId: string) =>
  request<any[]>(`/api/v1/locations/${locId}/employees`);
export const getMenuItems = (locId: string) =>
  request<any[]>(`/api/v1/locations/${locId}/menu-items`);
export const getOrders = (locId: string) =>
  request<any[]>(`/api/v1/locations/${locId}/orders`);
export const getShifts = (locId: string, active?: boolean) =>
  request<any[]>(`/api/v1/locations/${locId}/shifts${active !== undefined ? `?active=${active}` : ''}`);

// -- Demo controls --
export const demoReset = () =>
  request<any>('/api/v1/demo/reset', { method: 'POST' });
export const demoLoadScenario = (scenario: string) =>
  request<any>('/api/v1/demo/load-scenario', { method: 'POST', body: JSON.stringify({ scenario }) });
export const quickAssess = (data: { staff_count: number; orders_today: number; avg_ticket: number; restaurant_name?: string }) =>
  request<any>('/api/v1/demo/quick-assess', { method: 'POST', body: JSON.stringify(data) });
export const demoRecompute = (locId: string) =>
  request<any>('/api/v1/demo/recompute', { method: 'POST', body: JSON.stringify({ location_id: locId }) });
export const getScenarios = () =>
  request<{ scenarios: string[] }>('/api/v1/demo/scenarios');

// -- Health --
export const getHealth = () => request<any>('/health');
