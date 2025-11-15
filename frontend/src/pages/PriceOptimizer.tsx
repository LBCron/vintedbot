import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, TrendingUp, TrendingDown, Zap, AlertCircle } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import toast from 'react-hot-toast';

interface PriceSuggestion {
  draft_id: string;
  title: string;
  current_price: number;
  suggested_price: number;
  difference: number;
  difference_percent: number;
  reason: string;
  confidence: number;
  strategy: string;
}

export default function PriceOptimizer() {
  const [selectedDrafts, setSelectedDrafts] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<PriceSuggestion[]>([]);
  const [strategy, setStrategy] = useState('balanced');
  const [loading, setLoading] = useState(false);

  const strategies = [
    { value: 'quick_sale', label: '⚡ Quick Sale', desc: '-15% for fast turnover' },
    { value: 'balanced', label: '⚖️ Balanced', desc: 'Market median price' },
    { value: 'premium', label: '💎 Premium', desc: '+10-20% for quality' },
    { value: 'competitive', label: '🎯 Competitive', desc: 'Undercut competition' }
  ];

  const analyzePrices = async () => {
    if (selectedDrafts.length === 0) {
      toast.error('Select items to analyze');
      return;
    }

    setLoading(true);
    const loadingToast = toast.loading('Analyzing market prices...');

    try {
      const response = await fetch('/api/v1/pricing/bulk-optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          draft_ids: selectedDrafts,
          strategy,
          apply: false
        })
      });

      const data = await response.json();
      setSuggestions(data.results);
      toast.success(`Analyzed ${data.total_items} items!`, { id: loadingToast });
    } catch (error) {
      toast.error('Failed to analyze prices', { id: loadingToast });
    } finally {
      setLoading(false);
    }
  };

  const applyPrices = async () => {
    const loadingToast = toast.loading(`Updating ${suggestions.length} prices...`);

    try {
      await fetch('/api/v1/pricing/bulk-optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          draft_ids: suggestions.map(s => s.draft_id),
          strategy,
          apply: true
        })
      });

      toast.success('✅ Prices updated!', { id: loadingToast });
      setSuggestions([]);
      setSelectedDrafts([]);
    } catch (error) {
      toast.error('Failed to update prices', { id: loadingToast });
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
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-lg shadow-green-500/50">
            <DollarSign className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-green-200 to-emerald-200 bg-clip-text text-transparent">
              Price Optimizer
            </h1>
            <p className="text-slate-400">AI-powered dynamic pricing</p>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-8 space-y-8 pb-12">
        {/* Strategy Selector */}
        <GlassCard className="p-6">
          <h3 className="text-xl font-bold text-white mb-4">Pricing Strategy</h3>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {strategies.map(strat => (
              <button
                key={strat.value}
                onClick={() => setStrategy(strat.value)}
                className={`p-4 rounded-xl border-2 transition-all text-left ${
                  strategy === strat.value
                    ? 'border-violet-500 bg-violet-500/20'
                    : 'border-white/10 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className="text-white font-semibold mb-1">{strat.label}</div>
                <div className="text-sm text-slate-400">{strat.desc}</div>
              </button>
            ))}
          </div>

          <div className="mt-6">
            <Button
              onClick={analyzePrices}
              disabled={loading || selectedDrafts.length === 0}
              icon={Zap}
            >
              Analyze Prices
            </Button>
          </div>
        </GlassCard>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">
                Price Suggestions ({suggestions.length})
              </h3>
              <Button icon={Zap} onClick={applyPrices}>
                Apply All Prices
              </Button>
            </div>

            <div className="space-y-4">
              {suggestions.map(item => (
                <div
                  key={item.draft_id}
                  className="flex items-center gap-4 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <div className="flex-1">
                    <h4 className="text-white font-semibold mb-2">{item.title}</h4>
                    <p className="text-sm text-slate-400">{item.reason}</p>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-xs text-slate-400 mb-1">Current</p>
                      <p className="text-2xl font-bold text-slate-300">{item.current_price}€</p>
                    </div>

                    <div className="flex items-center">
                      {item.difference > 0 ? (
                        <TrendingUp className="w-6 h-6 text-green-400" />
                      ) : (
                        <TrendingDown className="w-6 h-6 text-red-400" />
                      )}
                      <span className={`text-sm font-semibold ml-1 ${
                        item.difference > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {item.difference > 0 ? '+' : ''}{item.difference_percent}%
                      </span>
                    </div>

                    <div className="text-center">
                      <p className="text-xs text-slate-400 mb-1">Suggested</p>
                      <p className="text-2xl font-bold text-violet-400">{item.suggested_price}€</p>
                    </div>

                    <Badge className="bg-violet-500/20 text-violet-300">
                      {Math.round(item.confidence * 100)}% confidence
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Empty State */}
        {suggestions.length === 0 && (
          <GlassCard className="p-12 text-center">
            <DollarSign className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Select items to optimize pricing
            </h3>
            <p className="text-slate-400 mb-6">
              AI will analyze market and suggest optimal prices
            </p>
            <Button onClick={() => window.location.href = '/drafts'}>
              Go to Drafts
            </Button>
          </GlassCard>
        )}

        {/* Info Box */}
        <GlassCard className="p-4 bg-blue-500/10 border-blue-500/30">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-300">
              <strong>How it works:</strong> Our AI analyzes similar items on Vinted to recommend optimal prices based on brand, category, and condition.
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
