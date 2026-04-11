import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/DashboardLayout';
import { CommandCenter } from '@/components/CommandCenter';
import { GlassBoxInspector } from '@/components/GlassBoxInspector';
import { MLOpsArena } from '@/components/MLOpsArena';
import { SystemHealth } from '@/components/SystemHealth';
import { PortfolioTracker } from '@/components/PortfolioTracker';
import { SentinelDetail } from '@/components/SentinelDetail';
import { IntakePage } from '@/pages/IntakePage';
import { BudgetDashboard } from '@/components/BudgetDashboard';
import { VersionControl } from '@/components/VersionControl';
import { AuditPage } from '@/components/AuditPage';
import { usePipelineWebSocket } from '@/lib/usePipelineWebSocket';


function App() {
    usePipelineWebSocket();

    return (
        <Router>
            <DashboardLayout>
                <Routes>
                    <Route path="/" element={<Navigate to="/command" replace />} />
                    {/* OBSERVE */}
                    <Route path="/command" element={<CommandCenter />} />
                    <Route path="/glassbox" element={<GlassBoxInspector />} />
                    {/* INTAKE */}
                    <Route path="/intake" element={<IntakePage />} />
                    {/* PORTFOLIO */}
                    <Route path="/portfolio" element={<PortfolioTracker />} />
                    <Route path="/sentinel/:id" element={<SentinelDetail />} />
                    {/* ANALYZE */}
                    <Route path="/arena" element={<MLOpsArena />} />
                    <Route path="/budget" element={<BudgetDashboard />} />
                    <Route path="/audit" element={<AuditPage />} />
                    <Route path="/versions" element={<VersionControl />} />
                    {/* SETTINGS */}
                    <Route path="/health" element={<SystemHealth />} />
                    <Route path="/settings" element={<SystemHealth />} />
                    
                    {/* FALLBACK 404 */}
                    <Route path="*" element={<div className="h-full w-full flex items-center justify-center font-mono text-slate-500 uppercase tracking-widest">404: Navigation Path Not Found</div>} />
                </Routes>
            </DashboardLayout>
        </Router>
    );
}

export default App;
