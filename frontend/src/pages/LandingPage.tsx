import { useState } from 'react';
import {
  Users,
  DollarSign,
  AlertTriangle,
  ChefHat,
  Timer,
  Fingerprint,
  ArrowRight,
  BarChart3,
  Shield,
  Settings,
  Gauge,
  Camera,
  Plug,
  SlidersHorizontal,
  LayoutDashboard,
  Zap,
  CheckCircle,
  Building2,
  Headset,
  UserCog,
  ChevronRight,
  Star,
  ExternalLink,
} from 'lucide-react';

interface LandingPageProps {
  onEnterApp: () => void;
}

/* ------------------------------------------------------------------ */
/*  Utility: section wrapper                                           */
/* ------------------------------------------------------------------ */

function Section({
  children,
  className = '',
  id,
  dark = false,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
  dark?: boolean;
}) {
  return (
    <section
      id={id}
      className={`px-5 sm:px-8 lg:px-16 py-16 sm:py-24 ${dark ? 'bg-gray-950 text-gray-100' : 'bg-white text-gray-900'} ${className}`}
    >
      <div className="max-w-6xl mx-auto">{children}</div>
    </section>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-mono text-[11px] tracking-[0.2em] uppercase text-amber-600 font-bold mb-3">
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Pricing cards                                                      */
/* ------------------------------------------------------------------ */

function PricingCards() {
  const [showCustom, setShowCustom] = useState(false);
  const [customAmount, setCustomAmount] = useState('');

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 max-w-3xl gap-4">
        {/* Single Location */}
        <div className="border border-gray-200 rounded-lg p-6 hover:border-amber-400 hover:shadow-md transition-all">
          <div className="font-mono text-[10px] tracking-[0.15em] uppercase text-gray-400 font-bold mb-2">
            Single Location
          </div>
          <div className="flex items-baseline gap-1 mb-1">
            <span className="text-3xl font-extrabold text-gray-900">$5,000</span>
            <span className="text-sm text-gray-400">setup</span>
          </div>
          <p className="text-xs text-gray-500 mb-2">One location, full deployment, prove the ROI.</p>
          <div className="text-xs text-gray-600 mb-5 space-y-1">
            <p><span className="font-semibold">$1,500/mo</span> for first 3 months</p>
            <p><span className="font-semibold">$2,500/mo</span> after onboarding</p>
          </div>
          <ul className="space-y-2 mb-6">
            {[
              'Single location deployment',
              'POS & labor provider integration',
              'All 6 quick-win rules live',
              'Dashboard, alerts & recommendations',
              'Hands-on setup & configuration',
              'Dedicated onboarding support',
            ].map((f) => (
              <li key={f} className="flex items-start gap-2 text-xs text-gray-600">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                {f}
              </li>
            ))}
          </ul>
          <a
            href="mailto:adam@adamscottthomas.com?subject=EightySix%20-%20Single%20Location"
            className="block w-full text-center px-4 py-2.5 border border-gray-300 text-gray-700 font-bold text-sm rounded hover:bg-gray-50 transition-colors"
          >
            Get Started
          </a>
        </div>

        {/* Multi-Location */}
        <div className="border-2 border-amber-400 rounded-lg p-6 relative shadow-sm">
          <div className="absolute -top-2.5 left-4 bg-amber-500 text-white font-mono text-[10px] tracking-wider uppercase font-bold px-2.5 py-0.5 rounded">
            <Star className="w-3 h-3 inline -mt-0.5 mr-0.5" /> Multi-location
          </div>
          <div className="font-mono text-[10px] tracking-[0.15em] uppercase text-amber-600 font-bold mb-2">
            Multi-Location
          </div>
          <div className="flex items-baseline gap-1 mb-1">
            <span className="text-3xl font-extrabold text-gray-900">$10,000</span>
            <span className="text-sm text-gray-400">setup</span>
          </div>
          <p className="text-xs text-gray-500 mb-2">Full rollout across your locations.</p>
          <div className="text-xs text-gray-600 mb-5 space-y-1">
            <p><span className="font-semibold">$5,000/mo</span> for up to 3 stores</p>
            <p><span className="font-semibold">$2,500/store</span> after that</p>
          </div>
          <ul className="space-y-2 mb-6">
            {[
              'Up to 3 locations included',
              'Additional stores at $2,500/store',
              'Full rules engine & integrity review',
              'Live POS & labor provider sync',
              'Custom threshold tuning per location',
              'Priority support & SLA',
              'API access & executive rollups',
            ].map((f) => (
              <li key={f} className="flex items-start gap-2 text-xs text-gray-600">
                <CheckCircle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
                {f}
              </li>
            ))}
          </ul>
          <a
            href="mailto:adam@adamscottthomas.com?subject=EightySix%20-%20Multi-Location"
            className="block w-full text-center px-4 py-2.5 bg-amber-500 text-white font-bold text-sm rounded hover:bg-amber-600 transition-colors"
          >
            Book a Demo
          </a>
        </div>
      </div>

      {/* Hidden custom amount — triple-click the footer text to reveal */}
      <div className="mt-6 flex items-center gap-2">
        <p
          className="text-xs text-gray-400 font-mono cursor-default select-none"
          onDoubleClick={() => setShowCustom((v) => !v)}
        >
          Setup + onboarding included in all plans.
        </p>
        {showCustom && (
          <button
            onClick={() => setShowCustom(false)}
            className="text-[10px] text-gray-300 hover:text-gray-500"
          >
            hide
          </button>
        )}
      </div>

      {showCustom && (
        <div className="mt-3 max-w-xs">
          <label className="block text-[10px] font-mono text-gray-400 uppercase tracking-wider mb-1">
            <Settings className="w-3 h-3 inline mr-1" />
            Custom quote amount
          </label>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">$</span>
            <input
              type="text"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              placeholder="Enter amount"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none bg-white font-mono"
            />
          </div>
          {customAmount && (
            <a
              href={`mailto:adam@adamscottthomas.com?subject=EightySix%20-%20Custom%20Quote&body=Custom%20amount%3A%20%24${encodeURIComponent(customAmount)}`}
              className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white font-bold text-xs rounded hover:bg-gray-800 transition-colors"
            >
              Send Quote for ${customAmount}
              <ArrowRight className="w-3 h-3" />
            </a>
          )}
        </div>
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function LandingPage({ onEnterApp }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-white">
      {/* ========== NAV ========== */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 lg:px-16 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-amber-500 rounded flex items-center justify-center">
              <ChefHat className="w-4 h-4 text-white" />
            </div>
            <span className="font-mono font-bold text-sm tracking-tight text-gray-900">
              EIGHTYSIX
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-6 text-xs font-medium text-gray-500">
            <a href="#features" className="hover:text-gray-900 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-gray-900 transition-colors">How it works</a>
            <a href="#pricing" className="hover:text-gray-900 transition-colors">Pricing</a>
            <button
              onClick={onEnterApp}
              className="px-3.5 py-1.5 bg-gray-900 text-white rounded font-semibold hover:bg-gray-800 transition-colors cursor-pointer"
            >
              Dashboard
            </button>
          </div>
          <button
            onClick={onEnterApp}
            className="sm:hidden px-3 py-1.5 bg-gray-900 text-white rounded text-xs font-semibold cursor-pointer"
          >
            Dashboard
          </button>
        </div>
      </nav>

      {/* ========== HERO ========== */}
      <section className="pt-28 sm:pt-36 pb-16 sm:pb-24 px-5 sm:px-8 lg:px-16 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="max-w-3xl">
            <div className="font-mono text-[11px] tracking-[0.25em] uppercase text-amber-600 font-bold mb-5 flex items-center gap-2">
              <span className="w-8 h-px bg-amber-500" />
              Restaurant Operations Intelligence
            </div>

            <h1 className="text-3xl sm:text-5xl lg:text-[3.5rem] font-extrabold leading-[1.1] tracking-tight text-gray-950 mb-6">
              Run your restaurant tighter
              <br />
              <span className="text-amber-600">without ripping out your POS.</span>
            </h1>

            <p className="text-base sm:text-lg text-gray-600 leading-relaxed mb-4 max-w-2xl">
              See staffing issues, labor leakage, refund spikes, rush bottlenecks,
              and suspicious punch-ins before they drain profit.
            </p>

            <p className="text-sm text-gray-500 leading-relaxed mb-8 max-w-2xl">
              Plug in the systems you already have, fill gaps with manual input when
              needed, and get a live dashboard built around the fastest wins in
              restaurant ops.
            </p>

            <div className="flex flex-wrap gap-3">
              <a
                href="mailto:adam@adamscottthomas.com?subject=EightySix%20Demo"
                className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 text-white font-bold text-sm rounded hover:bg-amber-600 transition-colors"
              >
                Book a Demo
                <ArrowRight className="w-4 h-4" />
              </a>
              <button
                onClick={onEnterApp}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 text-white font-bold text-sm rounded hover:bg-gray-800 transition-colors cursor-pointer"
              >
                See the Dashboard
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Trust line */}
          <div className="mt-14 pt-8 border-t border-gray-200">
            <p className="font-mono text-xs text-gray-400 tracking-wide">
              Built for operators who want useful answers now, not a six-month integration project.
            </p>
          </div>
        </div>
      </section>

      {/* ========== SIX MONEY STORIES ========== */}
      <Section id="features">
        <SectionLabel>The first six money stories it solves</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-10">
          Six problems. Real answers. Every shift.
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              icon: Users,
              title: 'Overstaffed or understaffed?',
              body: 'Compares order volume to active labor in rolling windows and tells you when to add or cut.',
              color: 'bg-blue-50 text-blue-700 border-blue-200',
              iconBg: 'bg-blue-100',
            },
            {
              icon: DollarSign,
              title: 'Is labor cost creeping too high?',
              body: 'Estimates labor spend in real time and compares it to revenue so you can correct mid-shift.',
              color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
              iconBg: 'bg-emerald-100',
            },
            {
              icon: AlertTriangle,
              title: 'Are refunds and comps leaking profit?',
              body: 'Tracks refund rate, total loss, and concentration by employee when available.',
              color: 'bg-red-50 text-red-700 border-red-200',
              iconBg: 'bg-red-100',
            },
            {
              icon: BarChart3,
              title: 'Is the menu helping or hurting?',
              body: 'Classifies items by volume and margin — stars, workhorses, puzzles, and dogs.',
              color: 'bg-purple-50 text-purple-700 border-purple-200',
              iconBg: 'bg-purple-100',
            },
            {
              icon: Timer,
              title: 'Is a rush turning into a bottleneck?',
              body: 'Watches order velocity and prep time together, flags buildup before service quality slips.',
              color: 'bg-amber-50 text-amber-700 border-amber-200',
              iconBg: 'bg-amber-100',
            },
            {
              icon: Fingerprint,
              title: 'Suspicious punch-in?',
              body: 'Scores punch integrity using geofence, device fingerprint, and staff-count discrepancies.',
              color: 'bg-gray-50 text-gray-700 border-gray-200',
              iconBg: 'bg-gray-200',
            },
          ].map((card) => (
            <div
              key={card.title}
              className={`${card.color} border rounded-lg p-5 transition-shadow hover:shadow-md`}
            >
              <div className={`${card.iconBg} w-9 h-9 rounded flex items-center justify-center mb-3`}>
                <card.icon className="w-4.5 h-4.5" />
              </div>
              <h3 className="font-bold text-sm mb-1.5">{card.title}</h3>
              <p className="text-xs leading-relaxed opacity-80">{card.body}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* ========== HOW IT WORKS ========== */}
      <Section id="how-it-works" dark>
        <SectionLabel>How it works</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-12">
          Five steps from chaos to clarity.
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-6 sm:gap-4">
          {[
            { step: '01', icon: Plug, title: 'Connect what you already have', body: 'Start with POS and labor data, or even just one. Manual input fills the gaps.' },
            { step: '02', icon: SlidersHorizontal, title: 'Normalize the chaos', body: 'Orders, employees, shifts, refunds, and observations mapped into one clean model.' },
            { step: '03', icon: Zap, title: 'Run the rules', body: 'Labor efficiency, refund rate, backlog risk, menu mix, staffing pressure, integrity risk.' },
            { step: '04', icon: LayoutDashboard, title: 'Get the dashboard', body: 'Revenue, staffing, throughput, leakage, flags, alerts, and recommendations in one view.' },
            { step: '05', icon: CheckCircle, title: 'Take action', body: 'Every recommendation explains what, why, confidence, and estimated impact.' },
          ].map((item) => (
            <div key={item.step} className="relative">
              <div className="font-mono text-[40px] font-black text-gray-800 leading-none mb-3 tabular-nums">
                {item.step}
              </div>
              <div className="w-8 h-8 rounded bg-amber-500/20 flex items-center justify-center mb-3">
                <item.icon className="w-4 h-4 text-amber-400" />
              </div>
              <h3 className="font-bold text-sm mb-1.5 text-gray-100">{item.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed">{item.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800">
          <p className="font-mono text-xs text-gray-500 italic">
            Because apparently "just trust the vibes" is not a serious operating strategy.
          </p>
        </div>
      </Section>

      {/* ========== FEATURES GRID ========== */}
      <Section>
        <SectionLabel>Features built for actual operators</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-10">
          Not decorative. Not theoretical. Wired.
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-gray-200 border border-gray-200 rounded-lg overflow-hidden">
          {[
            { icon: Gauge, title: 'Real-time staffing pressure', body: 'See when active staff count no longer matches order volume. Get clear add/reduce/rebalance recommendations.' },
            { icon: DollarSign, title: 'Labor leakage tracking', body: 'Watch labor cost estimate, SPLH, and labor cost ratio throughout the day — not a week later.' },
            { icon: AlertTriangle, title: 'Refund & comp monitoring', body: 'Track total loss from refunds, comps, and voids. Flag spikes and suspicious employee concentration.' },
            { icon: Timer, title: 'Rush & bottleneck alerts', body: 'Detect rising prep times, backlog risk, and throughput pressure before service breaks.' },
            { icon: BarChart3, title: 'Menu performance intelligence', body: 'Top sellers, bottom sellers, workhorses, attach-rate opportunities, and menu cleanup candidates.' },
            { icon: Fingerprint, title: 'Punch integrity review', body: 'Flag possible remote punch-ins via geofence, unknown devices, and staff-count discrepancies.' },
            { icon: Shield, title: 'Readiness scoring', body: 'Know whether your dashboard is fully ready, partial, or missing key data. No mystery. No fake confidence.' },
            { icon: Camera, title: 'Snapshot-based dashboard', body: 'Every recompute produces a current-state snapshot — clean source of truth, auditable history.' },
          ].map((f) => (
            <div key={f.title} className="bg-white p-5 flex flex-col">
              <f.icon className="w-5 h-5 text-amber-600 mb-3" />
              <h3 className="font-bold text-sm mb-1.5 text-gray-900">{f.title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* ========== WHY DIFFERENT ========== */}
      <Section dark>
        <SectionLabel>Why this is different</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-10">
          Not another dashboard full of decorative nonsense.
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            {
              title: 'The logic is wired.',
              body: 'Thresholds exist. Derivations are defined. Recommendations are connected to actual alerts and evidence. Not vibes.',
            },
            {
              title: 'Built for partial adoption.',
              body: 'Most restaurant tech assumes clean data and perfect integrations. Cute theory. This works when real life is messy.',
            },
            {
              title: 'Production-shaped from the start.',
              body: 'Real database models. Real rules engine. Real API. Real snapshot contract. The only stubbed part is the source adapters.',
            },
            {
              title: 'Debuggable.',
              body: 'Synchronous, deterministic recompute pipeline designed to be understood. No black box worker maze.',
            },
          ].map((d) => (
            <div key={d.title} className="border border-gray-800 rounded-lg p-5 hover:border-amber-500/40 transition-colors">
              <h3 className="font-bold text-sm text-amber-400 mb-2">{d.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed">{d.body}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* ========== FOR WHO ========== */}
      <Section>
        <SectionLabel>Who it's for</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-10">
          Owners. Operators. Managers.
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              icon: Building2,
              role: 'For Owners',
              headline: 'Protect margin without babysitting every shift.',
              body: 'Get a live read on labor, leakage, and operational drag so small losses stop stacking into ugly month-end surprises.',
            },
            {
              icon: Headset,
              role: 'For Operators',
              headline: 'Know what is happening right now.',
              body: 'See whether staffing is balanced, prep is slipping, refunds are spiking, or a punch needs review — all in one place.',
            },
            {
              icon: UserCog,
              role: 'For Managers',
              headline: 'Get actionable recommendations, not noise.',
              body: 'Each recommendation includes what to do, why it matters, confidence, and estimated impact. Move fast without guessing.',
            },
          ].map((p) => (
            <div
              key={p.role}
              className="border border-gray-200 rounded-lg p-6 hover:border-amber-400 hover:shadow-md transition-all"
            >
              <div className="w-10 h-10 rounded bg-gray-100 flex items-center justify-center mb-4">
                <p.icon className="w-5 h-5 text-gray-600" />
              </div>
              <div className="font-mono text-[10px] tracking-[0.15em] uppercase text-amber-600 font-bold mb-2">
                {p.role}
              </div>
              <h3 className="font-bold text-base text-gray-900 mb-2">{p.headline}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{p.body}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* ========== DEMO SCENARIOS ========== */}
      <Section dark>
        <SectionLabel>Demo the full lifecycle</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-4">
          Load a scenario. Recompute. See the state change.
        </h2>
        <p className="text-sm text-gray-400 mb-8 max-w-2xl">
          That means you can show exactly how the system behaves when the restaurant
          is healthy, strained, leaking, or getting weird. Which, to be fair, covers
          most restaurants.
        </p>

        <div className="flex flex-wrap gap-2">
          {[
            { name: 'Normal day', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
            { name: 'Dinner rush', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
            { name: 'Refund spike', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
            { name: 'Suspicious punch', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
            { name: 'Understaffed', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
            { name: 'Overstaffed', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
            { name: 'Ghost shift', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
            { name: 'Low-margin mix', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
          ].map((s) => (
            <span
              key={s.name}
              className={`${s.color} border font-mono text-xs font-bold px-3 py-1.5 rounded`}
            >
              {s.name}
            </span>
          ))}
        </div>

        <div className="mt-8">
          <button
            onClick={onEnterApp}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-500 text-white font-bold text-sm rounded hover:bg-amber-600 transition-colors cursor-pointer"
          >
            Try the Demo
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </Section>

      {/* ========== PRICING ========== */}
      <Section id="pricing">
        <SectionLabel>Pricing</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-3">
          Built for fast proof, then rollout.
        </h2>
        <p className="text-sm text-gray-500 mb-10 max-w-xl">
          Start with one location and the six quickest wins. Expand once the value is obvious.
        </p>

        <PricingCards />
      </Section>

      {/* ========== INTEGRATION ========== */}
      <Section dark>
        <SectionLabel>Integrations</SectionLabel>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-3">
          Start with stubs. Swap in live providers later.
        </h2>
        <p className="text-sm text-gray-400 mb-8 max-w-2xl">
          The platform is built around provider interfaces. Prove the dashboard,
          validate the workflow, then connect live sources when ready.
        </p>

        <div className="flex flex-wrap gap-3">
          {['Toast', 'Square', 'Clover', '7shifts', 'Gusto', 'Homebase'].map((p) => (
            <span
              key={p}
              className="font-mono text-xs font-bold px-4 py-2 border border-gray-700 rounded text-gray-300 hover:border-amber-500/50 hover:text-amber-400 transition-colors"
            >
              {p}
            </span>
          ))}
        </div>
      </Section>

      {/* ========== FINAL CTA ========== */}
      <section className="px-5 sm:px-8 lg:px-16 py-20 sm:py-28 bg-gray-50">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-gray-950 mb-4">
            See where your margin is leaking.
          </h2>
          <p className="text-base text-gray-500 mb-8 max-w-lg mx-auto">
            Stop guessing during service. Start with what you already have.
            No full rip-and-replace. No giant implementation circus.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <a
              href="mailto:adam@adamscottthomas.com?subject=EightySix%20Demo"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-amber-500 text-white font-bold text-sm rounded hover:bg-amber-600 transition-colors"
            >
              Book a Demo
              <ArrowRight className="w-4 h-4" />
            </a>
            <button
              onClick={onEnterApp}
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-gray-900 text-white font-bold text-sm rounded hover:bg-gray-800 transition-colors cursor-pointer"
            >
              See the Dashboard
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ========== FOOTER ========== */}
      <footer className="px-5 sm:px-8 lg:px-16 py-8 bg-gray-950 text-gray-500 border-t border-gray-800">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 bg-amber-500 rounded flex items-center justify-center">
              <ChefHat className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-mono text-xs font-bold text-gray-400">EIGHTYSIX</span>
          </div>
          <div className="flex items-center gap-5 text-xs">
            <a href="mailto:adam@adamscottthomas.com" className="hover:text-gray-300 transition-colors">
              Contact
            </a>
            <a href="https://github.com/adam-scott-thomas/eightysix" target="_blank" rel="noopener noreferrer" className="hover:text-gray-300 transition-colors">
              GitHub
            </a>
            <span className="text-gray-700">&copy; 2026 Maelstrom LLC</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
