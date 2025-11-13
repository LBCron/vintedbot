import { motion } from 'framer-motion';
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  ChevronRight,
} from 'lucide-react';
import { Badge } from '../../common/Badge';

interface Insight {
  type: 'opportunity' | 'alert' | 'recommendation';
  title: string;
  description: string;
  impact?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const mockInsights: Insight[] = [
  {
    type: 'opportunity',
    title: 'Hoodies performing well',
    description: 'Your hoodies sell 25% faster than average',
    impact: '+€45 avg revenue',
  },
  {
    type: 'opportunity',
    title: 'High demand category',
    description: 'White sneakers are trending this week',
    impact: '+38% views',
  },
  {
    type: 'alert',
    title: 'Listings without views',
    description: '5 items haven\'t received views in 7 days',
    action: {
      label: 'Review',
      onClick: () => {}
    }
  },
  {
    type: 'recommendation',
    title: 'Optimal posting time',
    description: 'Publish on Thursday between 6-8pm for +35% engagement',
    impact: '+35% engagement',
  },
  {
    type: 'recommendation',
    title: 'Price optimization',
    description: 'Lower prices by 10% on slow-moving items',
    impact: '+40% conversion',
  },
];

export default function AIInsights({ limit = 5 }: { limit?: number }) {
  const displayedInsights = mockInsights.slice(0, limit);

  const getInsightIcon = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':
        return <TrendingUp className="w-5 h-5" />;
      case 'alert':
        return <AlertTriangle className="w-5 h-5" />;
      case 'recommendation':
        return <Lightbulb className="w-5 h-5" />;
    }
  };

  const getInsightColor = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':
        return 'text-success-600 dark:text-success-400 bg-success-100 dark:bg-success-900/20';
      case 'alert':
        return 'text-warning-600 dark:text-warning-400 bg-warning-100 dark:bg-warning-900/20';
      case 'recommendation':
        return 'text-primary-600 dark:text-primary-400 bg-primary-100 dark:bg-primary-900/20';
    }
  };

  const getInsightBadgeVariant = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':
        return 'success' as const;
      case 'alert':
        return 'warning' as const;
      case 'recommendation':
        return 'primary' as const;
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            AI Insights
          </h3>
          <Badge variant="primary" size="sm">Beta</Badge>
        </div>
      </div>

      <div className="space-y-4">
        {/* Opportunities */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-success-600 dark:text-success-400" />
            Opportunities
          </h4>
          <div className="space-y-2">
            {displayedInsights
              .filter((i) => i.type === 'opportunity')
              .map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-3 rounded-lg bg-success-50 dark:bg-success-900/10 border border-success-200 dark:border-success-900/20"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-900 dark:text-white">
                        {insight.title}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                        {insight.description}
                      </p>
                      {insight.impact && (
                        <Badge variant="success" size="sm" className="mt-2">
                          {insight.impact}
                        </Badge>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
          </div>
        </div>

        {/* Alerts */}
        {displayedInsights.some((i) => i.type === 'alert') && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning-600 dark:text-warning-400" />
              Alerts
            </h4>
            <div className="space-y-2">
              {displayedInsights
                .filter((i) => i.type === 'alert')
                .map((insight, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: (index + 2) * 0.05 }}
                    className="p-3 rounded-lg bg-warning-50 dark:bg-warning-900/10 border border-warning-200 dark:border-warning-900/20"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="font-medium text-sm text-gray-900 dark:text-white">
                          {insight.title}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                          {insight.description}
                        </p>
                      </div>
                      {insight.action && (
                        <button
                          onClick={insight.action.onClick}
                          className="px-3 py-1.5 text-sm font-medium text-warning-700 dark:text-warning-400 hover:text-warning-800 dark:hover:text-warning-300 transition-colors flex items-center gap-1"
                        >
                          {insight.action.label}
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            Recommendations
          </h4>
          <div className="space-y-2">
            {displayedInsights
              .filter((i) => i.type === 'recommendation')
              .map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: (index + 4) * 0.05 }}
                  className="p-3 rounded-lg bg-primary-50 dark:bg-primary-900/10 border border-primary-200 dark:border-primary-900/20"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-900 dark:text-white">
                        {insight.title}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                        {insight.description}
                      </p>
                      {insight.impact && (
                        <Badge variant="primary" size="sm" className="mt-2">
                          {insight.impact}
                        </Badge>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
          </div>
        </div>
      </div>

      {displayedInsights.length === 0 && (
        <div className="text-center py-8">
          <Sparkles className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            AI is analyzing your data...
          </p>
          <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">
            Insights will appear once we have enough data
          </p>
        </div>
      )}
    </div>
  );
}
