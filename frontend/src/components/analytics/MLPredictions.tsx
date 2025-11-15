import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Brain, AlertCircle, Calendar, DollarSign } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import toast from 'react-hot-toast';

interface Prediction {
  date: string;
  predicted_revenue: number;
  confidence_low: number;
  confidence_high: number;
}

interface Insight {
  type: string;
  title: string;
  message: string;
  icon: string;
  priority: string;
}

interface KPIs {
  revenue_30d: number;
  revenue_trend: number;
  conversion_rate: number;
  avg_days_to_sell: number;
  total_views_30d: number;
  total_sales_30d: number;
}

export default function MLPredictions() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [loading, setLoading] = useState(false);
  const [daysAhead, setDaysAhead] = useState(7);

  useEffect(() => {
    loadPredictions();
    loadInsights();
    loadKPIs();
  }, [daysAhead]);

  const loadPredictions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/analytics-ml/predict-revenue?days_ahead=${daysAhead}`, {
        credentials: 'include'
      });
      const data = await response.json();
      if (data.predictions) {
        setPredictions(data.predictions);
      }
    } catch (error) {
      console.error('Failed to load predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadInsights = async () => {
    try {
      const response = await fetch('/api/v1/analytics-ml/insights', {
        credentials: 'include'
      });
      const data = await response.json();
      setInsights(data);
    } catch (error) {
      console.error('Failed to load insights:', error);
    }
  };

  const loadKPIs = async () => {
    try {
      const response = await fetch('/api/v1/analytics-ml/kpis', {
        credentials: 'include'
      });
      const data = await response.json();
      setKpis(data);
    } catch (error) {
      console.error('Failed to load KPIs:', error);
    }
  };

  const totalPredicted = predictions.reduce((sum, p) => sum + p.predicted_revenue, 0);

  return (
    <div className="space-y-6">
      {/* ML Badge */}
      <div className="flex items-center gap-3">
        <Brain className="w-6 h-6 text-violet-400" />
        <h2 className="text-2xl font-bold text-white">ML-Powered Predictions</h2>
        <Badge className="bg-violet-500/20 text-violet-300">
          AI Feature
        </Badge>
      </div>

      {/* KPIs Grid */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Revenue (30d)</p>
                <p className="text-2xl font-bold text-white">{kpis.revenue_30d}€</p>
              </div>
              <div className={`text-right ${kpis.revenue_trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
                <p className="text-sm font-semibold">
                  {kpis.revenue_trend > 0 ? '+' : ''}{kpis.revenue_trend}%
                </p>
                <p className="text-xs text-slate-500">vs last month</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div>
              <p className="text-sm text-slate-400">Conversion Rate</p>
              <p className="text-2xl font-bold text-white">{kpis.conversion_rate}%</p>
              <p className="text-xs text-slate-500">{kpis.total_sales_30d} sales / {kpis.total_views_30d} views</p>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div>
              <p className="text-sm text-slate-400">Avg Time to Sell</p>
              <p className="text-2xl font-bold text-white">{kpis.avg_days_to_sell} days</p>
              <p className="text-xs text-slate-500">Average across all items</p>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Revenue Predictions */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-white">Revenue Forecast</h3>
            <p className="text-sm text-slate-400">ML predictions for next {daysAhead} days</p>
          </div>
          <select
            value={daysAhead}
            onChange={(e) => setDaysAhead(Number(e.target.value))}
            className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:border-violet-500/50"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-8 h-8 border-4 border-violet-500/30 border-t-violet-500 rounded-full mx-auto"
            />
            <p className="text-slate-400 mt-4">Calculating predictions...</p>
          </div>
        ) : predictions.length > 0 ? (
          <>
            {/* Total Predicted */}
            <div className="mb-6 p-4 bg-violet-500/10 border border-violet-500/30 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-violet-300 mb-1">Total Predicted Revenue</p>
                  <p className="text-3xl font-bold text-white">{totalPredicted.toFixed(2)}€</p>
                </div>
                <DollarSign className="w-8 h-8 text-violet-400" />
              </div>
            </div>

            {/* Predictions Chart */}
            <div className="space-y-3">
              {predictions.map((pred, i) => (
                <motion.div
                  key={pred.date}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-4 p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-semibold text-white">
                        {new Date(pred.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    {/* Confidence Range Bar */}
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-violet-500 to-purple-600"
                        style={{ width: `${(pred.predicted_revenue / Math.max(...predictions.map(p => p.predicted_revenue))) * 100}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-white">{pred.predicted_revenue}€</p>
                    <p className="text-xs text-slate-500">
                      {pred.confidence_low}€ - {pred.confidence_high}€
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">Not enough data for predictions yet</p>
            <p className="text-sm text-slate-500 mt-2">Make more sales to unlock ML forecasting</p>
          </div>
        )}
      </GlassCard>

      {/* AI Insights */}
      {insights.length > 0 && (
        <GlassCard className="p-6">
          <h3 className="text-xl font-bold text-white mb-4">🎯 Smart Insights</h3>
          <div className="space-y-3">
            {insights.map((insight, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`p-4 rounded-lg border ${
                  insight.type === 'success'
                    ? 'bg-green-500/10 border-green-500/30'
                    : insight.type === 'warning'
                    ? 'bg-yellow-500/10 border-yellow-500/30'
                    : 'bg-blue-500/10 border-blue-500/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    insight.type === 'success'
                      ? 'bg-green-500/20'
                      : insight.type === 'warning'
                      ? 'bg-yellow-500/20'
                      : 'bg-blue-500/20'
                  }`}>
                    {insight.icon === 'calendar' && <Calendar className="w-5 h-5" />}
                    {insight.icon === 'alert-circle' && <AlertCircle className="w-5 h-5" />}
                    {insight.icon === 'trending-up' && <TrendingUp className="w-5 h-5" />}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white mb-1">{insight.title}</h4>
                    <p className="text-sm text-slate-300">{insight.message}</p>
                  </div>
                  {insight.priority === 'high' && (
                    <Badge className="bg-red-500/20 text-red-300">High Priority</Badge>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
