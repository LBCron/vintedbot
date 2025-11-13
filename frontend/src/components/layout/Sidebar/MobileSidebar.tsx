/**
 * Mobile Sidebar Component (Drawer)
 * Responsive drawer variant of the sidebar for mobile devices
 *
 * Features:
 * - Slide-in animation from left
 * - Backdrop overlay
 * - Auto-closes on navigation
 * - Touch-optimized sizing
 * - Same navigation structure as desktop
 */

import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { Badge } from '../../common/Badge';
import { mainNavItems, secondaryNavItems, adminNavItem, SUPER_ADMIN_EMAIL } from './navItems';
import { MobileSidebarProps } from './types';

export default function MobileSidebar({ isOpen, onClose }: MobileSidebarProps) {
  const location = useLocation();
  const { user } = useAuth();

  const isSuperAdmin = user?.email.toLowerCase() === SUPER_ADMIN_EMAIL.toLowerCase();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleLinkClick = () => {
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 z-40 md:hidden"
            style={{
              backgroundColor: 'var(--overlay)',
              backdropFilter: 'blur(4px)',
            }}
          />

          {/* Sidebar Drawer */}
          <motion.aside
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{
              duration: 0.3,
              ease: [0.4, 0, 0.2, 1]
            }}
            className="fixed top-0 left-0 bottom-0 w-72 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 z-50 flex flex-col md:hidden"
            style={{
              boxShadow: 'var(--shadow-2xl)',
            }}
          >
            {/* Header with Logo and Close Button */}
            <div
              className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800"
              style={{
                padding: 'var(--spacing-4)',
                minHeight: 'var(--navbar-height)',
              }}
            >
              <div className="flex items-center gap-3">
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
                <h1
                  className="text-xl font-bold"
                  style={{
                    background: 'var(--gradient-primary)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  VintedBot
                </h1>
              </div>

              <motion.button
                onClick={onClose}
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                style={{
                  transition: 'all var(--transition-fast)',
                }}
              >
                <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </motion.button>
            </div>

            {/* Navigation */}
            <nav
              className="flex-1 overflow-y-auto scrollbar-thin"
              style={{
                padding: 'var(--spacing-4) var(--spacing-3)',
              }}
            >
              {/* Main Navigation Items */}
              <div className="space-y-1">
                {mainNavItems.map((item, index) => {
                  const active = isActive(item.path);
                  const Icon = item.icon;

                  return (
                    <motion.div
                      key={item.path}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                    >
                      <Link
                        to={item.path}
                        onClick={handleLinkClick}
                        className={`flex items-center gap-3 rounded-lg transition-all relative ${
                          active
                            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 font-medium'
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
                            layoutId="activeMobileNav"
                            className="absolute left-0 top-0 bottom-0 w-1 bg-primary-500 rounded-r"
                            transition={{
                              type: 'spring',
                              stiffness: 500,
                              damping: 30
                            }}
                          />
                        )}

                        <motion.div
                          animate={active ? { scale: 1.1 } : { scale: 1 }}
                          transition={{ duration: 0.2 }}
                        >
                          <Icon
                            className="flex-shrink-0"
                            style={{
                              width: '1.25rem',
                              height: '1.25rem',
                            }}
                          />
                        </motion.div>

                        <span className="flex-1">{item.label}</span>

                        {item.badge && (
                          <Badge variant={item.badgeVariant || 'default'} size="sm">
                            {item.badge}
                          </Badge>
                        )}
                      </Link>
                    </motion.div>
                  );
                })}
              </div>

              {/* Divider */}
              <div
                className="border-t border-gray-200 dark:border-gray-800"
                style={{ margin: 'var(--spacing-6) 0' }}
              />

              {/* Secondary Navigation Items */}
              <div className="space-y-1">
                {secondaryNavItems.map((item, index) => {
                  const active = isActive(item.path);
                  const Icon = item.icon;

                  return (
                    <motion.div
                      key={item.path}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: (mainNavItems.length + index) * 0.03 }}
                    >
                      <Link
                        to={item.path}
                        onClick={handleLinkClick}
                        className={`flex items-center gap-3 rounded-lg transition-all ${
                          active
                            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 font-medium'
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
                          }}
                        />
                        <span className="flex-1">{item.label}</span>
                      </Link>
                    </motion.div>
                  );
                })}

                {/* Super Admin Panel */}
                {isSuperAdmin && (
                  <>
                    <div
                      className="border-t border-gray-300 dark:border-gray-700"
                      style={{ margin: 'var(--spacing-4) 0' }}
                    />
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: (mainNavItems.length + secondaryNavItems.length) * 0.03 }}
                    >
                      <Link
                        to={adminNavItem.path}
                        onClick={handleLinkClick}
                        className={`flex items-center gap-3 rounded-lg transition-all ${
                          isActive(adminNavItem.path)
                            ? 'bg-error-50 dark:bg-error-900/20 text-error-700 dark:text-error-400 font-semibold'
                            : 'text-error-600 dark:text-error-400 hover:bg-error-50 dark:hover:bg-error-900/20 font-semibold'
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
                        <span className="flex-1">{adminNavItem.label}</span>
                      </Link>
                    </motion.div>
                  </>
                )}
              </div>
            </nav>

            {/* Profile Section */}
            <div
              className="border-t border-gray-200 dark:border-gray-800"
              style={{ padding: 'var(--spacing-4)' }}
            >
              <Link
                to="/settings"
                onClick={handleLinkClick}
                className="flex items-center gap-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
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

                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                    {user?.email || 'user@example.com'}
                  </p>
                </div>
              </Link>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
