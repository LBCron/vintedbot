import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar as CalendarIcon, Clock, Zap, TrendingUp, AlertCircle } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import toast from 'react-hot-toast';

interface OptimalTime {
  day_of_week: number;
  day_name: string;
  hour: number;
  score: number;
  avg_views: number;
  conversion_rate: number;
  publication_count: number;
}

interface ScheduledItem {
  id: string;
  draft_id: string;
  scheduled_time: string;
  status: string;
  title: string;
  photos: string[];
  price: number;
}

export default function Scheduling() {
  const [optimalTimes, setOptimalTimes] = useState<OptimalTime[]>([]);
  const [scheduledItems, setScheduledItems] = useState<ScheduledItem[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadOptimalTimes();
    loadScheduledItems();
  }, []);

  const loadOptimalTimes = async () => {
    try {
      const response = await fetch('/api/v1/scheduling/optimal-times', {
        credentials: 'include'
      });
      const data = await response.json();
      setOptimalTimes(data);
    } catch (error) {
      console.error('Failed to load optimal times:', error);
    }
  };

  const loadScheduledItems = async () => {
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 7);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 30);

      const response = await fetch(
        `/api/v1/scheduling/calendar?start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}`,
        { credentials: 'include' }
      );
      const data = await response.json();
      setScheduledItems(data);
    } catch (error) {
      console.error('Failed to load scheduled items:', error);
    }
  };

  const autoSchedule = async (strategy: string) => {
    // This would need draft IDs - for demo purposes
    setLoading(true);
    const loadingToast = toast.loading(`Scheduling with ${strategy} strategy...`);

    try {
      const response = await fetch('/api/v1/scheduling/bulk-schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          draft_ids: [], // Would come from selected drafts
          strategy
        })
      });

      toast.success('✅ Scheduled successfully!', { id: loadingToast });
      loadScheduledItems();
    } catch (error) {
      toast.error('Failed to schedule', { id: loadingToast });
    } finally {
      setLoading(false);
    }
  };

  const cancelSchedule = async (scheduleId: string) => {
    try {
      await fetch(`/api/v1/scheduling/cancel/${scheduleId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      toast.success('Schedule cancelled');
      loadScheduledItems();
    } catch (error) {
      toast.error('Failed to cancel');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <motion.div
        className="p-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
              <CalendarIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
                Scheduling
              </h1>
              <p className="text-slate-400">{scheduledItems.length} items scheduled</p>
            </div>
          </div>

          <div className="flex gap-3">
            <Button icon={Zap} onClick={() => autoSchedule('optimal')} disabled={loading}>
              🎯 Auto-Schedule Optimal
            </Button>
            <Button variant="outline" onClick={() => autoSchedule('spread')} disabled={loading}>
              📊 Spread Evenly
            </Button>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-8 space-y-8 pb-12">
        {/* Optimal Times Bar */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-5 h-5 text-violet-400" />
            <h3 className="text-xl font-bold text-white">⭐ Best Time Slots (ML-Powered)</h3>
          </div>

          {optimalTimes.length > 0 ? (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {optimalTimes.map(time => (
                <div
                  key={`${time.day_of_week}_${time.hour}`}
                  className="flex-shrink-0 p-4 bg-gradient-to-br from-violet-500/20 to-purple-600/20 rounded-xl border border-violet-500/30 min-w-[160px]"
                >
                  <div className="text-white font-semibold mb-2">
                    {time.day_name} {time.hour}:00
                  </div>
                  <div className="space-y-1">
                    <div className="text-sm text-violet-300">
                      Score: {time.score}/100
                    </div>
                    <div className="text-xs text-slate-400">
                      {time.avg_views} avg views
                    </div>
                    <div className="text-xs text-slate-400">
                      {time.conversion_rate}% conversion
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Clock className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">
                Not enough data yet. Publish more items to get ML recommendations!
              </p>
            </div>
          )}
        </GlassCard>

        {/* Scheduled Items */}
        <GlassCard className="p-6">
          <h3 className="text-xl font-bold text-white mb-4">
            Scheduled Publications ({scheduledItems.length})
          </h3>

          {scheduledItems.length > 0 ? (
            <div className="space-y-3">
              {scheduledItems.map(item => (
                <div
                  key={item.id}
                  className="flex items-center gap-4 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  {item.photos && item.photos.length > 0 && (
                    <img
                      src={item.photos[0]}
                      className="w-16 h-16 rounded-lg object-cover"
                      alt={item.title}
                    />
                  )}
                  <div className="flex-1">
                    <h4 className="text-white font-semibold">{item.title}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <Clock className="w-4 h-4 text-slate-400" />
                      <span className="text-sm text-slate-400">
                        {new Date(item.scheduled_time).toLocaleString()}
                      </span>
                      <Badge
                        className={
                          item.status === 'pending'
                            ? 'bg-yellow-500/20 text-yellow-300'
                            : item.status === 'published'
                            ? 'bg-green-500/20 text-green-300'
                            : 'bg-red-500/20 text-red-300'
                        }
                      >
                        {item.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-white">{item.price}€</p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => cancelSchedule(item.id)}
                      disabled={item.status !== 'pending'}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <CalendarIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">
                No scheduled publications
              </h3>
              <p className="text-slate-400 mb-6">
                Schedule your drafts for optimal publication times
              </p>
              <Button onClick={() => window.location.href = '/drafts'}>
                Go to Drafts
              </Button>
            </div>
          )}
        </GlassCard>

        {/* Info Box */}
        <GlassCard className="p-4 bg-blue-500/10 border-blue-500/30">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-300">
              <strong>ML-Powered Scheduling:</strong> Our algorithm analyzes your historical sales data to recommend the best publication times based on views, conversion rates, and day/hour performance.
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
