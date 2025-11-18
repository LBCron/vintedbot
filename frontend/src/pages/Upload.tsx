import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, X, CheckCircle, ImagePlus, Sparkles, RotateCw } from 'lucide-react';
import { bulkAPI } from '../api/client';
import { showToast } from '../components/Toast';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Progress from '../components/common/Progress';
import { Badge } from '../components/common/Badge';

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
    <div className="max-w-6xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Upload Photos</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Upload photos of your items and let AI create drafts automatically
        </p>
      </motion.div>

      {!uploading ? (
        <>
          <div
            {...getRootProps()}
            className={`
              border-4 border-dashed rounded-xl p-12 text-center cursor-pointer
              transition-all duration-300
              ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800'
              }
            `}
          >
            <input {...getInputProps()} />
            <motion.div
              animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
              transition={{ duration: 0.2 }}
            >
              <UploadIcon className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
            </motion.div>

            {isDragActive ? (
              <p className="text-xl font-semibold text-primary-600 dark:text-primary-400">
                Déposez vos photos ici !
              </p>
            ) : (
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Glissez vos photos ici ou cliquez pour sélectionner
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  JPG, PNG, WEBP, HEIC • Maximum 500 photos • Max 15MB par photo
                </p>
              </div>
            )}
          </div>

          {previews.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {previews.length} photo{previews.length > 1 ? 's' : ''} sélectionnée
                  {previews.length > 1 ? 's' : ''}
                </h3>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700
                           disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                >
                  {uploading ? 'Upload en cours...' : 'Analyser avec IA'}
                </motion.button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <AnimatePresence>
                  {previews.map((preview, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.2 }}
                      className="relative group aspect-square"
                    >
                      <img
                        src={preview}
                        alt={`Preview ${index}`}
                        className="w-full h-full object-cover rounded-lg border-2 border-gray-200 dark:border-gray-700"
                      />
                      <div className="absolute top-2 left-2">
                        <Badge variant="default" size="sm">
                          #{index + 1}
                        </Badge>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => removeFile(index)}
                        className="absolute top-2 right-2 p-1.5 bg-error-500 text-white rounded-lg
                                 opacity-0 group-hover:opacity-100 transition-all hover:bg-error-600 shadow-lg"
                      >
                        <X className="w-4 h-4" />
                      </motion.button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card text-center space-y-6"
        >
          {progress < 100 ? (
            <>
              <LoadingSpinner size="large" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Processing Photos...
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  AI is analyzing your items and creating drafts
                </p>
              </div>
              <Progress
                value={progress}
                max={100}
                size="lg"
                variant="gradient"
                showLabel
                label="AI Analysis Progress"
                className="max-w-md mx-auto"
              />
            </>
          ) : (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', damping: 10 }}
            >
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-4">
                  Upload Complete!
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  Redirecting to drafts...
                </p>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  );
}
