import { useState } from 'react';
import { LandingPage } from './pages/LandingPage';
import { UploadPage } from './pages/UploadPage';
import { ConfirmPage } from './pages/ConfirmPage';
import { LeadCapturePage } from './pages/LeadCapturePage';
import { ResultsPage } from './pages/ResultsPage';
import type { UploadResponse, OwnerReport } from './lib/api';

type Page = 'landing' | 'upload' | 'confirm' | 'lead_capture' | 'results';

function App() {
  const [page, setPage] = useState<Page>('landing');
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [sessionId, setSessionId] = useState('');
  const [restaurantName, setRestaurantName] = useState('Restaurant');
  const [report, setReport] = useState<OwnerReport | null>(null);
  const [explanation, setExplanation] = useState('');

  const handleUploadComplete = (result: UploadResponse, name: string) => {
    setUploadResult(result);
    setSessionId(result.session_id);
    setRestaurantName(name);
    if (result.report) {
      setReport(result.report);
      setPage('lead_capture');
    } else {
      setPage('confirm');
    }
  };

  const handleConfirmComplete = (r: OwnerReport, _exp: string, _internal: Record<string, unknown>) => {
    setReport(r);
    setPage('lead_capture');
  };

  const handleVerified = (verifiedReport: OwnerReport, exp: string) => {
    setReport(verifiedReport);
    setExplanation(exp);
    setPage('results');
  };

  const handleReset = () => {
    setPage('landing');
    setUploadResult(null);
    setSessionId('');
    setReport(null);
    setExplanation('');
    setRestaurantName('Restaurant');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {page === 'landing' && <LandingPage onStart={() => setPage('upload')} />}
      {page === 'upload' && (
        <UploadPage onComplete={handleUploadComplete} onBack={handleReset} />
      )}
      {page === 'confirm' && uploadResult && (
        <ConfirmPage
          uploadResult={uploadResult}
          onComplete={handleConfirmComplete}
          onBack={() => setPage('upload')}
        />
      )}
      {page === 'lead_capture' && report && (
        <LeadCapturePage
          report={report}
          sessionId={sessionId}
          restaurantName={restaurantName}
          onComplete={handleVerified}
          onBack={() => setPage('upload')}
        />
      )}
      {page === 'results' && report && (
        <ResultsPage
          report={report}
          explanation={explanation}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;
