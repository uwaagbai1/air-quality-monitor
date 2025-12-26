import React, { useState } from 'react';
import { 
  Home, 
  LayoutDashboard, 
  Bell, 
  Settings, 
  HelpCircle,
  ChevronDown,
  Search,
  Wind,
  Cpu,
  Activity,
  FileText,
  Menu,
  X,
  Github
} from 'lucide-react';

export default function Sidebar({ activeView, setActiveView, alertCount = 0 }) {
  const [dashboardOpen, setDashboardOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  const menuItems = [
    { id: 'home', label: 'Home', icon: Home },
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: LayoutDashboard,
      submenu: [
        { id: 'overview', label: 'Overview' },
        { id: 'analytics', label: 'Analytics' },
      ]
    },
    { id: 'models', label: 'ML Models', icon: Cpu },
    { id: 'forecast', label: 'Forecast', icon: Activity },
    { id: 'alerts', label: 'Notifications', icon: Bell, badge: alertCount > 0 ? alertCount : null },
    { id: 'reports', label: 'Reports', icon: FileText },
  ];

  const bottomItems = [
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'help', label: 'Help & Docs', icon: HelpCircle },
  ];

  const NavItem = ({ item, isSubmenu = false }) => {
    const Icon = item.icon;
    const isActive = activeView === item.id || 
      (item.submenu?.some(sub => sub.id === activeView));
    const hasSubmenu = item.submenu && item.submenu.length > 0;

    return (
      <button
        onClick={() => {
          if (hasSubmenu) {
            setDashboardOpen(!dashboardOpen);
          } else {
            setActiveView(item.id);
            setMobileOpen(false);
          }
        }}
        className={`
          w-full flex items-center justify-between px-3 py-2.5 rounded-xl
          transition-all duration-200 group relative
          ${isSubmenu ? 'ml-6' : ''}
          ${isActive 
            ? 'bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400' 
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
          }
        `}
      >
        {isActive && !isSubmenu && (
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-emerald-500 rounded-r-full" />
        )}
        
        <div className="flex items-center gap-3">
          {Icon && (
            <div className={`
              p-1.5 rounded-lg transition-colors
              ${isActive 
                ? 'text-emerald-600 dark:text-emerald-400' 
                : 'text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300'
              }
            `}>
              <Icon className="w-[18px] h-[18px]" />
            </div>
          )}
          {!Icon && isSubmenu && (
            <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
          )}
          <span className="font-medium text-sm">{item.label}</span>
        </div>
        
        <div className="flex items-center gap-2">
          {item.badge && (
            <span className="flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-bold bg-red-500 text-white rounded-full animate-pulse">
              {item.badge}
            </span>
          )}
          {hasSubmenu && (
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${dashboardOpen ? 'rotate-180' : ''}`} />
          )}
        </div>
      </button>
    );
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="relative">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <Wind className="w-5 h-5 text-white" />
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white dark:border-gray-900 animate-pulse" />
        </div>
        <div>
          <h1 className="font-bold text-gray-900 dark:text-white text-lg tracking-tight">AirQualityMonitor</h1>
          {/* <p className="text-xs text-gray-500 dark:text-gray-400 font-medium"></p> */}
        </div>
      </div>

      {/* Search */}
      <div className="px-4 pb-4">
        <div className="relative flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-12 py-2.5 bg-gray-100 dark:bg-gray-800 border-0 rounded-xl text-sm
                       placeholder-gray-400 dark:placeholder-gray-500 text-gray-900 dark:text-white
                       focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
          />
          <kbd className="absolute right-3 hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium text-gray-400 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        <p className="px-3 py-2 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          Main Menu
        </p>
        {menuItems.map((item) => (
          <div key={item.id}>
            <NavItem item={item} />
            {item.submenu && dashboardOpen && (
              <div className="mt-1 space-y-1">
                {item.submenu.map((subItem) => (
                  <NavItem key={subItem.id} item={subItem} isSubmenu />
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="px-3 py-4 border-t border-gray-200 dark:border-gray-700 space-y-1">
        <p className="px-3 py-2 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          Settings
        </p>
        {bottomItems.map((item) => (
          <NavItem key={item.id} item={item} />
        ))}
      </div>

      {/* User profile */}
      <div className="px-4 py-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
            UA
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">Uwa Uwa Agbai</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">MSc Student • Newcastle</p>
          </div>
          <a 
            href="https://github.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <Github className="w-4 h-4 text-gray-400" />
          </a>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700"
      >
        {mobileOpen ? <X className="w-5 h-5 text-gray-600 dark:text-gray-300" /> : <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-72 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col
        transform transition-transform duration-300 shadow-2xl lg:shadow-none
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <SidebarContent />
      </aside>
    </>
  );
}
