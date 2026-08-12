import React, { useState } from 'react';
import { 
  Search,
  Bell,
  Settings,
  User,
  Zap,
  Command,
  HelpCircle,
  Moon,
  Sun,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { useUIState, useSystemData } from '../lib/store';

const Header: React.FC = () => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { theme, setTheme, notifications } = useUIState();
  const { user } = useSystemData();
  
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const unreadNotifications = notifications.filter(n => !n.read).length;

  return (
    <header className="h-14 bg-[#111111] border-b border-[#333333] flex items-center justify-between px-6">
      {/* Left Section - Search */}
      <div className="flex items-center space-x-4 flex-1">
        <div className="relative max-w-md w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search projects, docs, or type a command..."
            className="w-full pl-10 pr-4 py-2 bg-[#1a1a1a] border border-[#333333] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#00ff88] focus:ring-1 focus:ring-[#00ff88] transition-colors"
          />
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
            <Command className="w-3 h-3 text-gray-500" />
            <span className="text-xs text-gray-500">K</span>
          </div>
        </div>
      </div>

      {/* Center Section - Breadcrumb */}
      <div className="flex items-center space-x-2 text-sm text-gray-400">
        <span>InfraNest</span>
        <span>/</span>
        <span className="text-white">Workspace</span>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center space-x-3">
        {/* Quick Actions */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-2 hover:bg-[#222222] rounded-lg transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-gray-400 hover:text-white" />
            ) : (
              <Moon className="w-4 h-4 text-gray-400 hover:text-white" />
            )}
          </button>
          
          <button
            onClick={toggleFullscreen}
            className="p-2 hover:bg-[#222222] rounded-lg transition-colors"
            title="Toggle fullscreen"
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4 text-gray-400 hover:text-white" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-400 hover:text-white" />
            )}
          </button>

          <button 
            className="p-2 hover:bg-[#222222] rounded-lg transition-colors" 
            title="Help & Documentation"
          >
            <HelpCircle className="w-4 h-4 text-gray-400 hover:text-white" />
          </button>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-[#333333]"></div>

        {/* Notifications */}
        <button className="relative p-2 hover:bg-[#222222] rounded-lg transition-colors">
          <Bell className="w-4 h-4 text-gray-400 hover:text-white" />
          {unreadNotifications > 0 && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#ff4444] rounded-full flex items-center justify-center">
              <span className="text-xs text-white font-bold">{unreadNotifications}</span>
            </div>
          )}
        </button>

        {/* AI Assistant */}
        <button className="flex items-center space-x-2 px-3 py-1.5 bg-gradient-to-r from-[#00ff88]/20 to-[#00ccff]/20 border border-[#00ff88]/30 rounded-lg hover:from-[#00ff88]/30 hover:to-[#00ccff]/30 transition-all">
          <Zap className="w-4 h-4 text-[#00ff88]" />
          <span className="text-sm text-[#00ff88] font-medium">AI</span>
        </button>

        {/* Settings */}
        <button className="p-2 hover:bg-[#222222] rounded-lg transition-colors">
          <Settings className="w-4 h-4 text-gray-400 hover:text-white" />
        </button>

        {/* User Profile */}
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-[#00ff88] to-[#00ccff] rounded-full flex items-center justify-center">
            {user?.avatar ? (
              <img src={user.avatar} alt={user.name} className="w-full h-full rounded-full" />
            ) : (
              <User className="w-4 h-4 text-black" />
            )}
          </div>
          <div className="hidden md:block">
            <div className="text-sm text-white font-medium">
              {user?.name || 'Developer'}
            </div>
            <div className="text-xs text-gray-400">
              {user?.plan ? `${user.plan.charAt(0).toUpperCase() + user.plan.slice(1)} Plan` : 'Free Plan'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;