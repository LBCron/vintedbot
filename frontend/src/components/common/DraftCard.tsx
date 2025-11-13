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
      whileHover={{ scale: 1.02, y: -4 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`card overflow-hidden hover:shadow-2xl hover:shadow-primary-500/10 transition-all relative group ${isSelected ? 'ring-2 ring-primary-500 dark:ring-primary-400 shadow-xl' : ''}`}
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

      <div className="p-5 space-y-4">
        {/* AI Confidence Badge */}
        {draft.confidence && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-2 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 p-2.5 rounded-lg"
          >
            <Sparkles className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
              AI Confidence:
            </span>
            <Badge variant={getConfidenceColor(confidenceScore)} size="sm">
              {confidenceScore}%
            </Badge>
            <Tooltip content="AI confidence score based on photo quality, title, description completeness, and pricing accuracy">
              <HelpCircle className="w-3.5 h-3.5 text-gray-400 cursor-help" />
            </Tooltip>
          </motion.div>
        )}

        {/* Title */}
        <div>
          <h3 className="font-bold text-xl text-gray-900 dark:text-white line-clamp-2 mb-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
            {draft.title}
          </h3>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-2.5 text-sm">
            <div className="px-3 py-1.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-lg font-bold shadow-sm">
              {draft.price}€
            </div>
            <Badge variant="default" size="sm" className="font-medium">{draft.category}</Badge>
            <Badge variant="outline" size="sm" className="font-medium">{draft.condition}</Badge>
          </div>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-wider">
              Description
            </span>
            <div className="flex-1 h-px bg-gradient-to-r from-gray-300 to-transparent dark:from-gray-600"></div>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3 leading-relaxed">
            {draft.description}
          </p>
        </div>

        {/* Tags/Metadata */}
        {(draft.brand || draft.size || draft.color) && (
          <div className="flex flex-wrap gap-2">
            {draft.brand && (
              <Badge variant="outline" size="sm" className="font-medium">
                🏷️ {draft.brand}
              </Badge>
            )}
            {draft.size && (
              <Badge variant="outline" size="sm" className="font-medium">
                📏 {draft.size}
              </Badge>
            )}
            {draft.color && (
              <Badge variant="outline" size="sm" className="font-medium">
                🎨 {draft.color}
              </Badge>
            )}
          </div>
        )}
      </div>
      
      <div className="p-5 pt-0 flex gap-2.5">
        <Link
          to={`/drafts/${draft.id}`}
          className="flex-1 px-4 py-3 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 text-primary-700 dark:text-primary-400 rounded-xl hover:from-primary-100 hover:to-primary-200 dark:hover:from-primary-900/40 dark:hover:to-primary-800/40 flex items-center justify-center gap-2 text-sm font-semibold transition-all hover:shadow-md transform hover:scale-105"
        >
          <Edit className="w-4 h-4" />
          Edit
        </Link>

        {onPublish && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onPublish(draft.id)}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-success-50 to-green-100 dark:from-success-900/20 dark:to-green-800/20 text-success-700 dark:text-success-400 rounded-xl hover:from-success-100 hover:to-green-200 dark:hover:from-success-900/40 dark:hover:to-green-800/40 flex items-center justify-center gap-2 text-sm font-semibold transition-all hover:shadow-md"
          >
            <Send className="w-4 h-4" />
            Publish
          </motion.button>
        )}

        {onDelete && (
          <Tooltip content="Delete draft">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onDelete(draft.id)}
              className="px-4 py-3 bg-gradient-to-r from-error-50 to-red-100 dark:from-error-900/20 dark:to-red-800/20 text-error-700 dark:text-error-400 rounded-xl hover:from-error-100 hover:to-red-200 dark:hover:from-error-900/40 dark:hover:to-red-800/40 flex items-center justify-center gap-2 text-sm font-semibold transition-all hover:shadow-md"
            >
              <Trash2 className="w-4 h-4" />
            </motion.button>
          </Tooltip>
        )}
      </div>
    </motion.div>
  );
}
