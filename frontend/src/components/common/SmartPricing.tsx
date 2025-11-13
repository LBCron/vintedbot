import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  Lightbulb,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Badge } from './Badge';

interface PricingData {
  current: number;
  suggested: {
    optimal: number;
    quickSale: number;
    maxProfit: number;
  };
  market: {
    min: number;
    max: number;
    average: number;
  };
  insights: {
    title: string;
    description: string;
  }[];
}

interface SmartPricingProps {
  category: string;
  brand?: string;
  condition?: string;
  currentPrice?: number;
  onChange?: (price: number) => void;
}

export default function SmartPricing({
  category,
  brand,
  condition,
  currentPrice = 0,
  onChange,
}: SmartPricingProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Mock data - would come from API
  const pricingData: PricingData = {
    current: currentPrice,
    suggested: {
      optimal: 28,
      quickSale: 25,
      maxProfit: 32,
    },
    market: {
      min: 22,
      max: 35,
      average: 28,
    },
    insights: [
      {
        title: 'Similar items selling fast',
        description: 'Items priced at €25-30 sell within 3 days',
      },
      {
        title: 'Season demand',
        description: 'Hoodies see 40% more interest in fall/winter',
      },
      {
        title: 'Brand premium',
        description: `${brand || 'This brand'} typically sells 15% above average`,
      },
    ],
  };

  const handleApplyPrice = (price: number) => {
    if (onChange) {
      onChange(price);
    }
  };

  const priceChange = currentPrice ? ((pricingData.suggested.optimal - currentPrice) / currentPrice) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Current Price vs Suggested */}
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Price (€)
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Current: {currentPrice}€
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-primary-600 dark:text-primary-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Suggested: {pricingData.suggested.optimal}€
          </span>
          {currentPrice > 0 && priceChange !== 0 && (
            <Badge variant={priceChange > 0 ? 'success' : 'error'} size="sm">
              {priceChange > 0 ? '+' : ''}{priceChange.toFixed(0)}%
            </Badge>
          )}
        </div>
      </div>

      {/* Market Analysis Card */}
      <motion.div
        initial={false}
        animate={{ height: isExpanded ? 'auto' : '120px' }}
        className="bg-gradient-to-br from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 border border-primary-200 dark:border-primary-800 rounded-lg overflow-hidden"
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              Market Analysis
            </h4>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          </div>

          {/* Price Range Visualization */}
          <div className="mb-4">
            <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-2">
              <span>{pricingData.market.min}€</span>
              <span className="font-medium text-gray-900 dark:text-white">
                Avg: {pricingData.market.average}€
              </span>
              <span>{pricingData.market.max}€</span>
            </div>

            <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              {/* Range bar */}
              <div className="absolute inset-0 bg-gradient-to-r from-success-500 via-warning-500 to-error-500 opacity-50" />

              {/* Suggested optimal position */}
              <div
                className="absolute top-0 bottom-0 w-1 bg-primary-600"
                style={{
                  left: `${((pricingData.suggested.optimal - pricingData.market.min) / (pricingData.market.max - pricingData.market.min)) * 100}%`,
                }}
              >
                <div className="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
                    Optimal
                  </span>
                </div>
              </div>
            </div>
          </div>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-3 mt-4"
              >
                {/* Pricing Strategies */}
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleApplyPrice(pricingData.suggested.quickSale)}
                    className="p-3 bg-white dark:bg-gray-800 border border-success-200 dark:border-success-800 rounded-lg hover:border-success-400 dark:hover:border-success-600 transition-colors group"
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <TrendingDown className="w-3.5 h-3.5 text-success-600 dark:text-success-400" />
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        Quick Sale
                      </span>
                    </div>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {pricingData.suggested.quickSale}€
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Sell faster
                    </p>
                  </button>

                  <button
                    onClick={() => handleApplyPrice(pricingData.suggested.optimal)}
                    className="p-3 bg-white dark:bg-gray-800 border-2 border-primary-500 dark:border-primary-400 rounded-lg hover:border-primary-600 dark:hover:border-primary-300 transition-colors group"
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <Target className="w-3.5 h-3.5 text-primary-600 dark:text-primary-400" />
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        Optimal
                      </span>
                    </div>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {pricingData.suggested.optimal}€
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Best balance
                    </p>
                  </button>

                  <button
                    onClick={() => handleApplyPrice(pricingData.suggested.maxProfit)}
                    className="p-3 bg-white dark:bg-gray-800 border border-warning-200 dark:border-warning-800 rounded-lg hover:border-warning-400 dark:hover:border-warning-600 transition-colors group"
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <DollarSign className="w-3.5 h-3.5 text-warning-600 dark:text-warning-400" />
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        Max Profit
                      </span>
                    </div>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {pricingData.suggested.maxProfit}€
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Higher price
                    </p>
                  </button>
                </div>

                {/* Insights */}
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                    Key Insights
                  </p>
                  {pricingData.insights.map((insight, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-2 p-2 bg-white/50 dark:bg-gray-800/50 rounded"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-xs font-medium text-gray-900 dark:text-white">
                          {insight.title}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                          {insight.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
