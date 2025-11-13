import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { motion } from 'framer-motion';

interface BreadcrumbItem {
  label: string;
  path: string;
}

// Map routes to readable labels
const routeLabels: Record<string, string> = {
  '': 'Dashboard',
  'upload': 'Upload',
  'drafts': 'Drafts',
  'publish': 'Publish',
  'analytics': 'Analytics',
  'messages': 'Messages',
  'history': 'History',
  'templates': 'Templates',
  'settings': 'Settings',
  'help': 'Help Center',
  'accounts': 'Accounts',
  'automation': 'Automation',
  'admin': 'Admin',
  'feedback': 'Feedback',
};

export default function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Generate breadcrumb items
  const breadcrumbs: BreadcrumbItem[] = pathnames.map((segment, index) => {
    const path = `/${pathnames.slice(0, index + 1).join('/')}`;
    const label = routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);

    return { label, path };
  });

  // Add home at the beginning if not already there
  if (pathnames.length > 0) {
    breadcrumbs.unshift({ label: 'Dashboard', path: '/' });
  }

  // Don't show breadcrumbs on home page
  if (pathnames.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm mb-6" aria-label="Breadcrumb">
      {breadcrumbs.map((breadcrumb, index) => {
        const isLast = index === breadcrumbs.length - 1;
        const isFirst = index === 0;

        return (
          <motion.div
            key={breadcrumb.path}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center"
          >
            {/* Separator */}
            {!isFirst && (
              <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-600 mx-2" />
            )}

            {/* Breadcrumb item */}
            {isLast ? (
              <span className="font-medium text-gray-900 dark:text-white">
                {breadcrumb.label}
              </span>
            ) : (
              <Link
                to={breadcrumb.path}
                className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              >
                {isFirst && <Home className="w-4 h-4" />}
                <span className="hidden sm:inline">{breadcrumb.label}</span>
              </Link>
            )}
          </motion.div>
        );
      })}
    </nav>
  );
}
