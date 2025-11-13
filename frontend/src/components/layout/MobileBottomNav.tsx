import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  FileText,
  Plus,
  MessageCircle,
  BarChart3,
  LucideIcon,
} from 'lucide-react';
import { Badge } from '../common/Badge';

interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  badge?: number;
}

const navItems: NavItem[] = [
  { label: 'Home', path: '/', icon: LayoutDashboard },
  { label: 'Drafts', path: '/drafts', icon: FileText },
  { label: 'Messages', path: '/messages', icon: MessageCircle, badge: 3 },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
];

interface MobileBottomNavProps {
  onUpload?: () => void;
}

export default function MobileBottomNav({ onUpload }: MobileBottomNavProps) {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 pb-safe">
      <div className="flex items-center justify-around h-16 px-2">
        {/* First two items */}
        {navItems.slice(0, 2).map((item) => {
          const active = isActive(item.path);
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              className="relative flex flex-col items-center justify-center flex-1 h-full"
            >
              <motion.div
                whileTap={{ scale: 0.9 }}
                className={`relative flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                  active
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                {/* Active indicator */}
                {active && (
                  <motion.div
                    layoutId="mobileActiveNav"
                    className="absolute inset-0 bg-primary-50 dark:bg-primary-900/20 rounded-lg"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}

                <Icon className={`w-6 h-6 relative z-10 ${active ? 'text-primary-600 dark:text-primary-400' : ''}`} />

                <span className={`text-xs font-medium relative z-10 ${active ? 'text-primary-600 dark:text-primary-400' : ''}`}>
                  {item.label}
                </span>

                {/* Badge */}
                {item.badge && (
                  <span className="absolute top-1 right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-error-500 text-white text-[10px] font-bold rounded-full px-1">
                    {item.badge > 9 ? '9+' : item.badge}
                  </span>
                )}
              </motion.div>
            </Link>
          );
        })}

        {/* Central FAB (Upload) */}
        <div className="flex-1 flex items-center justify-center">
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onUpload}
            className="relative -mt-8 w-14 h-14 bg-gradient-to-br from-primary-500 to-purple-500 rounded-full shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center"
          >
            <Plus className="w-7 h-7 text-white" />

            {/* Pulse effect */}
            <span className="absolute inset-0 rounded-full bg-primary-500 animate-ping opacity-20" />
          </motion.button>
        </div>

        {/* Last two items */}
        {navItems.slice(2, 4).map((item) => {
          const active = isActive(item.path);
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              className="relative flex flex-col items-center justify-center flex-1 h-full"
            >
              <motion.div
                whileTap={{ scale: 0.9 }}
                className={`relative flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                  active
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                {/* Active indicator */}
                {active && (
                  <motion.div
                    layoutId="mobileActiveNav"
                    className="absolute inset-0 bg-primary-50 dark:bg-primary-900/20 rounded-lg"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}

                <Icon className={`w-6 h-6 relative z-10 ${active ? 'text-primary-600 dark:text-primary-400' : ''}`} />

                <span className={`text-xs font-medium relative z-10 ${active ? 'text-primary-600 dark:text-primary-400' : ''}`}>
                  {item.label}
                </span>

                {/* Badge */}
                {item.badge && (
                  <span className="absolute top-1 right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-error-500 text-white text-[10px] font-bold rounded-full px-1">
                    {item.badge > 9 ? '9+' : item.badge}
                  </span>
                )}
              </motion.div>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
