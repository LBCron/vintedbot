import { useState } from 'react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, rectSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { X, GripVertical, Eye, RotateCw, Plus } from 'lucide-react';
import { logger } from '../../utils/logger';

interface Photo {
  id: string;
  url: string;
  order: number;
}

interface PhotoGalleryProps {
  photos: Photo[];
  onPhotosChange: (photos: Photo[]) => void;
  onPhotoAdd?: (files: FileList) => void;
  editable?: boolean;
}

function SortablePhoto({ photo, onDelete, onRotate, onPreview }: {
  photo: Photo;
  onDelete: (id: string) => void;
  onRotate: (id: string) => void;
  onPreview: (photo: Photo) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: photo.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="relative group bg-gray-100 rounded-lg overflow-hidden aspect-square"
    >
      {/* Photo */}
      <img
        src={photo.url}
        alt={`Photo ${photo.order + 1}`}
        className="w-full h-full object-cover"
      />

      {/* Overlay avec actions */}
      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-200 flex items-center justify-center gap-2">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-white rounded-lg shadow-lg hover:bg-gray-100 cursor-move"
          title="Glisser pour réorganiser"
        >
          <GripVertical className="w-5 h-5 text-gray-700" />
        </button>

        {/* Preview */}
        <button
          onClick={() => onPreview(photo)}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-white rounded-lg shadow-lg hover:bg-gray-100"
          title="Aperçu"
        >
          <Eye className="w-5 h-5 text-gray-700" />
        </button>

        {/* Rotate */}
        <button
          onClick={() => onRotate(photo.id)}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-white rounded-lg shadow-lg hover:bg-gray-100"
          title="Pivoter"
        >
          <RotateCw className="w-5 h-5 text-gray-700" />
        </button>

        {/* Delete */}
        <button
          onClick={() => onDelete(photo.id)}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-red-500 rounded-lg shadow-lg hover:bg-red-600"
          title="Supprimer"
        >
          <X className="w-5 h-5 text-white" />
        </button>
      </div>

      {/* Badge d'ordre */}
      <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
        #{photo.order + 1}
      </div>
    </div>
  );
}

export default function PhotoGallery({ photos, onPhotosChange, onPhotoAdd, editable = true }: PhotoGalleryProps) {
  const [previewPhoto, setPreviewPhoto] = useState<Photo | null>(null);
  const [localPhotos, setLocalPhotos] = useState<Photo[]>(photos);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: any) => {
    const { active, over } = event;

    if (active.id !== over.id) {
      setLocalPhotos((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);

        const newPhotos = arrayMove(items, oldIndex, newIndex).map((photo, index) => ({
          ...photo,
          order: index,
        }));

        onPhotosChange(newPhotos);
        return newPhotos;
      });
    }
  };

  const handleDelete = (id: string) => {
    const newPhotos = localPhotos
      .filter((photo) => photo.id !== id)
      .map((photo, index) => ({ ...photo, order: index }));
    setLocalPhotos(newPhotos);
    onPhotosChange(newPhotos);
  };

  const handleRotate = (id: string) => {
    // TODO: Implémenter la rotation de l'image
    logger.info('Rotate photo', { id });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && onPhotoAdd) {
      onPhotoAdd(e.target.files);
    }
  };

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Photos ({localPhotos.length})
          </h3>
          {editable && (
            <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Plus className="w-4 h-4" />
              Ajouter des photos
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>
          )}
        </div>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={localPhotos.map((p) => p.id)}
            strategy={rectSortingStrategy}
          >
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {localPhotos.map((photo) => (
                <SortablePhoto
                  key={photo.id}
                  photo={photo}
                  onDelete={handleDelete}
                  onRotate={handleRotate}
                  onPreview={setPreviewPhoto}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {localPhotos.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <p className="text-gray-500">Aucune photo. Cliquez sur "Ajouter des photos" pour commencer.</p>
          </div>
        )}
      </div>

      {/* Modal Preview */}
      {previewPhoto && (
        <div
          className="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center p-4"
          onClick={() => setPreviewPhoto(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setPreviewPhoto(null)}
              className="absolute top-4 right-4 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={previewPhoto.url}
              alt={`Photo ${previewPhoto.order + 1}`}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-70 text-white px-4 py-2 rounded-full">
              Photo #{previewPhoto.order + 1}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
