import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/DashboardLayout';
import { CommandCenter } from '@/components/CommandCenter';
import { GlassBoxInspector } from '@/components/GlassBoxInspector';
import { MLOpsArena } from '@/components/MLOpsArena';
import { SystemHealth } from '@/components/SystemHealth';
import { PortfolioTracker } from '@/components/PortfolioTracker';
import { SentinelDetail } from '@/components/SentinelDetail';
import { usePipelineWebSocket } from '@/lib/usePipelineWebSocket';
import { SystemHealth } from '@/components/SystemHealth';
// Removed dead routes as per V7 deletion


function App() {
    usePipelineWebSocket();

    return (
        <Router>
            <DashboardLayout>
                <Routes>
                    <Route path="/" element={<Navigate to="/command" replace />} />
                    {/* OBSERVE */}
                    <Route path="/command" element={<CommandCenter />} />
                    {/* INTAKE (Pending Step 5 components) */}
                    {/* PORTFOLIO */}
                    <Route path="/portfolio" element={<PortfolioTracker />} />
                    <Route path="/sentinel/:id" element={<SentinelDetail />} />
                    {/* ANALYZE */}
                    <Route path="/analyze" element={<MLOpsArena />} />
                    {/* SETTINGS */}
                    <Route path="/settings" element={<SystemHealth />} />
                </Routes>
            </DashboardLayout>
        </Router>
    );
}

export default App;
