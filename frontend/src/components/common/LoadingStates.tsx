import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

// Skeleton Loader
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${className}`}
      style={{
        animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }}
    />
  );
}

// Skeleton Card (for draft cards)
export function SkeletonCard() {
  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-start gap-4">
        {/* Image skeleton */}
        <Skeleton className="w-32 h-32 flex-shrink-0" />

        {/* Content skeleton */}
        <div className="flex-1 space-y-3">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-16" />
            <Skeleton className="h-6 w-16" />
            <Skeleton className="h-6 w-16" />
          </div>
        </div>
      </div>

      {/* Actions skeleton */}
      <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
      </div>
    </div>
  );
}

// Skeleton Grid (for multiple cards)
export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

// Skeleton List
export function SkeletonList({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card p-4 flex items-center gap-4">
          <Skeleton className="w-12 h-12 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-8 w-20" />
        </div>
      ))}
    </div>
  );
}

// Skeleton Table
export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700 last:border-0"
        >
          {Array.from({ length: cols }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

// Spinning Loader
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

export function Spinner({ size = 'md', className = '', text }: SpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <Loader2 className={`${sizeClasses[size]} animate-spin text-primary-500`} />
      {text && (
        <p className="text-sm text-gray-600 dark:text-gray-400 animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
}

// Full Page Loader
export function PageLoader({ text }: { text?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <Spinner size="xl" text={text || 'Loading...'} />
    </div>
  );
}

// Inline Loader (for buttons, inline elements)
export function InlineLoader({ text }: { text?: string }) {
  return (
    <div className="flex items-center gap-2">
      <Loader2 className="w-4 h-4 animate-spin text-current" />
      {text && <span className="text-sm">{text}</span>}
    </div>
  );
}

// Progress Loader with percentage
interface ProgressLoaderProps {
  progress: number;
  text?: string;
  showPercentage?: boolean;
}

export function ProgressLoader({
  progress,
  text,
  showPercentage = true,
}: ProgressLoaderProps) {
  return (
    <div className="w-full space-y-2">
      {(text || showPercentage) && (
        <div className="flex items-center justify-between text-sm">
          {text && <span className="text-gray-700 dark:text-gray-300">{text}</span>}
          {showPercentage && (
            <span className="font-medium text-primary-600 dark:text-primary-400">
              {Math.round(progress)}%
            </span>
          )}
        </div>
      )}
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
}

// Upload Progress (with file info)
interface UploadProgressProps {
  fileName: string;
  fileSize: string;
  progress: number;
  onCancel?: () => void;
}

export function UploadProgress({
  fileName,
  fileSize,
  progress,
  onCancel,
}: UploadProgressProps) {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 dark:text-white truncate">
            {fileName}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {fileSize}
          </p>
        </div>
        {onCancel && (
          <button
            onClick={onCancel}
            className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            Cancel
          </button>
        )}
      </div>
      <ProgressLoader progress={progress} showPercentage />
    </div>
  );
}

// Pulsing Dot Loader
export function DotLoader() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 bg-primary-500 rounded-full"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  );
}

// Shimmer Effect Wrapper
export function ShimmerWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative overflow-hidden">
      {children}
      <div
        className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent"
        style={{
          animation: 'shimmer 2s infinite',
        }}
      />
    </div>
  );
}

// Content Loader (combines skeleton + text)
interface ContentLoaderProps {
  title?: string;
  description?: string;
  lines?: number;
}

export function ContentLoader({
  title = 'Loading content...',
  description,
  lines = 3,
}: ContentLoaderProps) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <Spinner size="lg" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {description && (
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {description}
          </p>
        )}
      </div>

      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  );
}
