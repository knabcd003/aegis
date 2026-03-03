import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { Dashboard } from './components/Dashboard';
import { AssetTerminal } from './components/AssetTerminal';
import { StrategyConfig } from './components/StrategyConfig';
import { ApiManagement } from './components/ApiManagement';
import { Performance } from './components/Performance';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [currentTicker, setCurrentTicker] = useState<string | null>(null);

  const handleNavChange = (view: string) => {
    setCurrentTicker(null); // Reset deep dive when changing main tabs
    setCurrentView(view);
  };

  const renderContent = () => {
    if (currentTicker) {
      return <AssetTerminal ticker={currentTicker} onBack={() => setCurrentTicker(null)} />;
    }

    switch (currentView) {
      case 'config': return <StrategyConfig />;
      case 'api': return <ApiManagement />;
      case 'performance': return <Performance />;
      default: return <Dashboard onSelectAsset={(ticker: string) => setCurrentTicker(ticker)} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentView={currentView} onViewChange={handleNavChange} />
      <div className="main-content">
        {!currentTicker && <TopBar />}
        {renderContent()}
      </div>
    </div>
  );
}

export default App;
