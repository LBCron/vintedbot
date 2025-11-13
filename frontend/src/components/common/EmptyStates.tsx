import { motion } from 'framer-motion';
import {
  Search,
  FileText,
  MessageCircle,
  Upload,
  Clock,
  AlertCircle,
  TrendingUp,
  Inbox,
  Users,
  FolderOpen,
  Image as ImageIcon,
  Archive,
  ShoppingBag,
  LucideIcon,
} from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  children?: React.ReactNode;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  secondaryAction,
  children,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card p-12 text-center"
    >
      <div className="inline-flex items-center justify-center w-16 h-16 mb-6 rounded-full bg-gray-100 dark:bg-gray-800">
        <Icon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
      </div>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>

      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        {description}
      </p>

      {children}

      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          {action && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={action.onClick}
              className={`px-6 py-3 rounded-lg font-medium inline-flex items-center gap-2 transition-colors ${
                action.variant === 'secondary'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500'
                  : 'bg-primary-500 hover:bg-primary-600 text-white shadow-lg'
              }`}
            >
              {action.label}
            </motion.button>
          )}

          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="px-6 py-3 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium transition-colors"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}

// No Drafts
export function NoDrafts({ onUpload, onCreate }: { onUpload: () => void; onCreate: () => void }) {
  return (
    <EmptyState
      icon={FileText}
      title="No drafts yet"
      description="Upload photos or create a draft manually to start selling on Vinted"
      action={{ label: 'Upload Photos', onClick: onUpload }}
      secondaryAction={{ label: 'Create Draft', onClick: onCreate }}
    />
  );
}

// No Search Results
export function NoSearchResults({
  query,
  onReset,
}: {
  query: string;
  onReset: () => void;
}) {
  return (
    <EmptyState
      icon={Search}
      title="No results found"
      description={`No results for "${query}". Try adjusting your search or filters.`}
      action={{ label: 'Clear Filters', onClick: onReset, variant: 'secondary' }}
    />
  );
}

// No Messages
export function NoMessages() {
  return (
    <EmptyState
      icon={MessageCircle}
      title="No messages"
      description="Your conversations with buyers will appear here"
      secondaryAction={{ label: 'Learn More', onClick: () => {} }}
    />
  );
}

// No Analytics
export function NoAnalytics({ onPublish }: { onPublish: () => void }) {
  return (
    <EmptyState
      icon={TrendingUp}
      title="No analytics data yet"
      description="Publish your first listing to start seeing analytics and insights"
      action={{ label: 'Publish Draft', onClick: onPublish }}
    />
  );
}

// No History
export function NoHistory() {
  return (
    <EmptyState
      icon={Clock}
      title="No activity yet"
      description="Your actions and changes will be tracked here"
    />
  );
}

// No Templates
export function NoTemplates({ onCreate }: { onCreate: () => void }) {
  return (
    <EmptyState
      icon={FileText}
      title="No templates yet"
      description="Create reusable templates to speed up your listing creation"
      action={{ label: 'Create Template', onClick: onCreate }}
      secondaryAction={{ label: 'Learn About Templates', onClick: () => {} }}
    />
  );
}

// Upload Required
export function UploadRequired({ onUpload }: { onUpload: () => void }) {
  return (
    <EmptyState
      icon={Upload}
      title="Upload photos to get started"
      description="Our AI will automatically analyze your photos and create optimized drafts"
    >
      <div className="mb-6 p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg max-w-md mx-auto">
        <p className="text-sm text-primary-700 dark:text-primary-400">
          💡 <strong>Tip:</strong> Take clear photos in good lighting for best AI results
        </p>
      </div>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onUpload}
        className="px-8 py-4 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium inline-flex items-center gap-2 shadow-lg"
      >
        <Upload className="w-5 h-5" />
        Upload Photos
      </motion.button>
    </EmptyState>
  );
}

// Error State
export function ErrorState({
  title = 'Something went wrong',
  description = 'An error occurred while loading this content',
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry: () => void;
}) {
  return (
    <EmptyState
      icon={AlertCircle}
      title={title}
      description={description}
      action={{ label: 'Try Again', onClick: onRetry, variant: 'secondary' }}
    />
  );
}

// Welcome State (first time user)
export function WelcomeState({ onGetStarted }: { onGetStarted: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="card p-12 text-center"
    >
      <div className="mb-6">
        <div className="inline-flex items-center justify-center w-20 h-20 mb-4 rounded-full bg-gradient-to-br from-primary-500 to-purple-500">
          <ShoppingBag className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
          Welcome to VintedBot! 👋
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Automate your Vinted selling with AI-powered photo analysis, smart pricing, and bulk publishing
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-4xl mx-auto">
        {[
          {
            icon: Upload,
            title: 'Upload Photos',
            description: 'Bulk upload your product photos',
          },
          {
            icon: FileText,
            title: 'AI Analysis',
            description: 'Get auto-generated descriptions',
          },
          {
            icon: TrendingUp,
            title: 'Smart Pricing',
            description: 'Optimize prices for quick sales',
          },
        ].map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 + 0.2 }}
            className="p-6 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <div className="inline-flex items-center justify-center w-12 h-12 mb-4 rounded-lg bg-primary-100 dark:bg-primary-900/20">
              <feature.icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              {feature.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {feature.description}
            </p>
          </motion.div>
        ))}
      </div>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onGetStarted}
        className="px-8 py-4 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium inline-flex items-center gap-2 shadow-lg text-lg"
      >
        Get Started
        <Upload className="w-5 h-5" />
      </motion.button>

      <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
        Or <button className="text-primary-600 dark:text-primary-400 hover:underline">watch the 2-min tutorial</button>
      </p>
    </motion.div>
  );
}

// No Data with Illustration
export function NoDataIllustration({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="py-12 text-center"
    >
      {/* Simple SVG Illustration */}
      <svg
        className="mx-auto mb-6 w-48 h-48 text-gray-300 dark:text-gray-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>

      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        {description}
      </p>

      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium inline-flex items-center gap-2 shadow-lg transition-colors"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  );
}

// Maintenance Mode
export function MaintenanceState() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-md"
      >
        <div className="inline-flex items-center justify-center w-20 h-20 mb-6 rounded-full bg-warning-100 dark:bg-warning-900/20">
          <AlertCircle className="w-10 h-10 text-warning-600 dark:text-warning-400" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          Under Maintenance
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          We're currently performing scheduled maintenance. We'll be back shortly!
        </p>

        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Expected downtime: <strong>30 minutes</strong>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

// Offline State
export function OfflineState({ onRetry }: { onRetry: () => void }) {
  return (
    <EmptyState
      icon={AlertCircle}
      title="You're offline"
      description="Check your internet connection and try again"
      action={{ label: 'Retry', onClick: onRetry, variant: 'secondary' }}
    />
  );
}
