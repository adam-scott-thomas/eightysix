import { useState } from 'react';
import { submitLead, type OwnerReport } from '../lib/api';

interface Props {
  report: OwnerReport;
  restaurantName: string;
  onComplete: () => void;
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
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

export function LeadCapturePage({ report, restaurantName, onComplete, onBack }: Props) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const toggle = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const handleSubmit = async () => {
    if (!name.trim() || !email.trim()) {
      setError('Name and email are required.');
      return;
    }
    if (!email.includes('@')) {
      setError('Please enter a valid email.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await submitLead({
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        restaurant_name: restaurantName,
        address: address.trim(),
        top_concerns: selected,
        estimated_leakage: report.estimated_annual_leakage,
      });
      onComplete();
    } catch (e: any) {
      setError(e.message || 'Something went wrong.');
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

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-lg font-bold mb-1">See the full breakdown</h2>
          <p className="text-gray-400 text-sm mb-6">
            Enter your info to unlock the detailed analysis — where the money is going and what to fix first.
          </p>

          {/* Name */}
          <label className="block text-sm font-medium text-gray-300 mb-1">Your name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Joe Martinez"
            className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-4 focus:outline-none focus:border-amber-500"
          />

          {/* Email */}
          <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="joe@restaurant.com"
            className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-4 focus:outline-none focus:border-amber-500"
          />

          {/* Phone */}
          <label className="block text-sm font-medium text-gray-300 mb-1">Phone number</label>
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="(555) 123-4567"
            className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-4 focus:outline-none focus:border-amber-500"
          />

          {/* Address */}
          <label className="block text-sm font-medium text-gray-300 mb-1">Restaurant address</label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="123 Main St, Chicago, IL"
            className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-6 focus:outline-none focus:border-amber-500"
          />

          {/* Top 3 concerns */}
          <label className="block text-sm font-medium text-gray-300 mb-2">
            What are your top 3 concerns?
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
            {CONCERNS.map((c) => {
              const isSelected = selected.includes(c.id);
              const isDisabled = !isSelected && selected.length >= 3;
              return (
                <button
                  key={c.id}
                  onClick={() => toggle(c.id)}
                  disabled={isDisabled}
                  className={`px-3 py-2 rounded-lg text-sm text-left transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-amber-500/20 border border-amber-500 text-amber-300'
                      : isDisabled
                      ? 'bg-gray-900 border border-gray-800 text-gray-600 cursor-not-allowed'
                      : 'bg-gray-950 border border-gray-700 text-gray-300 hover:border-gray-500'
                  }`}
                >
                  {isSelected && <span className="mr-1.5">&#10003;</span>}
                  {c.label}
                </button>
              );
            })}
          </div>
          {selected.length > 0 && (
            <p className="text-xs text-gray-500 mb-4">{selected.length}/3 selected</p>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading || !name.trim() || !email.trim()}
            className={`w-full py-3 rounded-lg font-bold text-lg transition-colors cursor-pointer ${
              loading || !name.trim() || !email.trim()
                ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
                : 'bg-amber-500 hover:bg-amber-400 text-black'
            }`}
          >
            {loading ? 'Submitting...' : 'Show my full breakdown'}
          </button>

          <p className="mt-3 text-xs text-gray-600 text-center">
            No spam. We'll only reach out about your results.
          </p>
        </div>
      </div>
    </div>
  );
}
