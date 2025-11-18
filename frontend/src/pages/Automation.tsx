import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Play,
  Pause,
  Trash2,
  Edit3,
  Clock,
  Zap,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  MessageSquare,
  RefreshCw,
  Calendar,
  Target
} from 'lucide-react';
import { cn } from '../lib/utils';
import toast from 'react-hot-toast';

export default function Automation() {
  const [rules] = useState([
    {
      id: '1',
      name: 'Auto-bump toutes les 3h',
      type: 'bump',
      status: 'active',
      schedule: 'Toutes les 3h',
      actions_count: 342,
      last_run: new Date('2024-01-20T14:30:00'),
      success_rate: 98
    },
    {
      id: '2',
      name: 'Réponse automatique aux questions',
      type: 'message',
      status: 'active',
      schedule: 'Temps réel',
      actions_count: 89,
      last_run: new Date('2024-01-20T15:45:00'),
      success_rate: 95
    },
    {
      id: '3',
      name: 'Baisse de prix après 7 jours',
      type: 'price',
      status: 'paused',
      schedule: 'Quotidien à 9h',
      actions_count: 23,
      last_run: new Date('2024-01-19T09:00:00'),
      success_rate: 100
    }
  ]);

  const stats = {
    total_actions: 454,
    active_rules: 2,
    time_saved: 12.5,
    success_rate: 97
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-br from-brand-600 via-brand-500 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-10 h-10" />
              <h1 className="text-4xl font-bold">Automatisation</h1>
            </div>
            <p className="text-brand-100 text-lg max-w-2xl">
              Configurez des règles pour automatiser vos actions sur Vinted
            </p>
          </motion.div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <AutoStatCard
              icon={<Zap className="w-5 h-5" />}
              label="Actions exécutées"
              value={stats.total_actions}
            />
            <AutoStatCard
              icon={<Play className="w-5 h-5" />}
              label="Règles actives"
              value={stats.active_rules}
            />
            <AutoStatCard
              icon={<Clock className="w-5 h-5" />}
              label="Heures gagnées"
              value={`${stats.time_saved}h`}
            />
            <AutoStatCard
              icon={<Target className="w-5 h-5" />}
              label="Taux de succès"
              value={`${stats.success_rate}%`}
            />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-6 pb-12">
        {/* Create New Rule */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.01 }}
          className="bg-white rounded-2xl p-8 border-2 border-dashed border-brand-300 mb-8 cursor-pointer group hover:border-brand-500 hover:shadow-lg transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-brand-50 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <Plus className="w-8 h-8 text-brand-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-1">
                  Créer une nouvelle règle
                </h3>
                <p className="text-gray-600">
                  Automatisez vos actions : bump, messages, prix, publication
                </p>
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn btn-primary"
              onClick={() => toast.success('Modal de création à venir')}
            >
              Créer
            </motion.button>
          </div>
        </motion.div>

        {/* Rules List */}
        <div className="space-y-4">
          {rules.map((rule, index) => (
            <AutomationRuleCard key={rule.id} rule={rule} index={index} />
          ))}
        </div>

        {/* Templates */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Templates populaires</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <RuleTemplate
              icon={<RefreshCw className="w-6 h-6" />}
              title="Auto-bump optimal"
              description="Remonte automatiquement vos articles toutes les 3h"
              color="blue"
            />
            <RuleTemplate
              icon={<MessageSquare className="w-6 h-6" />}
              title="Réponses automatiques"
              description="Répond automatiquement aux questions fréquentes"
              color="purple"
            />
            <RuleTemplate
              icon={<TrendingUp className="w-6 h-6" />}
              title="Pricing dynamique"
              description="Ajuste les prix selon la demande"
              color="green"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function AutoStatCard({ icon, label, value }: any) {
  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2 text-white/80">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
}

function AutomationRuleCard({ rule, index }: any) {
  const [isActive, setIsActive] = useState(rule.status === 'active');

  const typeConfig: any = {
    bump: { icon: RefreshCw, color: 'blue', label: 'Bump' },
    message: { icon: MessageSquare, color: 'purple', label: 'Messages' },
    price: { icon: TrendingUp, color: 'green', label: 'Prix' }
  };

  const config = typeConfig[rule.type];
  const TypeIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={cn(
        "bg-white rounded-2xl p-6 border-2 transition-all",
        isActive
          ? "border-brand-200 shadow-md"
          : "border-gray-200"
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          {/* Icon */}
          <div className={cn(
            "w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0",
            config.color === 'blue' && "bg-blue-50 text-blue-600",
            config.color === 'purple' && "bg-brand-50 text-brand-600",
            config.color === 'green' && "bg-success-50 text-success-600"
          )}>
            <TypeIcon className="w-7 h-7" />
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{rule.name}</h3>
              <span className={cn(
                "px-2 py-0.5 rounded-full text-xs font-semibold",
                config.color === 'blue' && "bg-blue-100 text-blue-700",
                config.color === 'purple' && "bg-brand-100 text-brand-700",
                config.color === 'green' && "bg-success-100 text-success-700"
              )}>
                {config.label}
              </span>
            </div>

            <div className="flex items-center gap-6 text-sm text-gray-600 mb-4">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                {rule.schedule}
              </span>
              <span className="flex items-center gap-1.5">
                <Zap className="w-4 h-4" />
                {rule.actions_count} actions
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-success-600" />
                {rule.success_rate}% succès
              </span>
            </div>

            <p className="text-sm text-gray-500">
              Dernière exécution : {new Date(rule.last_run).toLocaleString('fr-FR')}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 flex-shrink-0 ml-4">
          {/* Toggle */}
          <button
            onClick={() => {
              setIsActive(!isActive);
              toast.success(isActive ? 'Règle pausée' : 'Règle activée');
            }}
            className={cn(
              "relative w-14 h-8 rounded-full transition-all",
              isActive ? "bg-brand-600" : "bg-gray-200"
            )}
          >
            <motion.div
              animate={{ x: isActive ? 24 : 2 }}
              className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
            />
          </button>

          {/* Edit */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            onClick={() => toast.success('Édition à venir')}
          >
            <Edit3 className="w-5 h-5 text-gray-600" />
          </motion.button>

          {/* Delete */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 hover:bg-error-50 rounded-lg transition-colors"
            onClick={() => toast.error('Suppression à venir')}
          >
            <Trash2 className="w-5 h-5 text-gray-600 hover:text-error-600" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}

function RuleTemplate({ icon, title, description, color }: any) {
  const colors: any = {
    blue: 'from-blue-50 to-blue-100 border-blue-200 text-blue-600',
    purple: 'from-brand-50 to-brand-100 border-brand-200 text-brand-600',
    green: 'from-success-50 to-success-100 border-success-200 text-success-600'
  };

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      className={cn(
        "bg-gradient-to-br rounded-2xl p-6 border-2 cursor-pointer",
        colors[color]
      )}
      onClick={() => toast.success('Template à implémenter')}
    >
      <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4 shadow-sm">
        {icon}
      </div>
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="mt-4 text-sm font-semibold hover:underline"
      >
        Utiliser ce template
      </motion.button>
    </motion.div>
  );
}
