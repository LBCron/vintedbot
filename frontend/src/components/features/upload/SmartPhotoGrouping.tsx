import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Check,
  X,
  Move,
  Plus,
  Minus,
  Grid3x3,
  List,
} from 'lucide-react';
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core';
import {
  SortableContext,
  useSortable,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface PhotoGroup {
  id: string;
  name: string;
  photos: string[];
  confidence: number;
}

interface SmartPhotoGroupingProps {
  photos: string[];
  onGroupsConfirmed: (groups: PhotoGroup[]) => void;
  onCancel: () => void;
}

// Sortable Photo Component
function SortablePhoto({
  photo,
  groupId,
  onRemove,
}: {
  photo: string;
  groupId: string;
  onRemove: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: photo });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="relative aspect-square rounded-lg overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500 transition-colors cursor-move group"
    >
      <img
        src={photo}
        alt="Photo"
        className="w-full h-full object-cover"
        draggable={false}
      />
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="absolute top-1 right-1 p-1 bg-red-500 hover:bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

export default function SmartPhotoGrouping({
  photos,
  onGroupsConfirmed,
  onCancel,
}: SmartPhotoGroupingProps) {
  const [groups, setGroups] = useState<PhotoGroup[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    analyzePhotos();
  }, [photos]);

  const analyzePhotos = async () => {
    setIsAnalyzing(true);

    // Simulate AI analysis with realistic delays
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Mock smart grouping logic
    // In production, this would use computer vision to detect similar photos
    const detectedGroups: PhotoGroup[] = [];
    const photosPerGroup = Math.max(3, Math.floor(photos.length / 4));

    let currentIndex = 0;
    let groupNumber = 1;

    while (currentIndex < photos.length) {
      const groupPhotos = photos.slice(currentIndex, currentIndex + photosPerGroup);
      if (groupPhotos.length > 0) {
        detectedGroups.push({
          id: `group-${groupNumber}`,
          name: `Item ${groupNumber}`,
          photos: groupPhotos,
          confidence: 75 + Math.random() * 20, // 75-95% confidence
        });
        groupNumber++;
      }
      currentIndex += photosPerGroup;
    }

    setGroups(detectedGroups);
    setIsAnalyzing(false);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    // Handle reordering logic here
    // This would move photos between groups
  };

  const movePhotoToGroup = (
    photoUrl: string,
    fromGroupId: string,
    toGroupId: string
  ) => {
    setGroups((prev) => {
      const newGroups = [...prev];
      const fromGroup = newGroups.find((g) => g.id === fromGroupId);
      const toGroup = newGroups.find((g) => g.id === toGroupId);

      if (fromGroup && toGroup) {
        fromGroup.photos = fromGroup.photos.filter((p) => p !== photoUrl);
        toGroup.photos.push(photoUrl);
      }

      return newGroups.filter((g) => g.photos.length > 0);
    });
  };

  const removePhotoFromGroup = (photoUrl: string, groupId: string) => {
    setGroups((prev) => {
      const newGroups = [...prev];
      const group = newGroups.find((g) => g.id === groupId);
      if (group) {
        group.photos = group.photos.filter((p) => p !== photoUrl);
      }
      return newGroups.filter((g) => g.photos.length > 0);
    });
  };

  const createNewGroup = () => {
    setGroups((prev) => [
      ...prev,
      {
        id: `group-${Date.now()}`,
        name: `Item ${prev.length + 1}`,
        photos: [],
        confidence: 100,
      },
    ]);
  };

  const mergeGroups = (groupId1: string, groupId2: string) => {
    setGroups((prev) => {
      const newGroups = [...prev];
      const group1 = newGroups.find((g) => g.id === groupId1);
      const group2 = newGroups.find((g) => g.id === groupId2);

      if (group1 && group2) {
        group1.photos.push(...group2.photos);
        return newGroups.filter((g) => g.id !== groupId2);
      }

      return newGroups;
    });
  };

  const renameGroup = (groupId: string, newName: string) => {
    setGroups((prev) =>
      prev.map((g) => (g.id === groupId ? { ...g, name: newName } : g))
    );
  };

  const handleConfirm = () => {
    onGroupsConfirmed(groups);
  };

  if (isAnalyzing) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white dark:bg-gray-900 rounded-xl p-8 max-w-md text-center"
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
            <Sparkles className="w-8 h-8 text-white animate-pulse" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Analyzing Photos...
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            AI is detecting similar photos and grouping them by item
          </p>
          <div className="mt-6 flex items-center justify-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce" />
            <div
              className="w-2 h-2 rounded-full bg-primary-500 animate-bounce"
              style={{ animationDelay: '0.1s' }}
            />
            <div
              className="w-2 h-2 rounded-full bg-primary-500 animate-bounce"
              style={{ animationDelay: '0.2s' }}
            />
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/50 overflow-y-auto"
      >
        <div className="min-h-screen flex items-center justify-center p-6">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="w-full max-w-6xl bg-white dark:bg-gray-900 rounded-xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Smart Photo Grouping
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {groups.length} items detected from {photos.length} photos
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-lg transition-colors ${
                    viewMode === 'grid'
                      ? 'bg-primary-100 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                      : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <Grid3x3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-lg transition-colors ${
                    viewMode === 'list'
                      ? 'bg-primary-100 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                      : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 max-h-[70vh] overflow-y-auto">
              <div className="space-y-6">
                {groups.map((group, groupIndex) => (
                  <motion.div
                    key={group.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: groupIndex * 0.1 }}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                  >
                    {/* Group Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <input
                          type="text"
                          value={group.name}
                          onChange={(e) => renameGroup(group.id, e.target.value)}
                          className="text-lg font-semibold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-2 py-1 text-gray-900 dark:text-white"
                        />
                        <div className="px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 text-xs font-medium">
                          {group.photos.length} photos
                        </div>
                        <div className="px-3 py-1 rounded-full bg-success-100 dark:bg-success-900/20 text-success-600 dark:text-success-400 text-xs font-medium">
                          {Math.round(group.confidence)}% confident
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          if (confirm(`Delete ${group.name}?`)) {
                            setGroups((prev) => prev.filter((g) => g.id !== group.id));
                          }
                        }}
                        className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Photos Grid */}
                    <div
                      className={
                        viewMode === 'grid'
                          ? 'grid grid-cols-6 gap-3'
                          : 'flex flex-wrap gap-2'
                      }
                    >
                      {group.photos.map((photo) => (
                        <SortablePhoto
                          key={photo}
                          photo={photo}
                          groupId={group.id}
                          onRemove={() => removePhotoFromGroup(photo, group.id)}
                        />
                      ))}
                    </div>
                  </motion.div>
                ))}

                {/* Add New Group Button */}
                <button
                  onClick={createNewGroup}
                  className="w-full py-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-primary-500 hover:text-primary-600 dark:hover:text-primary-400 transition-colors flex items-center justify-center gap-2"
                >
                  <Plus className="w-5 h-5" />
                  Add New Group
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Drag photos between groups to reorganize
              </p>

              <div className="flex gap-2">
                <button
                  onClick={onCancel}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirm}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium flex items-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  Confirm Groups
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
