import { create } from 'zustand';
import type { AppMode, DashboardSnapshot, Location } from '../types/api';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface AppState {
  mode: AppMode;
  locations: Location[];
  activeLocationId: string | null;
  dashboard: DashboardSnapshot | null;
  loading: boolean;
  error: string | null;
  toasts: Toast[];

  setMode: (mode: AppMode) => void;
  setLocations: (locations: Location[]) => void;
  setActiveLocation: (id: string | null) => void;
  setDashboard: (dashboard: DashboardSnapshot | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

let toastId = 0;

export const useStore = create<AppState>((set) => ({
  mode: 'demo',
  locations: [],
  activeLocationId: null,
  dashboard: null,
  loading: false,
  error: null,
  toasts: [],

  setMode: (mode) => set({ mode }),
  setLocations: (locations) => set({ locations }),
  setActiveLocation: (id) => set({ activeLocationId: id, dashboard: null }),
  setDashboard: (dashboard) => set({ dashboard }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  addToast: (toast) => {
    const id = String(++toastId);
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }));
    setTimeout(() => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })), 4000);
  },
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
