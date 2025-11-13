import toast, { Toaster } from 'react-hot-toast';

export const ToastProvider = () => (
  <Toaster
    position="top-right"
    toastOptions={{
      duration: 4000,
      style: {
        background: '#363636',
        color: '#fff',
        borderRadius: '0.5rem',
        padding: '16px',
      },
      success: {
        duration: 3000,
        iconTheme: { primary: '#10b981', secondary: '#fff' },
      },
      error: {
        duration: 5000,
        iconTheme: { primary: '#ef4444', secondary: '#fff' },
      },
      loading: {
        iconTheme: { primary: '#3b82f6', secondary: '#fff' },
      },
    }}
  />
);

export const showToast = {
  success: (message: string) => toast.success(message),
  error: (message: string) => toast.error(message),
  loading: (message: string) => toast.loading(message),
  promise: <T,>(
    promise: Promise<T>,
    messages: { 
      loading: string; 
      success: string | ((data: T) => string); 
      error: string | ((error: any) => string);
    }
  ) => toast.promise(promise, messages),
  dismiss: (toastId?: string) => toast.dismiss(toastId),
};
