import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Terminal,
  MessageSquare,
  Settings,
  Code,
  Rocket,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  Database,
  Globe,
  Shield,
  Activity
} from 'lucide-react';
import { useUIState, useSystemData } from '../lib/store';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { sidebarCollapsed, setSidebarCollapsed } = useUIState();
  const { systemStatus } = useSystemData();
  
  const navItems = [
    { 
      path: '/', 
      label: 'Home', 
      icon: Terminal,
      description: 'Start your journey'
    },
    { 
      path: '/prompt', 
      label: 'AI Prompt', 
      icon: MessageSquare,
      description: 'Describe your backend'
    },
    { 
      path: '/builder', 
      label: 'DSL Builder', 
      icon: Settings,
      description: 'Visual configuration'
    },
    { 
      path: '/generate', 
      label: 'Code Gen', 
      icon: Code,
      description: 'Generate production code'
    },
    { 
      path: '/deploy', 
      label: 'Deploy', 
      icon: Rocket,
      description: 'Ship to production'
    },
    { 
      path: '/dashboard', 
      label: 'Monitor', 
      icon: BarChart3,
      description: 'Track performance'
    }
  ];

  const quickActions = [
    { icon: GitBranch, label: 'Git Sync', color: 'text-orange-400', action: () => console.log('Git sync') },
    { icon: Database, label: 'Database', color: 'text-blue-400', action: () => console.log('Database') },
    { icon: Globe, label: 'API Docs', color: 'text-green-400', action: () => console.log('API docs') },
    { icon: Shield, label: 'Security', color: 'text-purple-400', action: () => console.log('Security') }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'connected':
      case 'active':
        return 'text-[#00ff88]';
      case 'degraded':
      case 'maintenance':
        return 'text-[#ffaa00]';
      case 'offline':
      case 'disconnected':
      case 'error':
      case 'inactive':
        return 'text-[#ff4444]';
      default:
        return 'text-gray-400';
    }
  };
  
  return (
    <div className={`bg-[#111111] border-r border-[#333333] flex flex-col transition-all duration-300 ${
      sidebarCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Logo Section */}
      <div className="p-4 border-b border-[#333333]">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="relative">
                <img 
                  src="/assets/logo.svg" 
                  alt="InfraNest" 
                  className="w-8 h-8"
                />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#00ff88] rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-[#00ff88] to-[#00ccff] bg-clip-text text-transparent">
                  InfraNest
                </h1>
                <p className="text-xs text-gray-400 font-mono">v2.0.0-beta</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 hover:bg-[#222222] rounded transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group relative flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/20'
                    : 'text-gray-300 hover:text-white hover:bg-[#222222]'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-[#00ff88]' : 'text-gray-400 group-hover:text-white'}`} />
                {!sidebarCollapsed && (
                  <div className="ml-3 flex-1">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-gray-500 group-hover:text-gray-400">
                      {item.description}
                    </div>
                  </div>
                )}
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00ff88] rounded-r"></div>
                )}
                
                {/* Tooltip for collapsed state */}
                {sidebarCollapsed && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-[#222222] text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}
        </div>

        {/* Quick Actions */}
        {!sidebarCollapsed && (
          <div className="mt-8">
            <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Quick Actions
            </h3>
            <div className="space-y-1">
              {quickActions.map((action, index) => {
                const Icon = action.icon;
                return (
                  <button
                    key={index}
                    onClick={action.action}
                    className="w-full flex items-center px-3 py-2 text-gray-400 hover:text-white hover:bg-[#222222] rounded-lg transition-colors"
                  >
                    <Icon className={`w-4 h-4 ${action.color}`} />
                    <span className="ml-3 text-sm">{action.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </nav>

      {/* Status Footer */}
      <div className="p-4 border-t border-[#333333]">
        {!sidebarCollapsed ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className={`w-4 h-4 ${getStatusColor(systemStatus.api)}`} />
                <span className="text-sm text-gray-300">System Status</span>
              </div>
              <div className={`w-2 h-2 rounded-full ${
                systemStatus.api === 'online' ? 'bg-[#00ff88] animate-pulse' : 'bg-[#ff4444]'
              }`}></div>
            </div>
            <div className="text-xs text-gray-500 font-mono">
              API: {systemStatus.api} • DB: {systemStatus.database}
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <Activity className={`w-5 h-5 ${getStatusColor(systemStatus.api)}`} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;