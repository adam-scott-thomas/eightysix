import { create } from 'zustand';
import type { AppMode, DashboardSnapshot, Location } from '../types/api';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AppState {
  // Auth
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;

  // App
  mode: AppMode;
  locations: Location[];
  activeLocationId: string | null;
  dashboard: DashboardSnapshot | null;
  loading: boolean;
  error: string | null;
  toasts: Toast[];

  // Auth actions
  loginSuccess: (user: AuthUser, token: string) => void;
  logout: () => void;

  // App actions
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

// Restore auth from localStorage on init
const savedToken = localStorage.getItem('rc_token');
const savedUser = (() => {
  try {
    const raw = localStorage.getItem('rc_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

export const useStore = create<AppState>((set) => ({
  user: savedUser,
  token: savedToken,
  isAuthenticated: !!(savedToken && savedUser),

  mode: 'demo',
  locations: [],
  activeLocationId: null,
  dashboard: null,
  loading: false,
  error: null,
  toasts: [],

  loginSuccess: (user, token) => {
    localStorage.setItem('rc_token', token);
    localStorage.setItem('rc_user', JSON.stringify(user));
    set({ user, token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('rc_token');
    localStorage.removeItem('rc_user');
    set({ user: null, token: null, isAuthenticated: false, locations: [], activeLocationId: null, dashboard: null });
  },

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
