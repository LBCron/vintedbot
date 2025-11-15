import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, X, CheckCircle, ImagePlus, Sparkles, Zap } from 'lucide-react';
import { bulkAPI } from '../api/client';
import { showToast } from '../components/Toast';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export default function Upload() {
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);

    acceptedFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        setPreviews((prev) => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });

    showToast.success(`${acceptedFiles.length} photo${acceptedFiles.length > 1 ? 's' : ''} ajoutée${acceptedFiles.length > 1 ? 's' : ''}`);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.heic'] },
    maxFiles: 500,
    maxSize: 15 * 1024 * 1024,
  });

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleUpload = useCallback(async () => {
    if (files.length === 0) {
      showToast.error('Aucune photo sélectionnée');
      return;
    }

    setUploading(true);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('photos_per_item', '6');

    const uploadAndPollPromise = new Promise((resolve, reject) => {
      bulkAPI.uploadPhotos(formData)
        .then((response) => {
          const jobId = response.data.job_id;

          const pollJob = () => {
            bulkAPI.getJob(jobId)
              .then((jobStatus) => {
                setProgress(jobStatus.data.progress_percent);

                if (jobStatus.data.status === 'completed') {
                  setFiles([]);
                  setPreviews([]);
                  setUploading(false);
                  setProgress(0);

                  setTimeout(() => {
                    navigate('/drafts');
                  }, 1000);

                  resolve(jobStatus.data);
                } else if (jobStatus.data.status === 'failed') {
                  setUploading(false);
                  setProgress(0);
                  reject(new Error(jobStatus.data.errors?.join(', ') || 'Upload failed'));
                } else {
                  setTimeout(pollJob, 2000);
                }
              })
              .catch((err) => {
                setUploading(false);
                setProgress(0);
                reject(err);
              });
          };

          pollJob();
        })
        .catch((err) => {
          setUploading(false);
          setProgress(0);
          reject(err);
        });
    });

    showToast.promise(uploadAndPollPromise, {
      loading: `Upload de ${files.length} photo${files.length > 1 ? 's' : ''}...`,
      success: 'Analyse IA terminée ! Redirection...',
      error: (err: any) => `Erreur: ${err?.message || "Upload échoué"}`,
    });
  }, [files, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-6xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          className="space-y-2"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
            Upload Photos
          </h1>
          <p className="text-lg text-slate-400">
            Upload photos and let <span className="text-violet-400 font-semibold">AI</span> create drafts automatically
          </p>
        </motion.div>

        {!uploading ? (
          <>
            {/* Dropzone */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              <div
                {...getRootProps()}
                className={`
                  relative overflow-hidden
                  border-4 border-dashed rounded-2xl p-16 text-center cursor-pointer
                  backdrop-blur-xl transition-all duration-300
                  ${
                    isDragActive
                      ? 'border-violet-500 bg-violet-500/10 shadow-[0_0_40px_rgba(168,85,247,0.3)]'
                      : 'border-white/20 bg-white/5 hover:border-violet-400 hover:bg-white/8 hover:shadow-[0_20px_50px_rgba(0,0,0,0.3)]'
                  }
                `}
              >
                {/* Animated Background Gradient */}
                <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 via-transparent to-purple-500/10 opacity-0 hover:opacity-100 transition-opacity duration-500" />

                <input {...getInputProps()} />

                <motion.div
                  animate={isDragActive ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
                  transition={{ duration: 0.3 }}
                  className="relative z-10"
                >
                  <div className="mx-auto w-24 h-24 bg-gradient-to-br from-violet-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mb-6 border border-violet-500/30">
                    <UploadIcon className="w-12 h-12 text-violet-400" />
                  </div>
                </motion.div>

                {isDragActive ? (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="relative z-10"
                  >
                    <p className="text-2xl font-bold text-violet-400 mb-2">
                      Drop your photos here! 🎯
                    </p>
                    <p className="text-slate-400">
                      Release to start uploading
                    </p>
                  </motion.div>
                ) : (
                  <div className="relative z-10">
                    <h3 className="text-2xl font-bold text-white mb-3">
                      Drag & drop your photos here
                    </h3>
                    <p className="text-slate-400 mb-6">
                      or click to browse files
                    </p>
                    <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500">
                      <Badge variant="default">JPG, PNG, WEBP, HEIC</Badge>
                      <Badge variant="info">Up to 500 photos</Badge>
                      <Badge variant="warning">Max 15MB per photo</Badge>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Preview Grid */}
            {previews.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <GlassCard className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-violet-500/20 border border-violet-500/30">
                        <ImagePlus className="w-5 h-5 text-violet-400" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white">
                          {previews.length} photo{previews.length > 1 ? 's' : ''} ready
                        </h3>
                        <p className="text-sm text-slate-400">
                          Click "Analyze with AI" to start processing
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={handleUpload}
                      disabled={uploading}
                      icon={Sparkles}
                      size="lg"
                    >
                      Analyze with AI
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    <AnimatePresence>
                      {previews.map((preview, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8, rotate: -5 }}
                          transition={{ duration: 0.3 }}
                          className="relative group aspect-square"
                        >
                          {/* Image */}
                          <div className="relative w-full h-full rounded-xl overflow-hidden border-2 border-white/10 group-hover:border-violet-500/50 transition-all duration-300">
                            <img
                              src={preview}
                              alt={`Preview ${index}`}
                              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                            />
                            {/* Overlay on hover */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                          </div>

                          {/* Badge Number */}
                          <div className="absolute top-2 left-2 z-10">
                            <Badge variant="default" size="sm">
                              #{index + 1}
                            </Badge>
                          </div>

                          {/* Delete Button */}
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => removeFile(index)}
                            className="absolute top-2 right-2 z-10 p-1.5 bg-red-500 text-white rounded-lg
                                     opacity-0 group-hover:opacity-100 transition-all hover:bg-red-600 shadow-lg"
                          >
                            <X className="w-4 h-4" />
                          </motion.button>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </>
        ) : (
          /* Upload Progress */
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <GlassCard className="p-12 text-center">
              {progress < 100 ? (
                <div className="space-y-8">
                  {/* Animated Icon */}
                  <motion.div
                    animate={{
                      rotate: 360,
                      scale: [1, 1.1, 1]
                    }}
                    transition={{
                      rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                      scale: { duration: 1, repeat: Infinity }
                    }}
                    className="mx-auto w-24 h-24 bg-gradient-to-br from-violet-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center border border-violet-500/30"
                  >
                    <Sparkles className="w-12 h-12 text-violet-400" />
                  </motion.div>

                  {/* Text */}
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">
                      AI is analyzing your photos...
                    </h3>
                    <p className="text-slate-400">
                      Creating smart drafts with GPT-4 Vision
                    </p>
                  </div>

                  {/* Progress Bar */}
                  <div className="max-w-md mx-auto space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Progress</span>
                      <span className="text-violet-400 font-bold">{Math.round(progress)}%</span>
                    </div>
                    <div className="h-3 bg-white/5 rounded-full overflow-hidden border border-white/10">
                      <motion.div
                        className="h-full bg-gradient-to-r from-violet-500 to-purple-600 rounded-full shadow-[0_0_20px_rgba(168,85,247,0.5)]"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-2xl font-bold text-white">{files.length}</div>
                      <div className="text-xs text-slate-400">Photos</div>
                    </div>
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-2xl font-bold text-violet-400">
                        <Zap className="w-6 h-6 mx-auto" />
                      </div>
                      <div className="text-xs text-slate-400">AI Power</div>
                    </div>
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-2xl font-bold text-white">~{Math.ceil(files.length / 6)}</div>
                      <div className="text-xs text-slate-400">Drafts</div>
                    </div>
                  </div>
                </div>
              ) : (
                /* Success State */
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', damping: 10, delay: 0.2 }}
                  className="space-y-6"
                >
                  <motion.div
                    animate={{
                      scale: [1, 1.2, 1],
                    }}
                    transition={{
                      duration: 0.5,
                      repeat: 2
                    }}
                    className="mx-auto w-24 h-24 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-2xl flex items-center justify-center border border-green-500/30"
                  >
                    <CheckCircle className="w-12 h-12 text-green-400" />
                  </motion.div>
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">
                      Upload Complete! 🎉
                    </h3>
                    <p className="text-slate-400">
                      Redirecting to your drafts...
                    </p>
                  </div>
                </motion.div>
              )}
            </GlassCard>
          </motion.div>
        )}
      </div>
    </div>
  );
}
