import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  RotateCw,
  FlipHorizontal,
  FlipVertical,
  Crop,
  Sliders,
  Wand2,
  Download,
  Undo2,
  Redo2,
  Check,
  ZoomIn,
  ZoomOut,
  Maximize2,
} from 'lucide-react';

interface ImageEditorProps {
  image: string;
  onSave: (editedImage: string) => void;
  onClose: () => void;
}

type Tool = 'crop' | 'adjust' | 'filter' | 'rotate';

interface Adjustments {
  brightness: number;
  contrast: number;
  saturation: number;
  blur: number;
  hue: number;
}

interface CropBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

const ASPECT_RATIOS = [
  { label: 'Free', value: null },
  { label: '1:1', value: 1 },
  { label: '4:3', value: 4 / 3 },
  { label: '16:9', value: 16 / 9 },
  { label: '3:4', value: 3 / 4 },
  { label: '9:16', value: 9 / 16 },
];

const FILTERS = [
  { name: 'None', filter: '' },
  { name: 'Grayscale', filter: 'grayscale(100%)' },
  { name: 'Sepia', filter: 'sepia(100%)' },
  { name: 'Vintage', filter: 'sepia(50%) contrast(110%) brightness(110%)' },
  { name: 'Cool', filter: 'brightness(110%) contrast(110%) hue-rotate(180deg)' },
  { name: 'Warm', filter: 'brightness(110%) contrast(110%) sepia(30%)' },
  { name: 'High Contrast', filter: 'contrast(150%)' },
  { name: 'Vivid', filter: 'saturate(150%) contrast(110%)' },
];

export default function ImageEditor({ image, onSave, onClose }: ImageEditorProps) {
  const [activeTool, setActiveTool] = useState<Tool | null>(null);
  const [rotation, setRotation] = useState(0);
  const [flipH, setFlipH] = useState(false);
  const [flipV, setFlipV] = useState(false);
  const [zoom, setZoom] = useState(1);

  const [adjustments, setAdjustments] = useState<Adjustments>({
    brightness: 100,
    contrast: 100,
    saturation: 100,
    blur: 0,
    hue: 0,
  });

  const [selectedFilter, setSelectedFilter] = useState(0);
  const [cropBox, setCropBox] = useState<CropBox | null>(null);
  const [aspectRatio, setAspectRatio] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [history, setHistory] = useState<string[]>([image]);
  const [historyIndex, setHistoryIndex] = useState(0);

  useEffect(() => {
    loadImage();
  }, [image]);

  const loadImage = () => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = image;
    img.onload = () => {
      if (imageRef.current) {
        imageRef.current = img;
        applyTransformations();
      }
    };
  };

  const applyTransformations = () => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = img.width;
    canvas.height = img.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Apply transformations
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.scale(flipH ? -1 : 1, flipV ? -1 : 1);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);

    // Apply filters
    ctx.filter = `
      brightness(${adjustments.brightness}%)
      contrast(${adjustments.contrast}%)
      saturate(${adjustments.saturation}%)
      blur(${adjustments.blur}px)
      hue-rotate(${adjustments.hue}deg)
      ${FILTERS[selectedFilter].filter}
    `;

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    ctx.restore();
  };

  const handleRotate = (degrees: number) => {
    setRotation((prev) => (prev + degrees) % 360);
    applyTransformations();
  };

  const handleFlip = (direction: 'horizontal' | 'vertical') => {
    if (direction === 'horizontal') {
      setFlipH(!flipH);
    } else {
      setFlipV(!flipV);
    }
    applyTransformations();
  };

  const handleAdjustment = (key: keyof Adjustments, value: number) => {
    setAdjustments((prev) => ({ ...prev, [key]: value }));
    applyTransformations();
  };

  const handleFilter = (index: number) => {
    setSelectedFilter(index);
    applyTransformations();
  };

  const handleCropStart = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (activeTool !== 'crop') return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setDragStart({ x, y });
    setCropBox({ x, y, width: 0, height: 0 });
    setIsDragging(true);
  };

  const handleCropMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging || activeTool !== 'crop') return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let width = x - dragStart.x;
    let height = y - dragStart.y;

    if (aspectRatio) {
      height = width / aspectRatio;
    }

    setCropBox({ x: dragStart.x, y: dragStart.y, width, height });
  };

  const handleCropEnd = () => {
    setIsDragging(false);
  };

  const applyCrop = () => {
    if (!cropBox || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const imageData = ctx.getImageData(
      cropBox.x,
      cropBox.y,
      cropBox.width,
      cropBox.height
    );

    canvas.width = cropBox.width;
    canvas.height = cropBox.height;
    ctx.putImageData(imageData, 0, 0);

    setCropBox(null);
    setActiveTool(null);
    addToHistory();
  };

  const handleSave = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob);
        onSave(url);
      }
    }, 'image/jpeg', 0.95);
  };

  const addToHistory = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dataUrl = canvas.toDataURL();
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(dataUrl);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      const img = new Image();
      img.src = history[historyIndex - 1];
      img.onload = () => {
        imageRef.current = img;
        applyTransformations();
      };
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      const img = new Image();
      img.src = history[historyIndex + 1];
      img.onload = () => {
        imageRef.current = img;
        applyTransformations();
      };
    }
  };

  const handleAutoEnhance = () => {
    setAdjustments({
      brightness: 110,
      contrast: 115,
      saturation: 120,
      blur: 0,
      hue: 0,
    });
    applyTransformations();
    addToHistory();
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/95 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-900 border-b border-gray-800">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-white">Image Editor</h2>

            {/* Undo/Redo */}
            <div className="flex items-center gap-1">
              <button
                onClick={handleUndo}
                disabled={historyIndex === 0}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Undo"
              >
                <Undo2 className="w-5 h-5" />
              </button>
              <button
                onClick={handleRedo}
                disabled={historyIndex === history.length - 1}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Redo"
              >
                <Redo2 className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              Save
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-2 px-6 py-3 bg-gray-900 border-b border-gray-800">
          <button
            onClick={() => setActiveTool(activeTool === 'crop' ? null : 'crop')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              activeTool === 'crop'
                ? 'bg-primary-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Crop className="w-4 h-4" />
            Crop
          </button>

          <button
            onClick={() => handleRotate(90)}
            className="px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors flex items-center gap-2"
          >
            <RotateCw className="w-4 h-4" />
            Rotate
          </button>

          <button
            onClick={() => handleFlip('horizontal')}
            className="px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors flex items-center gap-2"
          >
            <FlipHorizontal className="w-4 h-4" />
            Flip H
          </button>

          <button
            onClick={() => handleFlip('vertical')}
            className="px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors flex items-center gap-2"
          >
            <FlipVertical className="w-4 h-4" />
            Flip V
          </button>

          <button
            onClick={() => setActiveTool(activeTool === 'adjust' ? null : 'adjust')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              activeTool === 'adjust'
                ? 'bg-primary-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Sliders className="w-4 h-4" />
            Adjust
          </button>

          <button
            onClick={() => setActiveTool(activeTool === 'filter' ? null : 'filter')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              activeTool === 'filter'
                ? 'bg-primary-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Wand2 className="w-4 h-4" />
            Filters
          </button>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={handleAutoEnhance}
              className="px-4 py-2 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <Wand2 className="w-4 h-4" />
              Auto Enhance
            </button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Canvas Area */}
          <div
            ref={containerRef}
            className="flex-1 flex items-center justify-center p-6 overflow-auto"
          >
            <div className="relative">
              <canvas
                ref={canvasRef}
                onMouseDown={handleCropStart}
                onMouseMove={handleCropMove}
                onMouseUp={handleCropEnd}
                onMouseLeave={handleCropEnd}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  transform: `scale(${zoom})`,
                  cursor: activeTool === 'crop' ? 'crosshair' : 'default',
                }}
                className="shadow-2xl"
              />

              {/* Crop Box Overlay */}
              {cropBox && activeTool === 'crop' && (
                <div
                  style={{
                    position: 'absolute',
                    left: cropBox.x,
                    top: cropBox.y,
                    width: cropBox.width,
                    height: cropBox.height,
                    border: '2px dashed white',
                    background: 'rgba(99, 102, 241, 0.2)',
                  }}
                />
              )}
            </div>
          </div>

          {/* Right Panel */}
          <AnimatePresence mode="wait">
            {activeTool && (
              <motion.div
                initial={{ x: 300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 300, opacity: 0 }}
                className="w-80 bg-gray-900 border-l border-gray-800 p-6 overflow-y-auto"
              >
                {/* Crop Panel */}
                {activeTool === 'crop' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white mb-4">Crop Image</h3>

                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Aspect Ratio
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {ASPECT_RATIOS.map((ratio) => (
                          <button
                            key={ratio.label}
                            onClick={() => setAspectRatio(ratio.value)}
                            className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                              aspectRatio === ratio.value
                                ? 'bg-primary-600 text-white'
                                : 'bg-gray-800 text-gray-400 hover:text-white'
                            }`}
                          >
                            {ratio.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {cropBox && (
                      <button
                        onClick={applyCrop}
                        className="w-full px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
                      >
                        Apply Crop
                      </button>
                    )}
                  </div>
                )}

                {/* Adjust Panel */}
                {activeTool === 'adjust' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Adjustments</h3>

                    {/* Brightness */}
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Brightness: {adjustments.brightness}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="200"
                        value={adjustments.brightness}
                        onChange={(e) => handleAdjustment('brightness', Number(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Contrast */}
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Contrast: {adjustments.contrast}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="200"
                        value={adjustments.contrast}
                        onChange={(e) => handleAdjustment('contrast', Number(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Saturation */}
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Saturation: {adjustments.saturation}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="200"
                        value={adjustments.saturation}
                        onChange={(e) => handleAdjustment('saturation', Number(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Hue */}
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Hue: {adjustments.hue}°
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="360"
                        value={adjustments.hue}
                        onChange={(e) => handleAdjustment('hue', Number(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Blur */}
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Blur: {adjustments.blur}px
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={adjustments.blur}
                        onChange={(e) => handleAdjustment('blur', Number(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Reset Button */}
                    <button
                      onClick={() => {
                        setAdjustments({
                          brightness: 100,
                          contrast: 100,
                          saturation: 100,
                          blur: 0,
                          hue: 0,
                        });
                        applyTransformations();
                      }}
                      className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
                    >
                      Reset All
                    </button>
                  </div>
                )}

                {/* Filter Panel */}
                {activeTool === 'filter' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>

                    <div className="grid grid-cols-2 gap-3">
                      {FILTERS.map((filter, index) => (
                        <button
                          key={filter.name}
                          onClick={() => handleFilter(index)}
                          className={`relative aspect-square rounded-lg overflow-hidden border-2 transition-all ${
                            selectedFilter === index
                              ? 'border-primary-500 shadow-lg shadow-primary-500/50'
                              : 'border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <div
                            style={{
                              filter: filter.filter,
                              backgroundImage: `url(${image})`,
                              backgroundSize: 'cover',
                              backgroundPosition: 'center',
                            }}
                            className="w-full h-full"
                          />
                          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                            <p className="text-xs font-medium text-white">{filter.name}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom Toolbar - Zoom */}
        <div className="flex items-center justify-center gap-4 px-6 py-3 bg-gray-900 border-t border-gray-800">
          <button
            onClick={() => setZoom(Math.max(0.1, zoom - 0.1))}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ZoomOut className="w-4 h-4" />
          </button>

          <span className="text-sm text-gray-400 min-w-[60px] text-center">
            {Math.round(zoom * 100)}%
          </span>

          <button
            onClick={() => setZoom(Math.min(3, zoom + 0.1))}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <button
            onClick={() => setZoom(1)}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Reset Zoom"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
