import { motion } from 'framer-motion';
import {
  Upload,
  Edit,
  Trash2,
  Send,
  DollarSign,
  TrendingUp,
  MessageCircle,
  LucideIcon,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface Activity {
  id: string;
  type: 'upload' | 'edit' | 'delete' | 'publish' | 'price_change' | 'status_change' | 'message';
  title: string;
  description: string;
  timestamp: string;
  icon: LucideIcon;
  iconColor: string;
}

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'publish',
    title: 'Draft published',
    description: '"Hoodie Nike" has been published successfully',
    timestamp: '2h ago',
    icon: Send,
    iconColor: 'text-success-600 dark:text-success-400 bg-success-100 dark:bg-success-900/20',
  },
  {
    id: '2',
    type: 'price_change',
    title: 'Price updated',
    description: '"Jordan 1 High" price changed from €120 to €110',
    timestamp: '5h ago',
    icon: DollarSign,
    iconColor: 'text-warning-600 dark:text-warning-400 bg-warning-100 dark:bg-warning-900/20',
  },
  {
    id: '3',
    type: 'upload',
    title: 'Photos uploaded',
    description: '15 photos uploaded successfully',
    timestamp: 'Yesterday',
    icon: Upload,
    iconColor: 'text-primary-600 dark:text-primary-400 bg-primary-100 dark:bg-primary-900/20',
  },
  {
    id: '4',
    type: 'message',
    title: 'New message',
    description: 'Marie sent you a message about "Supreme T-shirt"',
    timestamp: 'Yesterday',
    icon: MessageCircle,
    iconColor: 'text-info-600 dark:text-info-400 bg-info-100 dark:bg-info-900/20',
  },
  {
    id: '5',
    type: 'edit',
    title: 'Draft updated',
    description: '"Nike Dunk Low" description improved',
    timestamp: '2 days ago',
    icon: Edit,
    iconColor: 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800',
  },
];

export default function ActivityFeed({ limit = 5 }: { limit?: number }) {
  const displayedActivities = mockActivities.slice(0, limit);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-900/20 flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-primary-600 dark:text-primary-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Activity
          </h3>
        </div>

        <Link
          to="/history"
          className="text-sm text-primary-600 dark:text-primary-400 hover:underline inline-flex items-center gap-1"
        >
          View all
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="space-y-3">
        {displayedActivities.map((activity, index) => (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
          >
            {/* Icon */}
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${activity.iconColor}`}>
              <activity.icon className="w-5 h-5" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-gray-900 dark:text-white">
                {activity.title}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {activity.description}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {activity.timestamp}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {displayedActivities.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            No recent activity
          </p>
        </div>
      )}
    </div>
  );
}
