interface Props {
  onStart: () => void;
}

export function LandingPage({ onStart }: Props) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="max-w-xl text-center">
        <div className="w-14 h-14 bg-amber-500 rounded-xl flex items-center justify-center mx-auto mb-6">
          <span className="text-2xl font-black text-white">86</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
          Where is your restaurant
          <br />
          <span className="text-amber-400">bleeding money?</span>
        </h1>

        <p className="text-gray-400 text-lg mb-8 max-w-md mx-auto">
          Upload your POS exports, labor reports, and refund logs.
          We'll tell you how much you're losing and where.
        </p>

        <button
          onClick={onStart}
          className="px-8 py-3.5 bg-amber-500 hover:bg-amber-400 text-black font-bold rounded-lg text-lg transition-colors cursor-pointer"
        >
          Upload your reports
        </button>

        <div className="mt-12 grid grid-cols-3 gap-6 text-sm text-gray-500">
          <div>
            <div className="text-2xl font-bold text-white mb-1">CSV/XLSX</div>
            <div>Any POS export format</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white mb-1">5 min</div>
            <div>Upload to estimate</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white mb-1">5 checks</div>
            <div>Leakage categories</div>
          </div>
        </div>

        <p className="mt-12 text-xs text-gray-600 max-w-sm mx-auto">
          Works with Toast, Square, Clover, 7shifts, Homebase, or any system
          that exports CSV/XLSX. No integrations needed.
        </p>
      </div>
    </div>
  );
}
