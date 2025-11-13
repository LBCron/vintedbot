import { motion } from 'framer-motion';
import { TrendingUp, Info } from 'lucide-react';
import { Tooltip } from '../../common/Tooltip';

interface HeatmapData {
  day: string;
  hour: number;
  value: number;
  count: number;
}

interface AnalyticsHeatmapProps {
  data?: HeatmapData[];
  metric?: 'views' | 'likes' | 'messages' | 'sales';
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

// Generate realistic mock data if none provided
const generateMockData = (metric: string): HeatmapData[] => {
  const data: HeatmapData[] = [];

  DAYS.forEach((day, dayIndex) => {
    HOURS.forEach((hour) => {
      // Higher activity during specific times
      let baseValue = 0;

      // Weekday vs Weekend patterns
      const isWeekend = dayIndex >= 5;

      if (isWeekend) {
        // Weekend: more activity during day (10am-10pm)
        if (hour >= 10 && hour <= 22) {
          baseValue = 50 + Math.random() * 50;
        } else {
          baseValue = Math.random() * 20;
        }
      } else {
        // Weekday: lunch (12-14) and evening (18-22) peaks
        if ((hour >= 12 && hour <= 14) || (hour >= 18 && hour <= 22)) {
          baseValue = 60 + Math.random() * 40;
        } else if (hour >= 8 && hour <= 18) {
          baseValue = 20 + Math.random() * 30;
        } else {
          baseValue = Math.random() * 15;
        }
      }

      // Add some randomness
      const value = Math.round(baseValue + (Math.random() - 0.5) * 20);
      const count = Math.round(value * (0.5 + Math.random() * 0.5));

      data.push({
        day,
        hour,
        value: Math.max(0, Math.min(100, value)),
        count,
      });
    });
  });

  return data;
};

const getColorIntensity = (value: number): string => {
  if (value === 0) return 'bg-gray-100 dark:bg-gray-800';
  if (value < 20) return 'bg-primary-100 dark:bg-primary-900/20';
  if (value < 40) return 'bg-primary-200 dark:bg-primary-800/40';
  if (value < 60) return 'bg-primary-400 dark:bg-primary-600/60';
  if (value < 80) return 'bg-primary-500 dark:bg-primary-500/80';
  return 'bg-primary-600 dark:bg-primary-400';
};

const getMetricLabel = (metric: string): string => {
  const labels: Record<string, string> = {
    views: 'Views',
    likes: 'Likes',
    messages: 'Messages',
    sales: 'Sales',
  };
  return labels[metric] || 'Activity';
};

const getMetricIcon = (metric: string): string => {
  const icons: Record<string, string> = {
    views: '👁️',
    likes: '❤️',
    messages: '💬',
    sales: '💰',
  };
  return icons[metric] || '📊';
};

export default function AnalyticsHeatmap({
  data,
  metric = 'views',
}: AnalyticsHeatmapProps) {
  const heatmapData = data || generateMockData(metric);

  // Group data by day and hour
  const dataMap = new Map<string, HeatmapData>();
  heatmapData.forEach((item) => {
    const key = `${item.day}-${item.hour}`;
    dataMap.set(key, item);
  });

  // Find peak time
  const maxValue = Math.max(...heatmapData.map((d) => d.value));
  const peakData = heatmapData.find((d) => d.value === maxValue);

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Activity Heatmap
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {getMetricLabel(metric)} by day and hour
            </p>
          </div>
        </div>

        <Tooltip content="Shows when your listings get the most engagement">
          <div className="w-5 h-5 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center cursor-help">
            <Info className="w-3 h-3 text-gray-500 dark:text-gray-400" />
          </div>
        </Tooltip>
      </div>

      {/* Peak Insight */}
      {peakData && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 border border-primary-200 dark:border-primary-800 rounded-lg"
        >
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getMetricIcon(metric)}</span>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                Peak Time: {peakData.day} at {peakData.hour}:00
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {peakData.count} {getMetricLabel(metric).toLowerCase()} during this hour
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Heatmap Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-full">
          {/* Hour Labels */}
          <div className="flex mb-2">
            <div className="w-12 flex-shrink-0" />
            <div className="flex-1 flex">
              {[0, 3, 6, 9, 12, 15, 18, 21].map((hour) => (
                <div
                  key={hour}
                  className="flex-1 text-center"
                  style={{ minWidth: '40px' }}
                >
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {hour}h
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Heatmap Rows */}
          {DAYS.map((day, dayIndex) => (
            <motion.div
              key={day}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: dayIndex * 0.05 }}
              className="flex items-center mb-1"
            >
              {/* Day Label */}
              <div className="w-12 flex-shrink-0">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {day}
                </span>
              </div>

              {/* Hour Cells */}
              <div className="flex-1 flex gap-1">
                {HOURS.map((hour) => {
                  const key = `${day}-${hour}`;
                  const cellData = dataMap.get(key);
                  const value = cellData?.value || 0;
                  const count = cellData?.count || 0;

                  return (
                    <Tooltip
                      key={hour}
                      content={
                        <div className="text-center">
                          <p className="font-medium">
                            {day}, {hour}:00
                          </p>
                          <p className="text-sm">
                            {count} {getMetricLabel(metric).toLowerCase()}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {value}% activity
                          </p>
                        </div>
                      }
                    >
                      <motion.div
                        whileHover={{ scale: 1.2, zIndex: 10 }}
                        className={`flex-1 aspect-square rounded-sm cursor-pointer transition-all ${getColorIntensity(
                          value
                        )}`}
                        style={{ minWidth: '14px', minHeight: '14px' }}
                      />
                    </Tooltip>
                  );
                })}
              </div>
            </motion.div>
          ))}

          {/* Legend */}
          <div className="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <span className="text-xs text-gray-500 dark:text-gray-400">Less</span>
            <div className="flex gap-1">
              {[0, 20, 40, 60, 80, 100].map((value) => (
                <div
                  key={value}
                  className={`w-4 h-4 rounded-sm ${getColorIntensity(value)}`}
                />
              ))}
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">More</span>
          </div>

          {/* Best Times Suggestion */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
              💡 Publishing Tips
            </p>
            <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Weekdays: Best during lunch (12-2pm) and evening (6-10pm)</li>
              <li>• Weekends: More activity throughout the day (10am-10pm)</li>
              <li>• Avoid early morning (1-7am) for immediate engagement</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
