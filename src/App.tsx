import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Home from './pages/Home';
import PromptToDSL from './pages/PromptToDSL';
import DSLBuilder from './pages/DSLBuilder';
import CodeGenerator from './pages/CodeGenerator';
import Deploy from './pages/Deploy';
import Dashboard from './pages/Dashboard';
import { api } from './lib/api';
import { useSystemData } from './lib/store';
import './App.css';

function App() {
  const setApiStatus = useSystemData((state) => state.setApiStatus);

  useEffect(() => {
    let cancelled = false;

    const checkHealth = async () => {
      try {
        await api.health();
        if (!cancelled) setApiStatus('online');
      } catch {
        if (!cancelled) setApiStatus('offline');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [setApiStatus]);

  return (
    <Router>
      <div className="min-h-screen bg-[#0a0a0a] text-white flex">
        {/* Sidebar */}
        <Sidebar />
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <Header />
          
          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <div className="h-full">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/prompt" element={<PromptToDSL />} />
                <Route path="/builder" element={<DSLBuilder />} />
                <Route path="/generate" element={<CodeGenerator />} />
                <Route path="/deploy" element={<Deploy />} />
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </div>
          </main>
        </div>
        
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1a1a1a',
              color: '#ffffff',
              border: '1px solid #333333',
              borderRadius: '8px',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '14px',
            },
            success: {
              iconTheme: {
                primary: '#00ff88',
                secondary: '#000000',
              },
            },
            error: {
              iconTheme: {
                primary: '#ff4444',
                secondary: '#000000',
              },
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;