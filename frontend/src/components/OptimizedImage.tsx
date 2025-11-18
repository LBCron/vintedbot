import { useState } from 'react';
import { useInView } from 'react-intersection-observer';
import { cn } from '@/lib/utils';

interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  priority?: boolean;
}

export default function OptimizedImage({
  src,
  alt,
  className,
  priority = false
}: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(false);

  const { ref, inView } = useInView({
    triggerOnce: true,
    skip: priority,
    rootMargin: '50px'
  });

  const shouldLoad = priority || inView;

  return (
    <div ref={ref} className={cn("relative overflow-hidden bg-gray-100", className)}>
      {shouldLoad && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          onError={() => setError(true)}
          className={cn(
            "w-full h-full object-cover transition-opacity duration-300",
            isLoaded ? "opacity-100" : "opacity-0"
          )}
        />
      )}

      {!isLoaded && !error && shouldLoad && (
        <div className="absolute inset-0 animate-pulse bg-gray-200" />
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <span className="text-gray-400 text-sm">Erreur chargement</span>
        </div>
      )}
    </div>
  );
}
