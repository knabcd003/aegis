import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/DashboardLayout';
import { CommandCenter } from '@/components/CommandCenter';
import { SandboxCanvas } from '@/components/SandboxCanvas';
import { MLOpsArena } from '@/components/MLOpsArena';

function App() {
    return (
        <Router>
            <DashboardLayout>
                <Routes>
                    <Route path="/" element={<Navigate to="/command" replace />} />
                    <Route path="/command" element={<CommandCenter />} />
                    <Route path="/lab" element={<SandboxCanvas />} />
                    <Route path="/arena" element={<MLOpsArena />} />
                </Routes>
            </DashboardLayout>
        </Router>
    );
}

export default App;
