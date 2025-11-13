import { useState } from 'react';
import { ChevronLeft, ChevronRight, X, ZoomIn } from 'lucide-react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';

interface ImageCarouselProps {
  images: string[];
  alt?: string;
  className?: string;
  showThumbnails?: boolean;
  showControls?: boolean;
  autoPlay?: boolean;
  interval?: number;
  onImageClick?: (index: number) => void;
  onDelete?: (index: number) => void;
}

export default function ImageCarousel({
  images,
  alt = 'Image',
  className,
  showThumbnails = true,
  showControls = true,
  autoPlay = false,
  interval = 3000,
  onImageClick,
  onDelete,
}: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [direction, setDirection] = useState(0);

  const goToNext = () => {
    setDirection(1);
    setCurrentIndex((prev) => (prev + 1) % images.length);
  };

  const goToPrev = () => {
    setDirection(-1);
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const goToIndex = (index: number) => {
    setDirection(index > currentIndex ? 1 : -1);
    setCurrentIndex(index);
  };

  const handleDelete = (e: React.MouseEvent, index: number) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(index);
      if (currentIndex >= images.length - 1) {
        setCurrentIndex(Math.max(0, images.length - 2));
      }
    }
  };

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 1000 : -1000,
      opacity: 0
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      zIndex: 0,
      x: direction < 0 ? 1000 : -1000,
      opacity: 0
    })
  };

  if (images.length === 0) {
    return (
      <div className={clsx('bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center', className)}>
        <p className="text-gray-400 dark:text-gray-600">No images</p>
      </div>
    );
  }

  return (
    <div className={clsx('relative', className)}>
      {/* Main Image */}
      <div className="relative aspect-[4/3] bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden group">
        <AnimatePresence initial={false} custom={direction}>
          <motion.img
            key={currentIndex}
            src={images[currentIndex]}
            alt={`${alt} ${currentIndex + 1}`}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: 'spring', stiffness: 300, damping: 30 },
              opacity: { duration: 0.2 }
            }}
            className="absolute inset-0 w-full h-full object-cover"
            onClick={() => {
              if (onImageClick) {
                onImageClick(currentIndex);
              } else {
                setIsLightboxOpen(true);
              }
            }}
          />
        </AnimatePresence>

        {/* Navigation Controls */}
        {showControls && images.length > 1 && (
          <>
            <button
              onClick={goToPrev}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all"
              aria-label="Previous image"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all"
              aria-label="Next image"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </>
        )}

        {/* Image Counter */}
        <div className="absolute top-2 right-2 px-3 py-1 bg-black/60 text-white text-sm rounded-full">
          {currentIndex + 1} / {images.length}
        </div>

        {/* Zoom Icon */}
        <button
          onClick={() => setIsLightboxOpen(true)}
          className="absolute top-2 left-2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all"
          aria-label="Zoom image"
        >
          <ZoomIn className="w-4 h-4" />
        </button>

        {/* Delete Button */}
        {onDelete && (
          <button
            onClick={(e) => handleDelete(e, currentIndex)}
            className="absolute bottom-2 right-2 p-2 bg-error-500 hover:bg-error-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all"
            aria-label="Delete image"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Thumbnails */}
      {showThumbnails && images.length > 1 && (
        <div className="mt-4 flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
          {images.map((image, index) => (
            <button
              key={index}
              onClick={() => goToIndex(index)}
              className={clsx(
                'relative flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all',
                index === currentIndex
                  ? 'border-primary-500 ring-2 ring-primary-500/50'
                  : 'border-gray-200 dark:border-gray-700 hover:border-primary-300'
              )}
            >
              <img
                src={image}
                alt={`Thumbnail ${index + 1}`}
                className="w-full h-full object-cover"
              />
              {index === currentIndex && (
                <div className="absolute inset-0 bg-primary-500/20" />
              )}
              {onDelete && (
                <button
                  onClick={(e) => handleDelete(e, index)}
                  className="absolute top-1 right-1 p-1 bg-error-500 hover:bg-error-600 text-white rounded-full opacity-0 hover:opacity-100 transition-opacity"
                  aria-label={`Delete image ${index + 1}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Indicators */}
      {!showThumbnails && images.length > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
          {images.map((_, index) => (
            <button
              key={index}
              onClick={() => goToIndex(index)}
              className={clsx(
                'w-2 h-2 rounded-full transition-all',
                index === currentIndex
                  ? 'bg-white w-6'
                  : 'bg-white/50 hover:bg-white/75'
              )}
              aria-label={`Go to image ${index + 1}`}
            />
          ))}
        </div>
      )}

      {/* Lightbox */}
      {isLightboxOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setIsLightboxOpen(false)}
        >
          <button
            className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors"
            onClick={() => setIsLightboxOpen(false)}
          >
            <X className="w-6 h-6" />
          </button>

          <img
            src={images[currentIndex]}
            alt={`${alt} ${currentIndex + 1}`}
            className="max-w-full max-h-full object-contain"
            onClick={(e) => e.stopPropagation()}
          />

          {images.length > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  goToPrev();
                }}
                className="absolute left-4 top-1/2 -translate-y-1/2 p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors"
              >
                <ChevronLeft className="w-8 h-8" />
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  goToNext();
                }}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors"
              >
                <ChevronRight className="w-8 h-8" />
              </button>
            </>
          )}

          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-black/60 text-white text-sm rounded-full">
            {currentIndex + 1} / {images.length}
          </div>
        </div>
      )}
    </div>
  );
}
