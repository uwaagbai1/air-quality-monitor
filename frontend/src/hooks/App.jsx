import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import ModernDashboard from './components/ModernDashboard';

/**
 * Main Application Component
 * Toggle between dark theme (original) and light theme (modern)
 */
export default function App() {
  const [useModernTheme, setUseModernTheme] = useState(true);

  // Toggle with keyboard shortcut (Ctrl+T)
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        setUseModernTheme(!useModernTheme);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [useModernTheme]);

  if (useModernTheme) {
    return <ModernDashboard />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Dashboard />
    </div>
  );
}
