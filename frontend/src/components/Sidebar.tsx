import React, { useEffect, useState } from 'react';

interface AgentStatus {
    name: string;
    status: string;
}

interface SidebarProps {
    currentView: string;
    onViewChange: (view: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
    const [agents, setAgents] = useState<AgentStatus[]>([]);

    useEffect(() => {
        // Fetch initial status from API
        fetch('http://localhost:8000/api/agents/status')
            .then(res => res.json())
            .then(data => setAgents(data))
            .catch(err => console.error("Error fetching agent status:", err));
    }, []);

    return (
        <aside className="sidebar">
            <div className="brand">
                <div className="brand-dot"></div>
                AEGIS <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>v4.2</span>
            </div>

            <div className="nav-section">
                <div className="nav-title">CORE SYSTEMS</div>
                <ul style={{ listStyle: 'none' }}>
                    {agents.length > 0 ? agents.map(agent => (
                        <li className="nav-item" key={agent.name}>
                            <div className="nav-item-left">
                                <div className={`status-dot ${agent.status === 'IDLE' ? 'idle' : 'active'}`} />
                                <span>{agent.name}</span>
                            </div>
                            <div className={`status-badge ${agent.status === 'IDLE' ? 'idle' : 'active'}`}>
                                {agent.status}
                            </div>
                        </li>
                    )) : (
                        <li className="nav-item text-muted">Waiting for uplink...</li>
                    )}
                </ul>
            </div>

            <div className="nav-section">
                <div className="nav-title">OPERATIONS</div>
                <ul style={{ listStyle: 'none' }}>
                    <li className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`} onClick={() => onViewChange('dashboard')}>Live Orders</li>
                    <li className={`nav-item ${currentView === 'sandbox' ? 'active' : ''}`} onClick={() => onViewChange('sandbox')}>Sandbox</li>
                    <li className={`nav-item ${currentView === 'config' ? 'active' : ''}`} onClick={() => onViewChange('config')}>Strategy Config</li>
                    <li className={`nav-item ${currentView === 'api' ? 'active' : ''}`} onClick={() => onViewChange('api')}>API Management</li>
                    <li className={`nav-item ${currentView === 'performance' ? 'active' : ''}`} onClick={() => onViewChange('performance')}>Performance</li>
                </ul>
            </div>

            <div style={{ marginTop: 'auto', padding: '24px', borderTop: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--bg-card)' }}></div>
                    <div>
                        <div style={{ fontSize: '12px', fontWeight: 600 }}>Admin Console</div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Uptime: 142h 12m</div>
                    </div>
                </div>
            </div>
        </aside>
    );
};
