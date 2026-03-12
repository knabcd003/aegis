import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/DashboardLayout';
import { CommandCenter } from '@/components/CommandCenter';
import { SandboxCanvas } from '@/components/SandboxCanvas';
import { MLOpsArena } from '@/components/MLOpsArena';
import { CreateWizard } from '@/components/CreateWizard';
import { SystemHealth } from '@/components/SystemHealth';
import { EngineLibrary } from '@/components/EngineLibrary';
import { AuditPage } from '@/components/AuditPage';
import { VersionControl } from '@/components/VersionControl';
import { PortfolioTracker } from '@/components/PortfolioTracker';

function App() {
    return (
        <Router>
            <DashboardLayout>
                <Routes>
                    <Route path="/" element={<Navigate to="/command" replace />} />
                    {/* Observe */}
                    <Route path="/command" element={<CommandCenter />} />
                    <Route path="/portfolio" element={<PortfolioTracker />} />
                    <Route path="/health" element={<SystemHealth />} />
                    {/* Build */}
                    <Route path="/create" element={<CreateWizard />} />
                    <Route path="/lab" element={<SandboxCanvas />} />
                    <Route path="/engines" element={<EngineLibrary />} />
                    {/* Analyze */}
                    <Route path="/arena" element={<MLOpsArena />} />
                    <Route path="/audit" element={<AuditPage />} />
                    <Route path="/versions" element={<VersionControl />} />
                </Routes>
            </DashboardLayout>
        </Router>
    );
}

export default App;
