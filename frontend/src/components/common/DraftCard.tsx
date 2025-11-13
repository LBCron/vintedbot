import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Edit, Trash2, Send, CheckSquare, Square, Sparkles, HelpCircle } from 'lucide-react';
import ImageCarousel from './ImageCarousel';
import { Tooltip } from './Tooltip';
import { Badge } from './Badge';
import type { Draft } from '../../types';

interface DraftCardProps {
  draft: Draft;
  onPublish?: (id: string) => void;
  onDelete?: (id: string) => void;
  isSelected?: boolean;
  onToggleSelect?: () => void;
}

export default function DraftCard({ draft, onPublish, onDelete, isSelected, onToggleSelect }: DraftCardProps) {
  const confidenceScore = draft.confidence ? Math.round(draft.confidence * 100) : 0;

  const getConfidenceColor = (score: number) => {
    if (score >= 85) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01, y: -2 }}
      transition={{ duration: 0.2 }}
      className={`card overflow-hidden hover:shadow-premium transition-all relative ${isSelected ? 'ring-2 ring-primary-500 dark:ring-primary-400' : ''}`}
    >
      {/* Selection Checkbox */}
      {onToggleSelect && (
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={(e) => {
            e.preventDefault();
            onToggleSelect();
          }}
          className="absolute top-3 right-3 z-20 p-1.5 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-lg shadow-md hover:bg-white dark:hover:bg-gray-800 transition-colors"
        >
          {isSelected ? (
            <CheckSquare className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          ) : (
            <Square className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          )}
        </motion.button>
      )}

      {/* Image Carousel with Thumbnails */}
      {draft.photos.length > 0 && (
        <div className="relative" onClick={(e) => e.stopPropagation()}>
          {/* Photo count badge */}
          {draft.photos.length > 1 && (
            <div className="absolute top-3 left-3 z-10 px-3 py-1.5 bg-black/70 backdrop-blur-sm text-white text-xs font-semibold rounded-full flex items-center gap-1.5 shadow-lg">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
              {draft.photos.length} photos
            </div>
          )}
          <ImageCarousel
            images={draft.photos}
            alt={draft.title}
            className="w-full"
            showThumbnails={true}
            showControls={draft.photos.length > 1}
          />
        </div>
      )}

      <div className="p-4 space-y-3">
        {/* AI Confidence Badge */}
        {draft.confidence && (
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary-500" />
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
              AI Confidence:
            </span>
            <Badge variant={getConfidenceColor(confidenceScore)} size="sm">
              {confidenceScore}%
            </Badge>
            <Tooltip content="AI confidence score based on photo quality, title, description completeness, and pricing accuracy">
              <HelpCircle className="w-3.5 h-3.5 text-gray-400 cursor-help" />
            </Tooltip>
          </div>
        )}

        {/* Title */}
        <div>
          <h3 className="font-semibold text-lg text-gray-900 dark:text-white line-clamp-2 mb-1">
            {draft.title}
          </h3>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <span className="font-semibold text-primary-600 dark:text-primary-400">
              {draft.price}€
            </span>
            <span>•</span>
            <Badge variant="default" size="sm">{draft.category}</Badge>
            <span>•</span>
            <span>{draft.condition}</span>
          </div>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              Description
            </span>
            <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {draft.description}
          </p>
        </div>

        {/* Tags/Metadata */}
        {(draft.brand || draft.size || draft.color) && (
          <div className="flex flex-wrap gap-1.5">
            {draft.brand && (
              <Badge variant="outline" size="sm">{draft.brand}</Badge>
            )}
            {draft.size && (
              <Badge variant="outline" size="sm">{draft.size}</Badge>
            )}
            {draft.color && (
              <Badge variant="outline" size="sm">{draft.color}</Badge>
            )}
          </div>
        )}
      </div>
      
      <div className="p-4 pt-0 flex gap-2">
        <Link
          to={`/drafts/${draft.id}`}
          className="flex-1 px-4 py-2.5 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/40 flex items-center justify-center gap-2 text-sm font-medium transition-colors"
        >
          <Edit className="w-4 h-4" />
          Edit
        </Link>

        {onPublish && (
          <button
            onClick={() => onPublish(draft.id)}
            className="flex-1 px-4 py-2.5 bg-success-50 dark:bg-success-900/20 text-success-700 dark:text-success-400 rounded-lg hover:bg-success-100 dark:hover:bg-success-900/40 flex items-center justify-center gap-2 text-sm font-medium transition-colors"
          >
            <Send className="w-4 h-4" />
            Publish
          </button>
        )}

        {onDelete && (
          <Tooltip content="Delete draft">
            <button
              onClick={() => onDelete(draft.id)}
              className="px-4 py-2.5 bg-error-50 dark:bg-error-900/20 text-error-700 dark:text-error-400 rounded-lg hover:bg-error-100 dark:hover:bg-error-900/40 flex items-center justify-center gap-2 text-sm font-medium transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </Tooltip>
        )}
      </div>
    </motion.div>
  );
}
