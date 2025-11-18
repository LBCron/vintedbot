import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './contexts/AuthContext';
import { CommandPaletteProvider, useCommandPalette } from './contexts/CommandPaletteContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import LoadingSpinner from './components/common/LoadingSpinner';
import CommandPalette from './components/CommandPalette';

const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Upload = lazy(() => import('./pages/Upload'));
const Drafts = lazy(() => import('./pages/Drafts'));
const DraftEdit = lazy(() => import('./pages/DraftEdit'));
const DraftDetail = lazy(() => import('./pages/DraftDetail'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Automation = lazy(() => import('./pages/Automation'));
const Accounts = lazy(() => import('./pages/Accounts'));
const Settings = lazy(() => import('./pages/Settings'));
const Admin = lazy(() => import('./pages/Admin'));
const FeedbackPage = lazy(() => import('./pages/Feedback'));
const Templates = lazy(() => import('./pages/Templates'));
const HelpCenter = lazy(() => import('./pages/HelpCenter'));
const Publish = lazy(() => import('./pages/Publish'));
const Messages = lazy(() => import('./pages/Messages'));
const History = lazy(() => import('./pages/History'));
const Orders = lazy(() => import('./pages/Orders'));
const ImageEditor = lazy(() => import('./pages/ImageEditor'));
// const StorageStats = lazy(() => import('./pages/StorageStatsPage'));

const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <LoadingSpinner size="large" />
  </div>
);

function AppContent() {
  const { isOpen, close } = useCommandPalette();

  return (
    <>
      <CommandPalette open={isOpen} onClose={close} />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#363636',
            padding: '16px',
            borderRadius: '8px',
            fontSize: '14px',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="/drafts" element={<ProtectedRoute><Drafts /></ProtectedRoute>} />
          <Route path="/drafts/:id" element={<ProtectedRoute><DraftEdit /></ProtectedRoute>} />
          <Route path="/draft-detail/:id" element={<ProtectedRoute><DraftDetail /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/automation" element={<ProtectedRoute><Automation /></ProtectedRoute>} />
          <Route path="/accounts" element={<ProtectedRoute><Accounts /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />
          <Route path="/feedback" element={<ProtectedRoute><FeedbackPage /></ProtectedRoute>} />
          <Route path="/templates" element={<ProtectedRoute><Templates /></ProtectedRoute>} />
          <Route path="/help" element={<ProtectedRoute><HelpCenter /></ProtectedRoute>} />
          <Route path="/publish" element={<ProtectedRoute><Publish /></ProtectedRoute>} />
          <Route path="/messages" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
          <Route path="/image-editor" element={<ProtectedRoute><ImageEditor /></ProtectedRoute>} />
          {/* <Route path="/storage" element={<ProtectedRoute><StorageStats /></ProtectedRoute>} /> */}

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </>
  );
}

function App() {
  const { loading } = useAuth();

  if (loading) {
    return <PageLoader />;
  }

  return (
    <CommandPaletteProvider>
      <AppContent />
    </CommandPaletteProvider>
  );
}

export default App;
