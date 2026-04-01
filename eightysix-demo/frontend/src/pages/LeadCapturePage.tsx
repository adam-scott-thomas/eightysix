import { useState } from 'react';
import { submitLead, verifyEmail, type OwnerReport } from '../lib/api';

interface Props {
  report: OwnerReport;
  sessionId: string;
  restaurantName: string;
  onComplete: (report: OwnerReport, explanation: string) => void;
  onBack: () => void;
}

const CONCERNS = [
  { id: 'labor_costs', label: 'Labor costs too high' },
  { id: 'employee_theft', label: 'Employee theft or fraud' },
  { id: 'food_waste', label: 'Food waste / spoilage' },
  { id: 'refund_abuse', label: 'Too many refunds or voids' },
  { id: 'scheduling', label: 'Scheduling inefficiency' },
  { id: 'menu_pricing', label: 'Menu pricing / margins' },
  { id: 'delivery_fees', label: 'Delivery platform fees' },
  { id: 'inventory', label: 'Inventory shrinkage' },
  { id: 'turnover', label: 'Staff turnover costs' },
];

function formatMoney(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0,
  }).format(n);
}

export function LeadCapturePage({ report, sessionId, restaurantName, onComplete, onBack }: Props) {
  const [step, setStep] = useState<'info' | 'verify'>('info');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const toggle = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const handleSubmitInfo = async () => {
    if (!name.trim() || !email.trim()) {
      setError('Name and email are required.');
      return;
    }
    if (!email.includes('@') || !email.includes('.')) {
      setError('Please enter a valid email.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await submitLead({
        session_id: sessionId,
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        restaurant_name: restaurantName,
        address: address.trim(),
        top_concerns: selected,
        estimated_leakage: report.estimated_annual_leakage,
      });
      setStep('verify');
    } catch (e: any) {
      setError(e.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (code.length !== 6) {
      setError('Please enter the 6-digit code.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const result = await verifyEmail(sessionId, code);
      onComplete(result.report, result.explanation);
    } catch (e: any) {
      setError(e.message || 'Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    setError('');
    try {
      await submitLead({
        session_id: sessionId,
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        restaurant_name: restaurantName,
        address: address.trim(),
        top_concerns: selected,
        estimated_leakage: report.estimated_annual_leakage,
      });
      setError('');
      setCode('');
    } catch (e: any) {
      setError(e.message || 'Failed to resend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-16">
      <div className="max-w-lg w-full">
        <button onClick={onBack} className="text-gray-500 hover:text-white text-sm mb-6 cursor-pointer">
          &larr; Back
        </button>

        {/* The hook — show the big number */}
        <div className="text-center mb-10">
          <div className="text-sm text-gray-400 mb-1">We found an estimated</div>
          <div className="text-5xl font-black text-amber-400 tracking-tight mb-1">
            {formatMoney(report.estimated_annual_leakage)}
          </div>
          <div className="text-sm text-gray-500">in annual leakage</div>
        </div>

        {step === 'info' && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-lg font-bold mb-1">See the full breakdown</h2>
            <p className="text-gray-400 text-sm mb-6">
              Enter your info to unlock the detailed analysis — where the money is going and what to fix first.
            </p>

            <label className="block text-sm font-medium text-gray-300 mb-1">Your name *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Joe Martinez"
              className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-4 focus:outline-none focus:border-amber-500" />

            <label className="block text-sm font-medium text-gray-300 mb-1">Email *</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="joe@restaurant.com"
              className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-4 focus:outline-none focus:border-amber-500" />

            <label className="block text-sm font-medium text-gray-300 mb-1">Phone number</label>
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
              placeholder="(555) 123-4567"
              className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-4 focus:outline-none focus:border-amber-500" />

            <label className="block text-sm font-medium text-gray-300 mb-1">Restaurant address</label>
            <input type="text" value={address} onChange={(e) => setAddress(e.target.value)}
              placeholder="123 Main St, Chicago, IL"
              className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-6 focus:outline-none focus:border-amber-500" />

            <label className="block text-sm font-medium text-gray-300 mb-2">
              What are your top 3 concerns?
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
              {CONCERNS.map((c) => {
                const isSelected = selected.includes(c.id);
                const isDisabled = !isSelected && selected.length >= 3;
                return (
                  <button key={c.id} onClick={() => toggle(c.id)} disabled={isDisabled}
                    className={`px-3 py-2 rounded-lg text-sm text-left transition-colors cursor-pointer ${
                      isSelected ? 'bg-amber-500/20 border border-amber-500 text-amber-300'
                        : isDisabled ? 'bg-gray-900 border border-gray-800 text-gray-600 cursor-not-allowed'
                        : 'bg-gray-950 border border-gray-700 text-gray-300 hover:border-gray-500'
                    }`}>
                    {isSelected && <span className="mr-1.5">&#10003;</span>}
                    {c.label}
                  </button>
                );
              })}
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <button onClick={handleSubmitInfo}
              disabled={loading || !name.trim() || !email.trim()}
              className={`w-full py-3 rounded-lg font-bold text-lg transition-colors cursor-pointer ${
                loading || !name.trim() || !email.trim()
                  ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
                  : 'bg-amber-500 hover:bg-amber-400 text-black'
              }`}>
              {loading ? 'Sending code...' : 'Send verification code'}
            </button>
          </div>
        )}

        {step === 'verify' && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 text-center">
            <h2 className="text-lg font-bold mb-2">Check your email</h2>
            <p className="text-gray-400 text-sm mb-6">
              We sent a 6-digit code to <span className="text-white font-medium">{email}</span>
            </p>

            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="w-48 mx-auto block px-4 py-4 bg-gray-950 border border-gray-700 rounded-xl text-white text-center text-3xl font-mono tracking-[0.5em] placeholder-gray-700 mb-6 focus:outline-none focus:border-amber-500"
            />

            {error && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <button onClick={handleVerify}
              disabled={loading || code.length !== 6}
              className={`w-full py-3 rounded-lg font-bold text-lg transition-colors cursor-pointer ${
                loading || code.length !== 6
                  ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
                  : 'bg-amber-500 hover:bg-amber-400 text-black'
              }`}>
              {loading ? 'Verifying...' : 'Verify and see results'}
            </button>

            <button onClick={handleResend}
              disabled={loading}
              className="mt-3 text-sm text-gray-500 hover:text-white transition-colors cursor-pointer">
              Didn't get it? Resend code
            </button>

            <button onClick={() => { setStep('info'); setError(''); }}
              className="mt-2 block mx-auto text-sm text-gray-600 hover:text-gray-400 transition-colors cursor-pointer">
              Change email
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
