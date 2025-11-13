import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Badge } from '@/components/ui/Badge';
import {
  HardDrive,
  TrendingDown,
  Clock,
  DollarSign,
  Archive,
  Trash2,
  ArrowUp,
  AlertCircle,
  CheckCircle,
  Database
} from 'lucide-react';

interface StorageStats {
  temp_count: number;
  temp_size_gb: number;
  hot_count: number;
  hot_size_gb: number;
  cold_count: number;
  cold_size_gb: number;
  total_count: number;
  total_size_gb: number;
  monthly_cost_estimate: number;
  savings_vs_all_hot: number;
}

interface CostBreakdown {
  temp: { cost: number; size_gb: number; percentage: number };
  hot: { cost: number; size_gb: number; percentage: number };
  cold: { cost: number; size_gb: number; percentage: number };
  total: number;
}

interface LifecycleMetrics {
  photos_uploaded: number;
  photos_promoted: number;
  photos_archived: number;
  photos_deleted: number;
}

export default function StorageStatsPage() {
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [breakdown, setBreakdown] = useState<CostBreakdown | null>(null);
  const [lifecycle, setLifecycle] = useState<LifecycleMetrics | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStorageData();
  }, []);

  const fetchStorageData = async () => {
    try {
      setLoading(true);

      // Fetch stats
      const statsRes = await fetch('/api/storage/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch cost breakdown
      const breakdownRes = await fetch('/api/storage/stats/breakdown');
      const breakdownData = await breakdownRes.json();
      setBreakdown(breakdownData.breakdown);

      // Fetch lifecycle metrics (last 30 days)
      const lifecycleRes = await fetch('/api/storage/metrics/lifecycle?days=30');
      const lifecycleData = await lifecycleRes.json();
      setLifecycle(lifecycleData.metrics);

      // Fetch recommendations
      const recRes = await fetch('/api/storage/metrics/recommendations');
      const recData = await recRes.json();
      setRecommendations(recData.recommendations);

    } catch (error) {
      console.error('Failed to fetch storage data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatGB = (gb: number) => {
    if (gb < 0.1) return `${(gb * 1024).toFixed(0)} MB`;
    return `${gb.toFixed(2)} GB`;
  };

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `< $0.01`;
    return `$${cost.toFixed(2)}`;
  };

  if (loading || !stats || !breakdown || !lifecycle) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Stockage Multi-Tier
            </h1>
            <p className="text-gray-600 mt-1">
              Optimisation automatique des coûts de stockage photos
            </p>
          </div>
          <button
            onClick={fetchStorageData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Actualiser
          </button>
        </div>

        {/* Cost Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Coût Mensuel</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCost(stats.monthly_cost_estimate)}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <TrendingDown className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Économies</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCost(stats.savings_vs_all_hot)}
                </p>
                <p className="text-xs text-gray-500">vs. tout en HOT</p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Database className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Photos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total_count.toLocaleString()}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-orange-100 rounded-lg">
                <HardDrive className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Taille Totale</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatGB(stats.total_size_gb)}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Storage Tiers */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* TIER 1 - TEMP */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold text-gray-900">TIER 1 - TEMP</h3>
              </div>
              <Badge variant="secondary">Gratuit</Badge>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Photos</span>
                  <span className="font-medium">{stats.temp_count}</span>
                </div>
                <Progress value={(stats.temp_count / stats.total_count) * 100} />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Taille</span>
                  <span className="font-medium">{formatGB(stats.temp_size_gb)}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Coût</span>
                  <span className="font-bold text-green-600">$0.00</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Fly.io Volumes - Durée: 24-48h
                </p>
              </div>
            </div>
          </Card>

          {/* TIER 2 - HOT */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-orange-600" />
                <h3 className="font-semibold text-gray-900">TIER 2 - HOT</h3>
              </div>
              <Badge variant="warning">$0.015/GB</Badge>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Photos</span>
                  <span className="font-medium">{stats.hot_count}</span>
                </div>
                <Progress
                  value={(stats.hot_count / stats.total_count) * 100}
                  className="bg-orange-200"
                />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Taille</span>
                  <span className="font-medium">{formatGB(stats.hot_size_gb)}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Coût</span>
                  <span className="font-bold text-orange-600">
                    {formatCost(breakdown.hot.cost)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Cloudflare R2 - Drafts actifs &lt;90j
                </p>
              </div>
            </div>
          </Card>

          {/* TIER 3 - COLD */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Archive className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">TIER 3 - COLD</h3>
              </div>
              <Badge variant="info">$0.006/GB</Badge>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Photos</span>
                  <span className="font-medium">{stats.cold_count}</span>
                </div>
                <Progress
                  value={(stats.cold_count / stats.total_count) * 100}
                  className="bg-blue-200"
                />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Taille</span>
                  <span className="font-medium">{formatGB(stats.cold_size_gb)}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Coût</span>
                  <span className="font-bold text-blue-600">
                    {formatCost(breakdown.cold.cost)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Backblaze B2 - Archives &gt;90j
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Lifecycle Metrics (Last 30 Days) */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Lifecycle (30 derniers jours)
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-2">
                <ArrowUp className="w-6 h-6 text-green-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {lifecycle.photos_uploaded.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Photos uploadées</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-2">
                <TrendingDown className="w-6 h-6 text-blue-600 rotate-90" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {lifecycle.photos_promoted.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Promues HOT</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-2">
                <Archive className="w-6 h-6 text-purple-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {lifecycle.photos_archived.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Archivées COLD</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mb-2">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {lifecycle.photos_deleted.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Supprimées</p>
            </div>
          </div>
        </Card>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600" />
              Recommandations
            </h3>

            <div className="space-y-2">
              {recommendations.map((rec, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg"
                >
                  {rec.includes('✅') ? (
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  )}
                  <p className="text-sm text-gray-700">{rec}</p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Cost Breakdown Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Répartition des Coûts
          </h3>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">TIER 1 - TEMP (Gratuit)</span>
                <span className="font-medium">0%</span>
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-green-500" style={{ width: '0%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">TIER 2 - HOT (Cloudflare R2)</span>
                <span className="font-medium">{breakdown.hot.percentage.toFixed(1)}%</span>
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-orange-500"
                  style={{ width: `${breakdown.hot.percentage}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">TIER 3 - COLD (Backblaze B2)</span>
                <span className="font-medium">{breakdown.cold.percentage.toFixed(1)}%</span>
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{ width: `${breakdown.cold.percentage}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <span className="text-gray-900 font-semibold">Total Mensuel</span>
              <span className="text-2xl font-bold text-gray-900">
                {formatCost(breakdown.total)}
              </span>
            </div>
            <p className="text-sm text-green-600 mt-1">
              ✓ Économie de {formatCost(stats.savings_vs_all_hot)} vs. stockage HOT seul
            </p>
          </div>
        </Card>

        {/* Storage Lifecycle Workflow */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Workflow Lifecycle
          </h3>

          <div className="relative">
            <div className="flex items-center justify-between">
              <div className="text-center flex-1">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-2">
                  <Clock className="w-8 h-8 text-gray-600" />
                </div>
                <p className="font-medium text-gray-900">Upload</p>
                <p className="text-xs text-gray-600">TIER 1 - 48h</p>
              </div>

              <div className="flex-shrink-0 px-4">
                <div className="w-16 h-0.5 bg-gray-300"></div>
              </div>

              <div className="text-center flex-1">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-2">
                  <Database className="w-8 h-8 text-orange-600" />
                </div>
                <p className="font-medium text-gray-900">Active</p>
                <p className="text-xs text-gray-600">TIER 2 - 90j</p>
              </div>

              <div className="flex-shrink-0 px-4">
                <div className="w-16 h-0.5 bg-gray-300"></div>
              </div>

              <div className="text-center flex-1">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-2">
                  <Archive className="w-8 h-8 text-blue-600" />
                </div>
                <p className="font-medium text-gray-900">Archive</p>
                <p className="text-xs text-gray-600">TIER 3 - 365j</p>
              </div>

              <div className="flex-shrink-0 px-4">
                <div className="w-16 h-0.5 bg-gray-300"></div>
              </div>

              <div className="text-center flex-1">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-2">
                  <Trash2 className="w-8 h-8 text-red-600" />
                </div>
                <p className="font-medium text-gray-900">Delete</p>
                <p className="text-xs text-gray-600">Après 365j</p>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Note :</strong> Les photos publiées sur Vinted sont automatiquement
                supprimées après 7 jours (économie de ~80% des coûts).
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
