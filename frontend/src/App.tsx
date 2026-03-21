import { useState, useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { useStore } from './hooks/useStore';
import { Toasts } from './components/shared/Toasts';
import * as api from './lib/api';
import { DashboardPage } from './pages/DashboardPage';
import { AlertsPage } from './pages/AlertsPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { IntegrityPage } from './pages/IntegrityPage';
import { DataInputPage } from './pages/DataInputPage';
import { DemoPage } from './pages/DemoPage';

function App() {
  const store = useStore();
  const [page, setPage] = useState('dashboard');

  useEffect(() => {
    api.getLocations().then(store.setLocations).catch(() => {});
  }, []);

  useEffect(() => {
    if (store.activeLocationId) {
      store.setLoading(true);
      api
        .getDashboard(store.activeLocationId)
        .then(store.setDashboard)
        .catch(() => store.setDashboard(null))
        .finally(() => store.setLoading(false));
    }
  }, [store.activeLocationId]);

  const handleRecompute = async () => {
    if (!store.activeLocationId) return;
    store.setLoading(true);
    store.setError(null);
    try {
      const snap = await api.recompute(store.activeLocationId);
      store.setDashboard(snap);
    } catch (e: any) {
      store.setError(e.message);
    } finally {
      store.setLoading(false);
    }
  };

  const renderPage = () => {
    switch (page) {
      case 'dashboard':
        return <DashboardPage />;
      case 'alerts':
        return <AlertsPage />;
      case 'recommendations':
        return <RecommendationsPage />;
      case 'integrity':
        return <IntegrityPage />;
      case 'data':
        return <DataInputPage />;
      case 'demo':
        return <DemoPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <AppShell
      mode={store.mode}
      onModeChange={store.setMode}
      activePage={page}
      onNavigate={setPage}
      locations={store.locations}
      activeLocationId={store.activeLocationId}
      onLocationChange={store.setActiveLocation}
      onRecompute={handleRecompute}
      dashboardStatus={store.dashboard?.status ?? null}
      snapshotAt={store.dashboard?.snapshot_at ?? null}
      loading={store.loading}
    >
      {store.error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {store.error}
          <button
            onClick={() => store.setError(null)}
            className="ml-2 font-medium underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}
      {renderPage()}
      <Toasts />
    </AppShell>
  );
}

export default App;
