import { memo } from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

const LoadingSpinner = memo<LoadingSpinnerProps>(({ size = 'medium', className = '' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
  };

  return (
    <Loader2 className={`${sizeClasses[size]} animate-spin text-primary-600 ${className}`} />
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';

export default LoadingSpinner;
