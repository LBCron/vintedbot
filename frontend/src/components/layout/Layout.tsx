import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar/'; // Updated to use unified Sidebar
import TopBar from './TopBar';
import MobileBottomNav from './MobileBottomNav';
import Breadcrumbs from './Breadcrumbs';
import { useCommandPalette } from '../../contexts/CommandPaletteContext';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const navigate = useNavigate();
  const { open: openCommandPalette } = useCommandPalette();

  const handleToggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const handleUpload = () => {
    navigate('/upload');
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      {/* Sidebar - Desktop only */}
      <div className="hidden lg:block">
        <Sidebar collapsed={sidebarCollapsed} onToggleCollapse={handleToggleSidebar} />
      </div>

      {/* Main Content Area - Uses CSS variables for consistent spacing */}
      <div
        className="transition-all"
        style={{
          marginLeft: sidebarCollapsed ? 'var(--sidebar-width-collapsed)' : 'var(--sidebar-width)',
          transitionDuration: 'var(--transition-base)',
        }}
      >
        {/* TopBar */}
        <TopBar onOpenCommandPalette={openCommandPalette} />

        {/* Page Content */}
        <main
          className="pb-20 lg:pb-6"
          style={{
            minHeight: 'calc(100vh - var(--navbar-height))',
          }}
        >
          {/* Content Container with Breadcrumbs */}
          <div
            className="px-4 sm:px-6 lg:px-8 mx-auto"
            style={{
              paddingTop: 'var(--spacing-6)',
              paddingBottom: 'var(--spacing-6)',
              maxWidth: 'var(--screen-2xl)',
            }}
          >
            <Breadcrumbs />
            {children}
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav onUpload={handleUpload} />
    </div>
  );
}
