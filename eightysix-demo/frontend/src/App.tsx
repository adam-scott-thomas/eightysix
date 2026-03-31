import { useState } from 'react';
import { LandingPage } from './pages/LandingPage';
import { UploadPage } from './pages/UploadPage';
import { ConfirmPage } from './pages/ConfirmPage';
import { ResultsPage } from './pages/ResultsPage';
import type { UploadResponse, OwnerReport } from './lib/api';

type Page = 'landing' | 'upload' | 'confirm' | 'results';

function App() {
  const [page, setPage] = useState<Page>('landing');
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [report, setReport] = useState<OwnerReport | null>(null);
  const [explanation, setExplanation] = useState('');
  const [internalReport, setInternalReport] = useState<Record<string, unknown> | null>(null);

  const handleUploadComplete = (result: UploadResponse) => {
    setUploadResult(result);
    if (result.report) {
      setReport(result.report);
      setExplanation(result.explanation || '');
      setInternalReport(result.internal || null);
      setPage('results');
    } else {
      setPage('confirm');
    }
  };

  const handleConfirmComplete = (r: OwnerReport, exp: string, internal: Record<string, unknown>) => {
    setReport(r);
    setExplanation(exp);
    setInternalReport(internal);
    setPage('results');
  };

  const handleReset = () => {
    setPage('landing');
    setUploadResult(null);
    setReport(null);
    setExplanation('');
    setInternalReport(null);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {page === 'landing' && <LandingPage onStart={() => setPage('upload')} />}
      {page === 'upload' && <UploadPage onComplete={handleUploadComplete} onBack={handleReset} />}
      {page === 'confirm' && uploadResult && (
        <ConfirmPage
          uploadResult={uploadResult}
          onComplete={handleConfirmComplete}
          onBack={() => setPage('upload')}
        />
      )}
      {page === 'results' && report && (
        <ResultsPage
          report={report}
          explanation={explanation}
          internalReport={internalReport}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;
