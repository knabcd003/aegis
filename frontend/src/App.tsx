import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/Shell/Layout';
import { SetupPage } from '@/pages/SetupPage';
import { IntakePage } from '@/pages/IntakePage';
import { IntakePageV10 } from '@/pages/IntakePageV10';
import { LLMIntakePage } from '@/pages/LLMIntakePage';

// Placeholder pages — will be replaced with real implementations
function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-headline text-4xl font-light tracking-tight text-on-surface">{title}</h2>
        <p className="text-[#8e8e88] mt-2 max-w-2xl leading-relaxed">{description}</p>
      </div>
      <div className="bg-surface-container rounded-xl border border-white/5 p-12 flex flex-col items-center justify-center min-h-[400px]">
        <span
          className="material-symbols-outlined text-[48px] text-[#8e8e88]/30 mb-4"
          style={{ fontVariationSettings: "'wght' 200" }}
        >
          construction
        </span>
        <p className="text-[#8e8e88] text-sm italic font-headline">Under Construction</p>
        <p className="text-[#8e8e88]/60 text-[0.6875rem] mt-1">This page will be built next.</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          {/* OBSERVE */}
          <Route path="/" element={<PlaceholderPage title="Mission Control" description="Live feed of pipeline activity, pending signals, and deployed sentinels." />} />
          <Route path="/portfolio" element={<PlaceholderPage title="Portfolio Tracker" description="NAV charts, positions, and trade history across all deployed sentinels." />} />
          <Route path="/health" element={<PlaceholderPage title="System Health" description="Connector status, provider health, and pre-flight checks." />} />

          {/* PIPELINE */}
          <Route path="/pipeline" element={<PlaceholderPage title="Pipeline Map" description="Live topology of the autonomous reasoning pipeline." />} />
          <Route path="/components" element={<PlaceholderPage title="Component Library" description="Verified Component Library — browse, inspect, and manage pipeline building blocks." />} />
          <Route path="/sandbox" element={<PlaceholderPage title="Sandbox" description="Active sentinel incubation, iteration ledger, and promotion pipeline." />} />

          {/* ANALYZE */}
          <Route path="/glass-box" element={<PlaceholderPage title="Glass Box" description="Progressive disclosure audit trail — inspect what happened and why." />} />
          <Route path="/arena" element={<PlaceholderPage title="Arena" description="MLflow run leaderboard, strategy comparison, and performance metrics." />} />
          <Route path="/debates" element={<PlaceholderPage title="Debate Theater" description="Adversarial audit replays — see how the AI argued for and against each signal." />} />
          <Route path="/budget" element={<PlaceholderPage title="Budget Dashboard" description="Token quotas, provider spend tracking, and session quality distribution." />} />

          {/* SETTINGS */}
          <Route path="/intake" element={<IntakePage />} />
          <Route path="/intake-v10" element={<IntakePageV10 />} />
          <Route path="/llm-intake" element={<LLMIntakePage />} />
          <Route path="/settings" element={<SetupPage />} />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
