/**
 * Unified Sidebar Component (Desktop)
 * Combines the best features from all previous Sidebar implementations
 *
 * Features:
 * - Collapsible with smooth animations
 * - Active state with layoutId animation
 * - Badge support with variants
 * - Tooltips in collapsed state
 * - Profile section
 * - Super admin access
 * - Uses CSS variables from design system
 * - Dark mode support
 */

import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { Badge } from '../../common/Badge';
import { mainNavItems, secondaryNavItems, adminNavItem, SUPER_ADMIN_EMAIL } from './navItems';
import { SidebarProps } from './types';

export default function Sidebar({ collapsed = false, onToggleCollapse }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuth();

  const isSuperAdmin = user?.email.toLowerCase() === SUPER_ADMIN_EMAIL.toLowerCase();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 'var(--sidebar-width-collapsed)' : 'var(--sidebar-width)' }}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1] // ease-in-out from design system
      }}
      className="fixed left-0 top-0 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col z-40"
      style={{
        boxShadow: 'var(--shadow-sm)'
      }}
    >
      {/* Logo Header */}
      <Link
        to="/"
        className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-800"
        style={{
          padding: 'var(--spacing-6)',
          minHeight: 'var(--navbar-height)'
        }}
      >
        <div
          className="flex-shrink-0 flex items-center justify-center rounded-lg"
          style={{
            width: '2.5rem',
            height: '2.5rem',
            background: 'var(--gradient-primary)',
          }}
        >
          <span className="text-white font-bold text-xl">V</span>
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <h1
                className="text-xl font-bold whitespace-nowrap"
                style={{
                  background: 'var(--gradient-primary)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                VintedBot
              </h1>
            </motion.div>
          )}
        </AnimatePresence>
      </Link>

      {/* Main Navigation */}
      <nav
        className="flex-1 overflow-y-auto scrollbar-thin"
        style={{
          padding: 'var(--spacing-6) var(--spacing-3)',
        }}
      >
        <div className="space-y-1">
          {mainNavItems.map((item) => {
            const active = isActive(item.path);
            const Icon = item.icon;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 rounded-lg transition-all group relative ${
                  active
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
                style={{
                  padding: 'var(--spacing-3)',
                  transition: 'all var(--transition-fast)',
                }}
              >
                {/* Active Indicator */}
                {active && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute left-0 top-0 bottom-0 w-1 bg-primary-500 rounded-r"
                    transition={{
                      type: 'spring',
                      stiffness: 500,
                      damping: 30
                    }}
                  />
                )}

                {/* Icon */}
                <Icon
                  className="flex-shrink-0"
                  style={{
                    width: '1.25rem',
                    height: '1.25rem',
                    color: active ? 'var(--primary-600)' : undefined,
                  }}
                />

                {/* Label */}
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="font-medium whitespace-nowrap overflow-hidden"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {/* Badge */}
                {item.badge && !collapsed && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="ml-auto"
                  >
                    <Badge variant={item.badgeVariant || 'default'} size="sm">
                      {item.badge}
                    </Badge>
                  </motion.div>
                )}

                {/* Tooltip for collapsed state */}
                {collapsed && (
                  <div
                    className="absolute left-full ml-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50"
                    style={{
                      boxShadow: 'var(--shadow-lg)',
                    }}
                  >
                    {item.label}
                    {item.badge && (
                      <span
                        className="ml-2 px-2 py-0.5 bg-primary-500 rounded-full text-xs"
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}
              </Link>
            );
          })}
        </div>

        {/* Divider */}
        <div
          className="border-t border-gray-200 dark:border-gray-800"
          style={{ margin: 'var(--spacing-6) 0' }}
        />

        {/* Secondary Navigation */}
        <div className="space-y-1">
          {secondaryNavItems.map((item) => {
            const active = isActive(item.path);
            const Icon = item.icon;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 rounded-lg transition-all group relative ${
                  active
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
                style={{
                  padding: 'var(--spacing-3)',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <Icon
                  className="flex-shrink-0"
                  style={{
                    width: '1.25rem',
                    height: '1.25rem',
                    color: active ? 'var(--primary-600)' : undefined,
                  }}
                />

                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="font-medium whitespace-nowrap overflow-hidden"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {collapsed && (
                  <div
                    className="absolute left-full ml-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50"
                    style={{
                      boxShadow: 'var(--shadow-lg)',
                    }}
                  >
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}

          {/* Super Admin Panel */}
          {isSuperAdmin && (
            <>
              <div
                className="border-t border-gray-300 dark:border-gray-700"
                style={{ margin: 'var(--spacing-4) 0' }}
              />
              <Link
                to={adminNavItem.path}
                className={`flex items-center gap-3 rounded-lg transition-all group relative ${
                  isActive(adminNavItem.path)
                    ? 'bg-error-50 dark:bg-error-900/20 text-error-700 dark:text-error-400'
                    : 'text-error-600 dark:text-error-400 hover:bg-error-50 dark:hover:bg-error-900/20'
                }`}
                style={{
                  padding: 'var(--spacing-3)',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <adminNavItem.icon
                  className="flex-shrink-0"
                  style={{
                    width: '1.25rem',
                    height: '1.25rem',
                  }}
                />

                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="font-semibold whitespace-nowrap overflow-hidden"
                    >
                      {adminNavItem.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {collapsed && (
                  <div
                    className="absolute left-full ml-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50"
                    style={{
                      boxShadow: 'var(--shadow-lg)',
                    }}
                  >
                    {adminNavItem.label}
                  </div>
                )}
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Profile Section */}
      <div
        className="border-t border-gray-200 dark:border-gray-800"
        style={{ padding: 'var(--spacing-3)' }}
      >
        <Link
          to="/settings"
          className="flex items-center gap-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group relative"
          style={{
            padding: 'var(--spacing-3)',
            transition: 'all var(--transition-fast)',
          }}
        >
          <div
            className="flex-shrink-0 rounded-full flex items-center justify-center text-white font-semibold"
            style={{
              width: '2.5rem',
              height: '2.5rem',
              background: 'linear-gradient(135deg, var(--primary-500) 0%, #8b5cf6 100%)',
            }}
          >
            {user?.email?.[0].toUpperCase() || 'U'}
          </div>

          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
                className="flex-1 min-w-0 overflow-hidden"
              >
                <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                  {user?.name || 'User'}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {user?.email || 'user@example.com'}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {collapsed && (
            <div
              className="absolute left-full ml-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50"
              style={{
                boxShadow: 'var(--shadow-lg)',
              }}
            >
              <p className="font-medium">{user?.name || 'User'}</p>
              <p className="text-xs opacity-75">{user?.email || 'user@example.com'}</p>
            </div>
          )}
        </Link>
      </div>

      {/* Collapse Toggle Button */}
      {onToggleCollapse && (
        <button
          onClick={onToggleCollapse}
          className="absolute -right-3 w-6 h-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          style={{
            top: '5rem',
            boxShadow: 'var(--shadow-md)',
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          )}
        </button>
      )}
    </motion.aside>
  );
}
