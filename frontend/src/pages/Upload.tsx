import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload as UploadIcon,
  X,
  CheckCircle,
  ImagePlus,
  Sparkles,
  Zap,
  Brain,
  Clock,
  Wand2,
  FileText
} from 'lucide-react';
import { bulkAPI } from '@/api/client';
import { showToast } from '@/components/Toast';
import { cn } from '@/lib/utils';

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
    showToast.success('Photo retirée');
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
                  }, 1500);

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
      loading: `Analyse IA de ${files.length} photo${files.length > 1 ? 's' : ''}...`,
      success: 'Analyse IA terminée ! Redirection...',
      error: (err: any) => `Erreur: ${err?.message || "Upload échoué"}`,
    });
  }, [files, navigate]);

  return (
    <div className="min-h-screen bg-gray-50 -m-8">
      {/* Header avec gradient */}
      <div className="bg-gradient-to-br from-brand-600 via-purple-600 to-brand-700 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', delay: 0.2 }}
                className="w-14 h-14 bg-white/20 rounded-2xl backdrop-blur-sm flex items-center justify-center"
              >
                <ImagePlus className="w-8 h-8" />
              </motion.div>
              <h1 className="text-4xl font-bold">Upload Photos</h1>
            </div>
            <p className="text-brand-100 text-lg">
              Uploadez vos photos et laissez l'IA créer vos brouillons automatiquement
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-8 pb-12">
        {!uploading ? (
          <div className="space-y-8">
            {/* Drag & Drop Zone */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              {...getRootProps()}
              className={cn(
                "relative overflow-hidden bg-white border-4 border-dashed rounded-3xl p-16 text-center cursor-pointer transition-all duration-300 shadow-sm",
                isDragActive
                  ? "border-brand-500 bg-brand-50 shadow-xl scale-[1.02]"
                  : "border-gray-300 hover:border-brand-400 hover:bg-gray-50 hover:shadow-lg"
              )}
            >
              <input {...getInputProps()} />

              {/* Background Animation */}
              {isDragActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0 bg-gradient-to-br from-brand-100 to-purple-100 -z-10"
                />
              )}

              <motion.div
                animate={isDragActive ? { scale: 1.2, rotate: 5 } : { scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 300 }}
              >
                <div className={cn(
                  "w-24 h-24 mx-auto mb-6 rounded-3xl flex items-center justify-center transition-colors",
                  isDragActive ? "bg-brand-500" : "bg-gradient-to-br from-brand-500 to-purple-600"
                )}>
                  <UploadIcon className="w-12 h-12 text-white" />
                </div>
              </motion.div>

              {isDragActive ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h3 className="text-2xl font-bold text-brand-600 mb-2">
                    Déposez vos photos ici !
                  </h3>
                  <p className="text-brand-500">
                    On s'occupe du reste
                  </p>
                </motion.div>
              ) : (
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    Glissez vos photos ici
                  </h3>
                  <p className="text-lg text-gray-600 mb-4">
                    ou cliquez pour sélectionner
                  </p>
                  <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                    <span className="px-3 py-1 bg-gray-100 rounded-full">JPG, PNG, WEBP, HEIC</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full">Max 500 photos</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full">15MB/photo</span>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Preview Grid */}
            {previews.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-3xl p-8 border border-gray-200 shadow-sm"
              >
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">
                      {previews.length} photo{previews.length > 1 ? 's' : ''} prête{previews.length > 1 ? 's' : ''}
                    </h3>
                    <p className="text-gray-600 mt-1">
                      L'IA va analyser et créer vos brouillons automatiquement
                    </p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleUpload}
                    className="bg-gradient-to-r from-brand-600 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2 text-lg"
                  >
                    <Sparkles className="w-5 h-5" />
                    Analyser avec l'IA
                  </motion.button>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  <AnimatePresence>
                    {previews.map((preview, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8, rotate: -5 }}
                        transition={{ duration: 0.2 }}
                        whileHover={{ scale: 1.05, y: -4 }}
                        className="relative group aspect-square"
                      >
                        <img
                          src={preview}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-full object-cover rounded-xl border-2 border-gray-200 shadow-sm group-hover:shadow-md transition-shadow"
                        />

                        {/* Number Badge */}
                        <div className="absolute top-2 left-2 bg-brand-600 text-white text-xs font-bold px-2 py-1 rounded-lg">
                          #{index + 1}
                        </div>

                        {/* Remove Button */}
                        <motion.button
                          initial={{ opacity: 0, scale: 0 }}
                          animate={{ opacity: 0, scale: 0 }}
                          whileHover={{ opacity: 1, scale: 1 }}
                          onClick={() => removeFile(index)}
                          className="absolute top-2 right-2 p-2 bg-error-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all hover:bg-error-600 shadow-lg"
                        >
                          <X className="w-4 h-4" />
                        </motion.button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}

            {/* Feature Cards - Only show when no files */}
            {previews.length === 0 && (
              <div className="grid md:grid-cols-3 gap-6">
                {[
                  {
                    icon: Brain,
                    title: 'IA Puissante',
                    description: 'Détection automatique des articles et génération des descriptions',
                    color: 'from-purple-500 to-brand-600'
                  },
                  {
                    icon: Zap,
                    title: 'Ultra Rapide',
                    description: 'Traitement en quelques secondes, pas besoin d\'attendre',
                    color: 'from-brand-500 to-purple-600'
                  },
                  {
                    icon: FileText,
                    title: 'Brouillons Prêts',
                    description: 'Titres, descriptions et prix générés automatiquement',
                    color: 'from-purple-600 to-brand-500'
                  }
                ].map((feature, index) => (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    whileHover={{ y: -8, scale: 1.02 }}
                    className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-lg transition-all cursor-default"
                  >
                    <div className={cn(
                      "w-14 h-14 rounded-xl bg-gradient-to-br flex items-center justify-center mb-4",
                      feature.color
                    )}>
                      <feature.icon className="w-7 h-7 text-white" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">{feature.title}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-12 border border-gray-200 shadow-sm"
          >
            {progress < 100 ? (
              <div className="text-center space-y-8">
                {/* Animated Icon */}
                <motion.div
                  animate={{
                    rotate: [0, 360],
                    scale: [1, 1.1, 1]
                  }}
                  transition={{
                    rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                    scale: { duration: 1.5, repeat: Infinity }
                  }}
                  className="w-24 h-24 mx-auto bg-gradient-to-br from-brand-500 to-purple-600 rounded-3xl flex items-center justify-center"
                >
                  <Wand2 className="w-12 h-12 text-white" />
                </motion.div>

                <div>
                  <h3 className="text-3xl font-bold text-gray-900 mb-3">
                    Analyse IA en cours...
                  </h3>
                  <p className="text-lg text-gray-600">
                    L'IA analyse vos photos et génère les brouillons
                  </p>
                </div>

                {/* Progress Bar */}
                <div className="max-w-md mx-auto">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Progression</span>
                    <span className="text-sm font-bold text-brand-600">{progress}%</span>
                  </div>
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3 }}
                      className="h-full bg-gradient-to-r from-brand-500 via-purple-500 to-brand-600 rounded-full"
                    />
                  </div>
                </div>

                {/* Processing Steps */}
                <div className="flex justify-center gap-8 text-sm">
                  <div className={cn(
                    "flex items-center gap-2",
                    progress > 20 ? "text-brand-600" : "text-gray-400"
                  )}>
                    <CheckCircle className="w-5 h-5" />
                    <span>Upload</span>
                  </div>
                  <div className={cn(
                    "flex items-center gap-2",
                    progress > 60 ? "text-brand-600" : "text-gray-400"
                  )}>
                    <CheckCircle className="w-5 h-5" />
                    <span>Analyse IA</span>
                  </div>
                  <div className={cn(
                    "flex items-center gap-2",
                    progress > 90 ? "text-brand-600" : "text-gray-400"
                  )}>
                    <CheckCircle className="w-5 h-5" />
                    <span>Brouillons</span>
                  </div>
                </div>
              </div>
            ) : (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', damping: 10 }}
                className="text-center space-y-6"
              >
                <motion.div
                  animate={{
                    scale: [1, 1.2, 1],
                    rotate: [0, 360]
                  }}
                  transition={{
                    duration: 0.6
                  }}
                >
                  <CheckCircle className="w-24 h-24 text-success-500 mx-auto" />
                </motion.div>

                <div>
                  <h3 className="text-3xl font-bold text-gray-900 mb-3">
                    C'est fait !
                  </h3>
                  <p className="text-lg text-gray-600">
                    Vos brouillons sont prêts, redirection en cours...
                  </p>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
