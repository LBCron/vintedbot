import { HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { User } from 'lucide-react';

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  shape?: 'circle' | 'rounded' | 'square';
  status?: 'online' | 'offline' | 'away' | 'busy' | null;
}

export default function Avatar({
  src,
  alt,
  fallback,
  size = 'md',
  shape = 'circle',
  status = null,
  className,
  ...props
}: AvatarProps) {
  const sizes = {
    xs: 'w-6 h-6 text-xs',
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
    xl: 'w-16 h-16 text-xl',
    '2xl': 'w-24 h-24 text-3xl',
  };

  const shapes = {
    circle: 'rounded-full',
    rounded: 'rounded-lg',
    square: 'rounded-none',
  };

  const statusColors = {
    online: 'bg-success-500',
    offline: 'bg-gray-400',
    away: 'bg-warning-500',
    busy: 'bg-error-500',
  };

  const statusSizes = {
    xs: 'w-1.5 h-1.5',
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
    xl: 'w-4 h-4',
    '2xl': 'w-5 h-5',
  };

  return (
    <div className={clsx('relative inline-block', className)} {...props}>
      <div
        className={clsx(
          'flex items-center justify-center overflow-hidden bg-gray-200 dark:bg-gray-700',
          sizes[size],
          shapes[shape]
        )}
      >
        {src ? (
          <img src={src} alt={alt || 'Avatar'} className="w-full h-full object-cover" />
        ) : fallback ? (
          <span className="font-medium text-gray-600 dark:text-gray-300">{fallback}</span>
        ) : (
          <User className="w-1/2 h-1/2 text-gray-400 dark:text-gray-500" />
        )}
      </div>

      {status && (
        <span
          className={clsx(
            'absolute bottom-0 right-0 block rounded-full ring-2 ring-white dark:ring-gray-800',
            statusColors[status],
            statusSizes[size]
          )}
        />
      )}
    </div>
  );
}
