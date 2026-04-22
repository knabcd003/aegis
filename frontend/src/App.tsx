import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { DashboardLayout } from '@/components/DashboardLayout';
import { CommandCenter } from '@/components/CommandCenter';
import { GlassBoxInspector } from '@/components/GlassBoxInspector';
import { MLOpsArena } from '@/components/MLOpsArena';
import { SystemHealth } from '@/components/SystemHealth';
import { PortfolioTracker } from '@/components/PortfolioTracker';
import { SentinelDetail } from '@/components/SentinelDetail';
import { IntakePage } from '@/pages/IntakePage';
import { SetupPage } from '@/pages/SetupPage';
import { BudgetDashboard } from '@/components/BudgetDashboard';
import { VersionControl } from '@/components/VersionControl';
import { AuditPage } from '@/components/AuditPage';
import { usePipelineWebSocket } from '@/lib/usePipelineWebSocket';

function DashboardShell() {
    usePipelineWebSocket();
    return (
        <DashboardLayout>
            <Outlet />
        </DashboardLayout>
    );
}

function App() {
    return (
        <Router>
            <Routes>
                {/* Standalone full-screen — outside DashboardLayout */}
                <Route path="/setup" element={<SetupPage />} />

                {/* All dashboard routes inside the layout shell */}
                <Route element={<DashboardShell />}>
                    <Route path="/" element={<Navigate to="/command" replace />} />
                    <Route path="/command" element={<CommandCenter />} />
                    <Route path="/glassbox" element={<GlassBoxInspector />} />
                    <Route path="/intake" element={<IntakePage />} />
                    <Route path="/portfolio" element={<PortfolioTracker />} />
                    <Route path="/sentinel/:id" element={<SentinelDetail />} />
                    <Route path="/arena" element={<MLOpsArena />} />
                    <Route path="/budget" element={<BudgetDashboard />} />
                    <Route path="/audit" element={<AuditPage />} />
                    <Route path="/versions" element={<VersionControl />} />
                    <Route path="/health" element={<SystemHealth />} />
                    <Route path="/settings" element={<SystemHealth />} />
                    <Route path="*" element={<div className="h-full w-full flex items-center justify-center font-mono text-slate-500 uppercase tracking-widest">404: Navigation Path Not Found</div>} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
