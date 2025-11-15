import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users,
  Database,
  Activity,
  HardDrive,
  DollarSign,
  FileText,
  RefreshCw,
  Trash2,
  Eye,
  Edit,
  UserCog,
  Shield,
  TrendingUp,
  Server,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { adminAPI } from '../api/client';
import { GlassCard } from '../components/ui/GlassCard';
import { StatCard } from '../components/ui/StatCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { AnimatedNumber } from '../components/ui/AnimatedNumber';
import toast from 'react-hot-toast';
import { logger } from '../utils/logger';

const SUPER_ADMIN_EMAIL = 'ronanchenlopes@gmail.com';

interface UserData {
  id: string;
  email: string;
  name: string;
  plan: string;
  created_at: string;
  last_login: string;
  is_active: boolean;
}

interface SystemStats {
  postgres: {
    total_connections: number;
    active_connections: number;
    database_size_mb: number;
  };
  redis: {
    connected_clients: number;
    used_memory_mb: number;
    cache_hit_rate: number;
  };
  s3: {
    total_files: number;
    total_size_mb: number;
  };
  ai: {
    total_cost_today: number;
    total_cost_month: number;
    requests_today: number;
  };
}

interface UserStats {
  total_users: number;
  premium_users: number;
  users_today: number;
  active_users: number;
}

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  details?: any;
}

export default function Admin() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'system' | 'logs' | 'backups'>('overview');

  // Overview data
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);

  // Users data
  const [users, setUsers] = useState<UserData[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Logs data
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logLevel, setLogLevel] = useState<string>('all');

  // Backups data
  const [backups, setBackups] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    // Check if super admin
    if (!user || user.email.toLowerCase() !== SUPER_ADMIN_EMAIL.toLowerCase()) {
      navigate('/');
      return;
    }

    loadData();
  }, [user, navigate, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'overview') {
        const [statsRes, sysRes] = await Promise.all([
          adminAPI.getUsersStats(),
          adminAPI.getSystemStats(),
        ]);
        setUserStats(statsRes.data);
        setSystemStats(sysRes.data);
      } else if (activeTab === 'users') {
        const usersRes = await adminAPI.getUsers({ page_size: 100 });
        setUsers(usersRes.data.users || usersRes.data);
      } else if (activeTab === 'logs') {
        const logsRes = await adminAPI.getSystemLogs({ limit: 100 });
        setLogs(logsRes.data.logs || logsRes.data);
      } else if (activeTab === 'backups') {
        const backupsRes = await adminAPI.getBackups();
        setBackups(backupsRes.data.backups || backupsRes.data);
      }
    } catch (error: any) {
      logger.error('Failed to load admin data', error);
      if (error.response?.status === 403) {
        toast.error('Access denied. Super admin privileges required.');
        navigate('/');
      } else {
        toast.error('Failed to load admin data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    const toastId = toast.loading('Deleting user...');
    try {
      await adminAPI.deleteUser(userId);
      setUsers(users.filter(u => u.id !== userId));
      toast.success('User deleted successfully', { id: toastId });
    } catch (error) {
      logger.error('Failed to delete user', error);
      toast.error('Failed to delete user', { id: toastId });
    }
  };

  const handleChangePlan = async (userId: string) => {
    const plan = prompt('Enter new plan (free/premium/enterprise):');
    if (!plan) return;

    const toastId = toast.loading('Changing plan...');
    try {
      await adminAPI.changePlan(userId, plan);
      setUsers(users.map(u => u.id === userId ? { ...u, plan } : u));
      toast.success('Plan changed successfully', { id: toastId });
    } catch (error) {
      logger.error('Failed to change plan', error);
      toast.error('Failed to change plan', { id: toastId });
    }
  };

  const handleImpersonate = async (userId: string) => {
    if (!confirm('Login as this user? You will be logged out of your admin account.')) return;

    const toastId = toast.loading('Switching accounts...');
    try {
      const response = await adminAPI.impersonate(userId);
      localStorage.setItem('auth_token', response.data.access_token);
      toast.success('Account switched! Redirecting...', { id: toastId });
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    } catch (error) {
      logger.error('Failed to impersonate', error);
      toast.error('Failed to impersonate user', { id: toastId });
    }
  };

  const handleCreateBackup = async () => {
    if (!confirm('Create a new database backup?')) return;

    const toastId = toast.loading('Creating backup...');
    try {
      await adminAPI.createBackup();
      toast.success('Backup created successfully', { id: toastId });
      await loadData();
    } catch (error) {
      logger.error('Failed to create backup', error);
      toast.error('Failed to create backup', { id: toastId });
    }
  };

  const handleClearCache = async () => {
    if (!confirm('Clear all Redis cache? This will temporarily slow down requests.')) return;

    const toastId = toast.loading('Clearing cache...');
    try {
      await adminAPI.clearCache();
      toast.success('Cache cleared successfully', { id: toastId });
    } catch (error) {
      logger.error('Failed to clear cache', error);
      toast.error('Failed to clear cache', { id: toastId });
    }
  };

  const filteredUsers = users.filter(u =>
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'system', label: 'System', icon: Server },
    { id: 'logs', label: 'Logs', icon: FileText },
    { id: 'backups', label: 'Backups', icon: Database },
  ];

  if (loading && !userStats && !systemStats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <GlassCard className="p-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-12 h-12 border-4 border-violet-500/30 border-t-violet-500 rounded-full"
              />
              <p className="text-slate-400">Loading admin panel...</p>
            </div>
          </GlassCard>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-red-500 to-orange-600 rounded-2xl shadow-lg shadow-red-500/50">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-red-200 to-orange-200 bg-clip-text text-transparent">
                Super Admin Panel
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="error" size="md">SUPER ADMIN</Badge>
                <p className="text-slate-400 text-sm">
                  {user?.email}
                </p>
              </div>
            </div>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            icon={RefreshCw}
            className={refreshing ? 'animate-spin' : ''}
          >
            Refresh
          </Button>
        </motion.div>

        {/* Tabs */}
        <GlassCard noPadding>
          <div className="flex gap-2 p-2 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30'
                      : 'text-slate-300 hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </GlassCard>

        {/* Overview Tab */}
        {activeTab === 'overview' && userStats && systemStats && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {/* User Stats */}
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent mb-6">
                User Statistics
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                  title="Total Users"
                  value={<AnimatedNumber value={userStats.total_users} />}
                  icon={Users}
                  iconColor="blue"
                />
                <StatCard
                  title="Premium Users"
                  value={<AnimatedNumber value={userStats.premium_users} />}
                  icon={TrendingUp}
                  iconColor="purple"
                  subtitle={`${((userStats.premium_users / userStats.total_users) * 100).toFixed(1)}% of total`}
                />
                <StatCard
                  title="New Today"
                  value={<AnimatedNumber value={userStats.users_today} />}
                  icon={Users}
                  iconColor="green"
                />
                <StatCard
                  title="Active Now"
                  value={<AnimatedNumber value={userStats.active_users} />}
                  icon={Activity}
                  iconColor="yellow"
                />
              </div>
            </div>

            {/* System Stats */}
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent mb-6">
                System Resources
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <GlassCard hover>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-slate-400">PostgreSQL</h3>
                    <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                      <Database className="w-5 h-5 text-blue-400" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold text-white mb-1">
                    {systemStats.postgres.active_connections}/{systemStats.postgres.total_connections}
                  </p>
                  <p className="text-xs text-slate-500">
                    {systemStats.postgres.database_size_mb.toFixed(2)} MB
                  </p>
                </GlassCard>

                <GlassCard hover>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-slate-400">Redis Cache</h3>
                    <div className="p-2 bg-red-500/20 rounded-lg border border-red-500/30">
                      <Activity className="w-5 h-5 text-red-400" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold text-white mb-1">
                    {systemStats.redis.cache_hit_rate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-500">
                    {systemStats.redis.used_memory_mb.toFixed(2)} MB used
                  </p>
                </GlassCard>

                <GlassCard hover>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-slate-400">S3 Storage</h3>
                    <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/30">
                      <HardDrive className="w-5 h-5 text-green-400" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold text-white mb-1">
                    {systemStats.s3.total_files}
                  </p>
                  <p className="text-xs text-slate-500">
                    {systemStats.s3.total_size_mb.toFixed(2)} MB
                  </p>
                </GlassCard>

                <GlassCard hover>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-slate-400">AI Costs</h3>
                    <div className="p-2 bg-yellow-500/20 rounded-lg border border-yellow-500/30">
                      <DollarSign className="w-5 h-5 text-yellow-400" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold text-white mb-1">
                    ${systemStats.ai.total_cost_today.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">
                    ${systemStats.ai.total_cost_month.toFixed(2)} this month
                  </p>
                </GlassCard>
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent mb-6">
                Quick Actions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <GlassCard hover className="cursor-pointer" onClick={handleClearCache}>
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-500/30">
                      <RefreshCw className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">Clear Cache</h3>
                      <p className="text-sm text-slate-400">Reset Redis cache</p>
                    </div>
                  </div>
                </GlassCard>

                <GlassCard hover className="cursor-pointer" onClick={handleCreateBackup}>
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-green-500/20 rounded-xl border border-green-500/30">
                      <Database className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">Create Backup</h3>
                      <p className="text-sm text-slate-400">Backup PostgreSQL</p>
                    </div>
                  </div>
                </GlassCard>

                <GlassCard hover className="cursor-pointer" onClick={() => window.open('http://localhost:9090', '_blank')}>
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-violet-500/20 rounded-xl border border-violet-500/30">
                      <Activity className="w-6 h-6 text-violet-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">View Metrics</h3>
                      <p className="text-sm text-slate-400">Open Prometheus</p>
                    </div>
                  </div>
                </GlassCard>
              </div>
            </div>
          </motion.div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Search */}
            <GlassCard>
              <div className="relative">
                <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search users by email or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                />
              </div>
            </GlassCard>

            {/* Users Table */}
            <GlassCard noPadding className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-white/5 border-b border-white/10">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">User</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Plan</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Created</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {filteredUsers.map((user) => (
                      <tr key={user.id} className="hover:bg-white/5 transition-colors">
                        <td className="px-4 py-3">
                          <div>
                            <div className="font-medium text-white">{user.name}</div>
                            <div className="text-sm text-slate-400">{user.email}</div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            variant={user.plan === 'premium' ? 'primary' : user.plan === 'enterprise' ? 'warning' : 'info'}
                            size="sm"
                          >
                            {user.plan.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          {user.is_active ? (
                            <CheckCircle className="w-5 h-5 text-green-400" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-400" />
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-400">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => toast.info(`User ID: ${user.id}`)}
                              className="p-1.5 text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                              title="View Details"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleChangePlan(user.id)}
                              className="p-1.5 text-yellow-400 hover:bg-yellow-500/10 rounded-lg transition-colors"
                              title="Change Plan"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleImpersonate(user.id)}
                              className="p-1.5 text-green-400 hover:bg-green-500/10 rounded-lg transition-colors"
                              title="Impersonate User"
                            >
                              <UserCog className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className="p-1.5 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                              title="Delete User"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>

            {filteredUsers.length === 0 && (
              <GlassCard className="text-center py-12">
                <Users className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                <p className="text-slate-400">No users found</p>
              </GlassCard>
            )}
          </motion.div>
        )}

        {/* System Tab */}
        {activeTab === 'system' && systemStats && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* PostgreSQL Details */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                    <Database className="w-6 h-6 text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">PostgreSQL</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Active Connections:</span>
                    <span className="font-semibold text-white">
                      {systemStats.postgres.active_connections}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Connections:</span>
                    <span className="font-semibold text-white">
                      {systemStats.postgres.total_connections}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Database Size:</span>
                    <span className="font-semibold text-white">
                      {systemStats.postgres.database_size_mb.toFixed(2)} MB
                    </span>
                  </div>
                </div>
              </GlassCard>

              {/* Redis Details */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-red-500/20 rounded-lg border border-red-500/30">
                    <Activity className="w-6 h-6 text-red-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Redis Cache</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cache Hit Rate:</span>
                    <span className="font-semibold text-white">
                      {systemStats.redis.cache_hit_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Connected Clients:</span>
                    <span className="font-semibold text-white">
                      {systemStats.redis.connected_clients}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Memory Used:</span>
                    <span className="font-semibold text-white">
                      {systemStats.redis.used_memory_mb.toFixed(2)} MB
                    </span>
                  </div>
                </div>
              </GlassCard>

              {/* S3 Details */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/30">
                    <HardDrive className="w-6 h-6 text-green-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">S3 Storage</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Files:</span>
                    <span className="font-semibold text-white">
                      {systemStats.s3.total_files}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Size:</span>
                    <span className="font-semibold text-white">
                      {systemStats.s3.total_size_mb.toFixed(2)} MB
                    </span>
                  </div>
                </div>
              </GlassCard>

              {/* AI Costs Details */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-yellow-500/20 rounded-lg border border-yellow-500/30">
                    <DollarSign className="w-6 h-6 text-yellow-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">AI Costs</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Today:</span>
                    <span className="font-semibold text-white">
                      ${systemStats.ai.total_cost_today.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">This Month:</span>
                    <span className="font-semibold text-white">
                      ${systemStats.ai.total_cost_month.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Requests Today:</span>
                    <span className="font-semibold text-white">
                      {systemStats.ai.requests_today}
                    </span>
                  </div>
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Log Level Filter */}
            <GlassCard>
              <select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
              >
                <option value="all">All Levels</option>
                <option value="error">Errors</option>
                <option value="warning">Warnings</option>
                <option value="info">Info</option>
              </select>
            </GlassCard>

            {/* Logs */}
            <GlassCard className="space-y-2">
              {logs.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <FileText className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                  <p>No logs available</p>
                </div>
              ) : (
                logs.map((log, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-xl border ${
                      log.level === 'error' ? 'border-red-500/30 bg-red-500/10' :
                      log.level === 'warning' ? 'border-yellow-500/30 bg-yellow-500/10' :
                      'border-blue-500/30 bg-blue-500/10'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {log.level === 'error' && <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />}
                      {log.level === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />}
                      {log.level === 'info' && <CheckCircle className="w-5 h-5 text-blue-400 mt-0.5" />}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-slate-400">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                          <Badge
                            variant={log.level === 'error' ? 'error' : log.level === 'warning' ? 'warning' : 'info'}
                            size="sm"
                          >
                            {log.level.toUpperCase()}
                          </Badge>
                        </div>
                        <p className="text-sm text-white">{log.message}</p>
                        {log.details && (
                          <pre className="mt-2 text-xs text-slate-400 overflow-x-auto">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </GlassCard>
          </motion.div>
        )}

        {/* Backups Tab */}
        {activeTab === 'backups' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <GlassCard>
              <Button
                onClick={handleCreateBackup}
                icon={Database}
                className="w-full"
              >
                Create New Backup
              </Button>
            </GlassCard>

            <GlassCard>
              {backups.length === 0 ? (
                <div className="text-center py-12">
                  <Database className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                  <p className="text-slate-400">No backups available</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {backups.map((backup, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 border border-white/10 rounded-xl hover:bg-white/5 transition-colors"
                    >
                      <div>
                        <div className="font-medium text-white">{backup.name}</div>
                        <div className="text-sm text-slate-400">
                          {new Date(backup.created_at).toLocaleString()} • {backup.size_mb.toFixed(2)} MB
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toast.info('Restore functionality coming soon')}
                      >
                        Restore
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          </motion.div>
        )}
      </div>
    </div>
  );
}
