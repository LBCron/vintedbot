import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Image as ImageIcon,
  Crop,
  RotateCw,
  Sun,
  Contrast,
  Droplet,
  Type,
  Eraser,
  Download,
  Upload,
  Layers,
  Sliders,
  Sparkles,
  Check,
  X,
  ZoomIn,
  ZoomOut,
  Move,
  Grid,
  Eye,
  Zap,
} from 'lucide-react';
import { imagesAPI } from '../api/client';
import toast from 'react-hot-toast';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { logger } from '../utils/logger';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

interface ImageFile {
  id: string;
  path: string;
  name: string;
  url: string;
  selected: boolean;
}

type EditMode = 'crop' | 'rotate' | 'adjust' | 'watermark' | 'background' | null;

interface CropSettings {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface AdjustSettings {
  brightness: number;
  contrast: number;
  saturation: number;
}

interface WatermarkSettings {
  text: string;
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
  opacity: number;
  fontSize: number;
}

interface ImageQuality {
  brightness_score: number;
  sharpness_score: number;
  contrast_score: number;
  overall_score: number;
  suggestions: string[];
}

export default function ImageEditor() {
  const [images, setImages] = useState<ImageFile[]>([]);
  const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
  const [editMode, setEditMode] = useState<EditMode>(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [imageQuality, setImageQuality] = useState<ImageQuality | null>(null);
  const [analyzingAI, setAnalyzingAI] = useState(false);

  // Edit settings
  const [rotateAngle, setRotateAngle] = useState(90);
  const [cropSettings, setCropSettings] = useState<CropSettings>({
    x: 0,
    y: 0,
    width: 100,
    height: 100,
  });
  const [adjustSettings, setAdjustSettings] = useState<AdjustSettings>({
    brightness: 1,
    contrast: 1,
    saturation: 1,
  });
  const [watermarkSettings, setWatermarkSettings] = useState<WatermarkSettings>({
    text: '@YourUsername',
    position: 'bottom-right',
    opacity: 0.7,
    fontSize: 24,
  });

  const [presets, setPresets] = useState<any[]>([]);

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const response = await imagesAPI.getPresets();
      setPresets(response.data.presets || []);
    } catch (error) {
      logger.error('Failed to load presets', error);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newImages: ImageFile[] = Array.from(files).map((file, index) => ({
      id: `img-${Date.now()}-${index}`,
      path: file.name,
      name: file.name,
      url: URL.createObjectURL(file),
      selected: false,
    }));

    setImages([...images, ...newImages]);
    toast.success(`Added ${files.length} images`);
  };

  const toggleImageSelection = (id: string) => {
    const newSelection = new Set(selectedImages);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedImages(newSelection);
  };

  const selectAll = () => {
    if (selectedImages.size === images.length) {
      setSelectedImages(new Set());
    } else {
      setSelectedImages(new Set(images.map(img => img.id)));
    }
  };

  const handleBulkRotate = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select images to rotate');
      return;
    }

    try {
      setProcessing(true);
      toast.loading('Rotating images...');

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      await imagesAPI.bulkRotate({
        image_paths: selectedPaths,
        angle: rotateAngle,
      });

      toast.dismiss();
      toast.success(`Rotated ${selectedImages.size} images!`);
      setEditMode(null);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to rotate images');
      logger.error('Rotate error', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkCrop = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select images to crop');
      return;
    }

    try {
      setProcessing(true);
      toast.loading('Cropping images...');

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      await imagesAPI.bulkCrop({
        image_paths: selectedPaths,
        ...cropSettings,
      });

      toast.dismiss();
      toast.success(`Cropped ${selectedImages.size} images!`);
      setEditMode(null);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to crop images');
      logger.error('Crop error', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkAdjust = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select images to adjust');
      return;
    }

    try {
      setProcessing(true);
      toast.loading('Adjusting images...');

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      await imagesAPI.bulkAdjust({
        image_paths: selectedPaths,
        brightness: adjustSettings.brightness,
        contrast: adjustSettings.contrast,
        saturation: adjustSettings.saturation,
      });

      toast.dismiss();
      toast.success(`Adjusted ${selectedImages.size} images!`);
      setEditMode(null);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to adjust images');
      logger.error('Adjust error', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkWatermark = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select images to watermark');
      return;
    }

    if (!watermarkSettings.text) {
      toast.error('Please enter watermark text');
      return;
    }

    try {
      setProcessing(true);
      toast.loading('Adding watermark...');

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      await imagesAPI.bulkWatermark({
        image_paths: selectedPaths,
        ...watermarkSettings,
      });

      toast.dismiss();
      toast.success(`Added watermark to ${selectedImages.size} images!`);
      setEditMode(null);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to add watermark');
      logger.error('Watermark error', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkRemoveBackground = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select images');
      return;
    }

    try {
      setProcessing(true);
      toast.loading('Removing backgrounds... This may take a while');

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      await imagesAPI.bulkRemoveBackground({
        image_paths: selectedPaths,
        mode: 'auto',
      });

      toast.dismiss();
      toast.success(`Removed backgrounds from ${selectedImages.size} images!`);
      setEditMode(null);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to remove backgrounds');
      logger.error('Background removal error', error);
    } finally {
      setProcessing(false);
    }
  };

  const applyPreset = async (preset: any) => {
    if (selectedImages.size === 0) {
      toast.error('Please select images');
      return;
    }

    try {
      setProcessing(true);
      toast.loading(`Applying ${preset.name}...`);

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      // Apply preset settings
      if (preset.type === 'adjust') {
        await imagesAPI.bulkAdjust({
          image_paths: selectedPaths,
          ...preset.settings,
        });
      }

      toast.dismiss();
      toast.success(`Applied ${preset.name} to ${selectedImages.size} images!`);
    } catch (error) {
      toast.dismiss();
      toast.error(`Failed to apply ${preset.name}`);
      logger.error('Preset error', error);
    } finally {
      setProcessing(false);
    }
  };

  const analyzeWithAI = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select an image to analyze');
      return;
    }

    if (selectedImages.size > 1) {
      toast.error('Please select only one image for AI analysis');
      return;
    }

    try {
      setAnalyzingAI(true);
      const loadingToast = toast.loading('Analyzing image with GPT-4 Vision...');

      const selectedImage = images.find(img => selectedImages.has(img.id));
      if (!selectedImage) return;

      const response = await fetch('/api/v1/images/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          image_path: selectedImage.path
        })
      });

      const data = await response.json();

      setImageQuality({
        brightness_score: data.brightness_score,
        sharpness_score: data.sharpness_score,
        contrast_score: data.contrast_score,
        overall_score: data.overall_score,
        suggestions: data.suggestions || []
      });

      toast.success('AI analysis complete!', { id: loadingToast });
    } catch (error) {
      toast.error('Failed to analyze image');
      logger.error('AI analysis error', error);
    } finally {
      setAnalyzingAI(false);
    }
  };

  const autoEnhanceWithAI = async () => {
    if (selectedImages.size === 0) {
      toast.error('Please select images');
      return;
    }

    try {
      setProcessing(true);
      const loadingToast = toast.loading('Auto-enhancing with AI...');

      const selectedPaths = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.path);

      const response = await fetch('/api/v1/images/batch-enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          image_paths: selectedPaths
        })
      });

      const data = await response.json();

      toast.success(`Enhanced ${data.enhanced_count} images!`, { id: loadingToast });
      setImageQuality(null);
    } catch (error) {
      toast.error('Failed to enhance images');
      logger.error('Auto-enhance error', error);
    } finally {
      setProcessing(false);
    }
  };

  const executeEditAction = () => {
    switch (editMode) {
      case 'rotate':
        handleBulkRotate();
        break;
      case 'crop':
        handleBulkCrop();
        break;
      case 'adjust':
        handleBulkAdjust();
        break;
      case 'watermark':
        handleBulkWatermark();
        break;
      case 'background':
        handleBulkRemoveBackground();
        break;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
        >
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
              <ImageIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
                Bulk Image Editor
              </h1>
              <p className="text-slate-400 mt-1">
                Edit multiple images at once with powerful tools
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              icon={Sparkles}
              onClick={analyzeWithAI}
              disabled={analyzingAI || selectedImages.size !== 1}
              variant="outline"
            >
              AI Analyze
            </Button>
            <label className="cursor-pointer">
              <Button icon={Upload}>
                Upload Images
              </Button>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        </motion.div>

        {/* AI Quality Analysis Panel */}
        <AnimatePresence>
          {imageQuality && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <GlassCard className="p-6 bg-gradient-to-br from-violet-500/10 to-purple-500/10 border-violet-500/30">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Eye className="w-5 h-5 text-violet-400" />
                    <h3 className="text-xl font-bold text-white">AI Quality Analysis</h3>
                    <Badge
                      className={
                        imageQuality.overall_score >= 8
                          ? 'bg-green-500/20 text-green-300'
                          : imageQuality.overall_score >= 6
                          ? 'bg-yellow-500/20 text-yellow-300'
                          : 'bg-red-500/20 text-red-300'
                      }
                    >
                      {imageQuality.overall_score.toFixed(1)}/10 Overall
                    </Badge>
                  </div>
                  <button
                    onClick={() => setImageQuality(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Sun className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm text-slate-400">Brightness</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {imageQuality.brightness_score.toFixed(1)}/10
                    </p>
                  </div>

                  <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-blue-400" />
                      <span className="text-sm text-slate-400">Sharpness</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {imageQuality.sharpness_score.toFixed(1)}/10
                    </p>
                  </div>

                  <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Contrast className="w-4 h-4 text-purple-400" />
                      <span className="text-sm text-slate-400">Contrast</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {imageQuality.contrast_score.toFixed(1)}/10
                    </p>
                  </div>
                </div>

                {imageQuality.suggestions.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-white mb-2">AI Suggestions:</h4>
                    <ul className="space-y-1">
                      {imageQuality.suggestions.map((suggestion, index) => (
                        <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                          <span className="text-violet-400">•</span>
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Button
                  icon={Zap}
                  onClick={autoEnhanceWithAI}
                  disabled={processing}
                  className="w-full"
                >
                  Auto-Enhance with AI
                </Button>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action Toolbar */}
        {images.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <button
                    onClick={selectAll}
                    className="text-sm text-violet-400 hover:text-violet-300 font-medium transition-colors"
                  >
                    {selectedImages.size === images.length ? 'Deselect All' : 'Select All'}
                  </button>
                  {selectedImages.size > 0 && (
                    <span className="text-sm text-slate-400">
                      {selectedImages.size} image{selectedImages.size !== 1 ? 's' : ''} selected
                    </span>
                  )}
                </div>
              </div>

          <div className="flex flex-wrap gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setEditMode(editMode === 'crop' ? null : 'crop')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                editMode === 'crop'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <Crop className="w-4 h-4" />
              Crop
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setEditMode(editMode === 'rotate' ? null : 'rotate')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                editMode === 'rotate'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <RotateCw className="w-4 h-4" />
              Rotate
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setEditMode(editMode === 'adjust' ? null : 'adjust')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                editMode === 'adjust'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <Sliders className="w-4 h-4" />
              Adjust
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setEditMode(editMode === 'watermark' ? null : 'watermark')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                editMode === 'watermark'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <Type className="w-4 h-4" />
              Watermark
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setEditMode(editMode === 'background' ? null : 'background')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                editMode === 'background'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <Eraser className="w-4 h-4" />
              Remove BG
            </motion.button>
          </div>
            </GlassCard>
          </motion.div>
        )}

      {/* Edit Panel */}
      <AnimatePresence>
        {editMode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div className="space-y-6">
              {editMode === 'rotate' && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Rotate Images
                  </h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Rotation Angle
                    </label>
                    <div className="flex gap-3">
                      {[90, 180, 270, -90].map((angle) => (
                        <button
                          key={angle}
                          onClick={() => setRotateAngle(angle)}
                          className={`px-4 py-2 rounded-lg transition-colors ${
                            rotateAngle === angle
                              ? 'bg-primary-600 text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {angle}°
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {editMode === 'crop' && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Crop Images
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        X Position
                      </label>
                      <input
                        type="number"
                        value={cropSettings.x}
                        onChange={(e) => setCropSettings({ ...cropSettings, x: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Y Position
                      </label>
                      <input
                        type="number"
                        value={cropSettings.y}
                        onChange={(e) => setCropSettings({ ...cropSettings, y: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Width
                      </label>
                      <input
                        type="number"
                        value={cropSettings.width}
                        onChange={(e) => setCropSettings({ ...cropSettings, width: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Height
                      </label>
                      <input
                        type="number"
                        value={cropSettings.height}
                        onChange={(e) => setCropSettings({ ...cropSettings, height: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg"
                      />
                    </div>
                  </div>
                </>
              )}

              {editMode === 'adjust' && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Adjust Images
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        <Sun className="w-4 h-4" />
                        Brightness: {adjustSettings.brightness.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={adjustSettings.brightness}
                        onChange={(e) => setAdjustSettings({ ...adjustSettings, brightness: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        <Contrast className="w-4 h-4" />
                        Contrast: {adjustSettings.contrast.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={adjustSettings.contrast}
                        onChange={(e) => setAdjustSettings({ ...adjustSettings, contrast: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        <Droplet className="w-4 h-4" />
                        Saturation: {adjustSettings.saturation.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={adjustSettings.saturation}
                        onChange={(e) => setAdjustSettings({ ...adjustSettings, saturation: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                    </div>
                  </div>

                  {/* Presets */}
                  {presets.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Quick Presets
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {presets.map((preset) => (
                          <button
                            key={preset.id}
                            onClick={() => applyPreset(preset)}
                            className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
                          >
                            <Sparkles className="w-3 h-3 inline mr-1" />
                            {preset.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {editMode === 'watermark' && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Add Watermark
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Watermark Text
                      </label>
                      <input
                        type="text"
                        value={watermarkSettings.text}
                        onChange={(e) => setWatermarkSettings({ ...watermarkSettings, text: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg"
                        placeholder="@YourUsername"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Position
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { value: 'top-left', label: 'Top Left' },
                          { value: 'top-right', label: 'Top Right' },
                          { value: 'center', label: 'Center' },
                          { value: 'bottom-left', label: 'Bottom Left' },
                          { value: 'bottom-right', label: 'Bottom Right' },
                        ].map((pos) => (
                          <button
                            key={pos.value}
                            onClick={() => setWatermarkSettings({ ...watermarkSettings, position: pos.value as any })}
                            className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                              watermarkSettings.position === pos.value
                                ? 'bg-primary-600 text-white'
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            {pos.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Opacity: {(watermarkSettings.opacity * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={watermarkSettings.opacity}
                        onChange={(e) => setWatermarkSettings({ ...watermarkSettings, opacity: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Font Size: {watermarkSettings.fontSize}px
                      </label>
                      <input
                        type="range"
                        min="12"
                        max="72"
                        step="2"
                        value={watermarkSettings.fontSize}
                        onChange={(e) => setWatermarkSettings({ ...watermarkSettings, fontSize: parseInt(e.target.value) })}
                        className="w-full"
                      />
                    </div>
                  </div>
                </>
              )}

              {editMode === 'background' && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Remove Background
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    This will automatically remove the background from all selected images.
                    The process uses AI and may take a few moments per image.
                  </p>
                </>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => setEditMode(null)}
                  disabled={processing}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
                <button
                  onClick={executeEditAction}
                  disabled={processing || selectedImages.size === 0}
                  className="flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                  Apply to {selectedImages.size} image{selectedImages.size !== 1 ? 's' : ''}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Image Grid */}
      {images.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
        >
          {images.map((image, index) => (
            <motion.div
              key={image.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => toggleImageSelection(image.id)}
              className={`relative aspect-square rounded-lg overflow-hidden cursor-pointer transition-all ${
                selectedImages.has(image.id)
                  ? 'ring-4 ring-primary-600 scale-95'
                  : 'hover:scale-105'
              }`}
            >
              <img
                src={image.url}
                alt={image.name}
                className="w-full h-full object-cover"
              />
              {selectedImages.has(image.id) && (
                <div className="absolute inset-0 bg-primary-600/20 flex items-center justify-center">
                  <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                    <Check className="w-5 h-5 text-white" />
                  </div>
                </div>
              )}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
                <p className="text-white text-xs truncate">{image.name}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <ImageIcon className="w-20 h-20 text-gray-300 dark:text-gray-600 mx-auto mb-6" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            No images uploaded
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Upload images to start editing them in bulk
          </p>
          <label className="cursor-pointer">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Upload className="w-5 h-5" />
              Upload Your First Images
            </motion.div>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </motion.div>
      )}
      </div>
    </div>
  );
}
