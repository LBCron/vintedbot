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
import StatsCard from '../components/common/StatsCard';
import Skeleton from 'react-loading-skeleton';
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
        alert('Access denied. Super admin privileges required.');
        navigate('/');
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

    try {
      await adminAPI.deleteUser(userId);
      setUsers(users.filter(u => u.id !== userId));
      alert('User deleted successfully');
    } catch (error) {
      logger.error('Failed to delete user', error);
      alert('Failed to delete user');
    }
  };

  const handleChangePlan = async (userId: string) => {
    const plan = prompt('Enter new plan (free/premium/enterprise):');
    if (!plan) return;

    try {
      await adminAPI.changePlan(userId, plan);
      setUsers(users.map(u => u.id === userId ? { ...u, plan } : u));
      alert('Plan changed successfully');
    } catch (error) {
      logger.error('Failed to change plan', error);
      alert('Failed to change plan');
    }
  };

  const handleImpersonate = async (userId: string) => {
    if (!confirm('Login as this user? You will be logged out of your admin account.')) return;

    try {
      // SECURITY FIX Bug #3: Backend sets HTTP-only cookie automatically
      // No need to store token in localStorage (vulnerable to XSS)
      await adminAPI.impersonate(userId);
      window.location.href = '/';
    } catch (error) {
      logger.error('Failed to impersonate', error);
      alert('Failed to impersonate user');
    }
  };

  const handleCreateBackup = async () => {
    if (!confirm('Create a new database backup?')) return;

    try {
      await adminAPI.createBackup();
      alert('Backup created successfully');
      await loadData();
    } catch (error) {
      logger.error('Failed to create backup', error);
      alert('Failed to create backup');
    }
  };

  const handleClearCache = async () => {
    if (!confirm('Clear all Redis cache? This will temporarily slow down requests.')) return;

    try {
      await adminAPI.clearCache();
      alert('Cache cleared successfully');
    } catch (error) {
      logger.error('Failed to clear cache', error);
      alert('Failed to clear cache');
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
      <div className="space-y-6">
        <Skeleton height={60} />
        <Skeleton height={100} />
        <Skeleton height={400} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-red-600" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Super Admin Panel
            </h1>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Logged in as: <span className="font-mono font-semibold">{user?.email}</span>
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn btn-secondary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </motion.div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && userStats && systemStats && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-6"
        >
          {/* User Stats */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">User Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatsCard
                title="Total Users"
                value={userStats.total_users}
                icon={Users}
              />
              <StatsCard
                title="Premium Users"
                value={userStats.premium_users}
                icon={TrendingUp}
                trend={((userStats.premium_users / userStats.total_users) * 100).toFixed(1) + '%'}
              />
              <StatsCard
                title="New Today"
                value={userStats.users_today}
                icon={Users}
              />
              <StatsCard
                title="Active Now"
                value={userStats.active_users}
                icon={Activity}
              />
            </div>
          </div>

          {/* System Stats */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">System Resources</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">PostgreSQL</h3>
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                  {systemStats.postgres.active_connections}/{systemStats.postgres.total_connections}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {systemStats.postgres.database_size_mb.toFixed(2)} MB
                </p>
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Redis Cache</h3>
                  <Activity className="w-5 h-5 text-red-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                  {systemStats.redis.cache_hit_rate.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {systemStats.redis.used_memory_mb.toFixed(2)} MB used
                </p>
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">S3 Storage</h3>
                  <HardDrive className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                  {systemStats.s3.total_files}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {systemStats.s3.total_size_mb.toFixed(2)} MB
                </p>
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">AI Costs</h3>
                  <DollarSign className="w-5 h-5 text-yellow-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                  ${systemStats.ai.total_cost_today.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  ${systemStats.ai.total_cost_month.toFixed(2)} this month
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <button
                onClick={handleClearCache}
                className="card hover:shadow-lg transition-shadow cursor-pointer text-left"
              >
                <div className="flex items-center gap-3">
                  <RefreshCw className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Clear Cache</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Reset Redis cache</p>
                  </div>
                </div>
              </button>

              <button
                onClick={handleCreateBackup}
                className="card hover:shadow-lg transition-shadow cursor-pointer text-left"
              >
                <div className="flex items-center gap-3">
                  <Database className="w-6 h-6 text-green-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Create Backup</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Backup PostgreSQL</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => window.open('http://localhost:9090', '_blank')}
                className="card hover:shadow-lg transition-shadow cursor-pointer text-left"
              >
                <div className="flex items-center gap-3">
                  <Activity className="w-6 h-6 text-purple-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">View Metrics</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Open Prometheus</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {/* Search */}
          <div className="card">
            <input
              type="text"
              placeholder="Search users by email or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Users Table */}
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">User</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Plan</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Created</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{user.name}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          user.plan === 'premium' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
                          user.plan === 'enterprise' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                        }`}>
                          {user.plan}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {user.is_active ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-600" />
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => alert(`View user details: ${user.id}`)}
                            className="p-1 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleChangePlan(user.id)}
                            className="p-1 text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded"
                            title="Change Plan"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleImpersonate(user.id)}
                            className="p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                            title="Impersonate User"
                          >
                            <UserCog className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
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
          </div>

          {filteredUsers.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No users found
            </div>
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
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">PostgreSQL</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Active Connections:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.postgres.active_connections}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Connections:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.postgres.total_connections}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Database Size:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.postgres.database_size_mb.toFixed(2)} MB
                  </span>
                </div>
              </div>
            </div>

            {/* Redis Details */}
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <Activity className="w-6 h-6 text-red-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Redis Cache</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Cache Hit Rate:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.redis.cache_hit_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Connected Clients:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.redis.connected_clients}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Memory Used:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.redis.used_memory_mb.toFixed(2)} MB
                  </span>
                </div>
              </div>
            </div>

            {/* S3 Details */}
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <HardDrive className="w-6 h-6 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">S3 Storage</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Files:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.s3.total_files}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Size:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.s3.total_size_mb.toFixed(2)} MB
                  </span>
                </div>
              </div>
            </div>

            {/* AI Costs Details */}
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <DollarSign className="w-6 h-6 text-yellow-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Costs</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Today:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    ${systemStats.ai.total_cost_today.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">This Month:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    ${systemStats.ai.total_cost_month.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Requests Today:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {systemStats.ai.requests_today}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {/* Log Level Filter */}
          <div className="card">
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              className="input"
            >
              <option value="all">All Levels</option>
              <option value="error">Errors</option>
              <option value="warning">Warnings</option>
              <option value="info">Info</option>
            </select>
          </div>

          {/* Logs */}
          <div className="card space-y-2">
            {logs.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No logs available
              </div>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  className={`p-3 rounded border ${
                    log.level === 'error' ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20' :
                    log.level === 'warning' ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20' :
                    'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {log.level === 'error' && <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />}
                    {log.level === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />}
                    {log.level === 'info' && <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5" />}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                        <span className={`text-xs font-semibold uppercase px-2 py-0.5 rounded ${
                          log.level === 'error' ? 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200' :
                          log.level === 'warning' ? 'bg-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' :
                          'bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200'
                        }`}>
                          {log.level}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 dark:text-white">{log.message}</p>
                      {log.details && (
                        <pre className="mt-2 text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>
      )}

      {/* Backups Tab */}
      {activeTab === 'backups' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <div className="card">
            <button
              onClick={handleCreateBackup}
              className="btn btn-primary w-full"
            >
              <Database className="w-4 h-4" />
              Create New Backup
            </button>
          </div>

          <div className="card">
            {backups.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No backups available
              </div>
            ) : (
              <div className="space-y-2">
                {backups.map((backup, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{backup.name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(backup.created_at).toLocaleString()} • {backup.size_mb.toFixed(2)} MB
                      </div>
                    </div>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => alert('Restore functionality coming soon')}
                    >
                      Restore
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
