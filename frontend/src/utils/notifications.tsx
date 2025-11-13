import toast from 'react-hot-toast';
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

interface ToastOptions {
  duration?: number;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Custom Toast Component
const CustomToast = ({
  type,
  message,
  action,
  onClose
}: {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  onClose: () => void;
}) => {
  const icons = {
    success: <CheckCircle className="w-5 h-5 text-success-600 dark:text-success-400" />,
    error: <AlertCircle className="w-5 h-5 text-error-600 dark:text-error-400" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning-600 dark:text-warning-400" />,
    info: <Info className="w-5 h-5 text-info-600 dark:text-info-400" />,
  };

  const backgrounds = {
    success: 'bg-success-50 dark:bg-success-900/20 border-success-200 dark:border-success-800',
    error: 'bg-error-50 dark:bg-error-900/20 border-error-200 dark:border-error-800',
    warning: 'bg-warning-50 dark:bg-warning-900/20 border-warning-200 dark:border-warning-800',
    info: 'bg-info-50 dark:bg-info-900/20 border-info-200 dark:border-info-800',
  };

  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-lg border shadow-lg min-w-[300px] max-w-md ${backgrounds[type]}`}>
      <div className="flex-shrink-0 mt-0.5">
        {icons[type]}
      </div>

      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900 dark:text-white">
          {message}
        </p>

        {action && (
          <button
            onClick={() => {
              action.onClick();
              onClose();
            }}
            className="mt-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:underline"
          >
            {action.label}
          </button>
        )}
      </div>

      <button
        onClick={onClose}
        className="flex-shrink-0 p-0.5 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
      >
        <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
      </button>
    </div>
  );
};

// Toast Helpers
export const notify = {
  success: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => <CustomToast type="success" message={message} action={options?.action} onClose={() => toast.dismiss(t.id)} />,
      {
        duration: options?.duration || 3000,
        position: options?.position || 'top-right',
      }
    );
  },

  error: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => <CustomToast type="error" message={message} action={options?.action} onClose={() => toast.dismiss(t.id)} />,
      {
        duration: options?.duration || 5000,
        position: options?.position || 'top-right',
      }
    );
  },

  warning: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => <CustomToast type="warning" message={message} action={options?.action} onClose={() => toast.dismiss(t.id)} />,
      {
        duration: options?.duration || 4000,
        position: options?.position || 'top-right',
      }
    );
  },

  info: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => <CustomToast type="info" message={message} action={options?.action} onClose={() => toast.dismiss(t.id)} />,
      {
        duration: options?.duration || 4000,
        position: options?.position || 'top-right',
      }
    );
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    },
    options?: ToastOptions
  ) => {
    return toast.promise(
      promise,
      {
        loading: messages.loading,
        success: messages.success,
        error: messages.error,
      },
      {
        position: options?.position || 'top-right',
      }
    );
  },

  // Specific use cases
  uploadSuccess: (count: number) => {
    notify.success(`${count} photo${count > 1 ? 's' : ''} uploaded successfully!`);
  },

  draftCreated: () => {
    notify.success('Draft created successfully!', {
      action: {
        label: 'View',
        onClick: () => {
          // Navigate to drafts
          window.location.href = '/drafts';
        }
      }
    });
  },

  draftPublished: (title: string) => {
    notify.success(`"${title}" published to Vinted!`, {
      duration: 5000,
    });
  },

  aiAnalysisComplete: () => {
    notify.success('AI analysis complete!', {
      action: {
        label: 'Review',
        onClick: () => {
          // Navigate or open modal
        }
      }
    });
  },

  bulkActionComplete: (action: string, count: number) => {
    notify.success(`${count} draft${count > 1 ? 's' : ''} ${action}!`);
  },

  networkError: () => {
    notify.error('Network error. Please check your connection and try again.', {
      action: {
        label: 'Retry',
        onClick: () => {
          window.location.reload();
        }
      }
    });
  },

  sessionExpired: () => {
    notify.warning('Your session has expired. Please log in again.', {
      duration: 6000,
      action: {
        label: 'Log in',
        onClick: () => {
          window.location.href = '/login';
        }
      }
    });
  },

  quotaReached: (type: string) => {
    notify.warning(`You've reached your ${type} quota.`, {
      duration: 6000,
      action: {
        label: 'Upgrade',
        onClick: () => {
          window.location.href = '/settings?tab=subscription';
        }
      }
    });
  },
};

// Loading state helper
export const withLoading = async <T,>(
  action: () => Promise<T>,
  messages?: {
    loading?: string;
    success?: string | ((data: T) => string);
    error?: string | ((error: any) => string);
  }
): Promise<T> => {
  return toast.promise(
    action(),
    {
      loading: messages?.loading || 'Loading...',
      success: messages?.success || 'Success!',
      error: messages?.error || 'Something went wrong',
    }
  );
};
