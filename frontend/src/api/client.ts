import axios from 'axios';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  BulkUploadResponse,
  BulkJobStatus,
  DraftListResponse,
  Draft,
  AnalyticsResponse,
  AutomationRule,
  VintedAccount,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // Keep for CORS
});

// Request interceptor: add JWT token from localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: redirect to login on 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear and redirect to login
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data: RegisterRequest) =>
    apiClient.post<TokenResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/auth/login', data),

  logout: () =>
    apiClient.post('/auth/logout'),

  getMe: () =>
    apiClient.get<User>('/auth/me'),
};

export const bulkAPI = {
  uploadPhotos: (formData: FormData) =>
    apiClient.post<BulkUploadResponse>('/bulk/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  getJob: (jobId: string) =>
    apiClient.get<BulkJobStatus>(`/bulk/jobs/${jobId}`),
  
  getDrafts: (params?: { status?: string; page?: number; page_size?: number }) =>
    apiClient.get<DraftListResponse>('/bulk/drafts', { params }),
  
  getDraft: (draftId: string) =>
    apiClient.get<Draft>(`/bulk/drafts/${draftId}`),
  
  updateDraft: (draftId: string, data: Partial<Draft>) =>
    apiClient.patch<Draft>(`/bulk/drafts/${draftId}`, data),

  reorderPhotos: (draftId: string, photos: string[]) =>
    apiClient.patch(`/bulk/drafts/${draftId}/photos/reorder`, { photos }),

  addPhotos: (draftId: string, files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return apiClient.post(`/bulk/drafts/${draftId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  publishDraft: (draftId: string) =>
    apiClient.post(`/bulk/drafts/${draftId}/publish`),

  // Sprint 1 Feature: Optimized 1-click direct publish
  publishDraftDirect: (draftId: string, publishMode: 'auto' | 'draft' = 'auto') =>
    apiClient.post(`/bulk/drafts/${draftId}/publish-direct`, null, {
      params: { publish_mode: publishMode }
    }),

  deleteDraft: (draftId: string) =>
    apiClient.delete(`/bulk/drafts/${draftId}`),
};

export const analyticsAPI = {
  getDashboard: (days: number = 30) =>
    apiClient.get<AnalyticsResponse>('/analytics/dashboard', { params: { days } }),
  
  trackView: (listing_id: string, source: string = 'organic') =>
    apiClient.post('/analytics/events/view', { listing_id, source }),
  
  trackLike: (listing_id: string) =>
    apiClient.post('/analytics/events/like', { listing_id }),
  
  trackMessage: (listing_id: string) =>
    apiClient.post('/analytics/events/message', { listing_id }),
  
  trackSale: (listing_id: string) =>
    apiClient.post('/analytics/events/sale', { listing_id }),
};

export const automationAPI = {
  getRules: () =>
    apiClient.get<AutomationRule[]>('/automation/rules'),
  
  createRule: (data: Partial<AutomationRule>) =>
    apiClient.post<AutomationRule>('/automation/rules', data),
  
  updateRule: (ruleId: string, data: Partial<AutomationRule>) =>
    apiClient.put<AutomationRule>(`/automation/rules/${ruleId}`, data),
  
  deleteRule: (ruleId: string) =>
    apiClient.delete(`/automation/rules/${ruleId}`),
  
  executeBump: (listing_ids: string[]) =>
    apiClient.post('/automation/bump/execute', { listing_ids }),
  
  executeFollow: (user_ids: string[]) =>
    apiClient.post('/automation/follow/execute', { user_ids }),
  
  configureBump: (config: any) =>
    apiClient.post('/automation/bump/config', config),
  
  configureFollow: (config: any) =>
    apiClient.post('/automation/follow/config', config),
  
  configureMessages: (config: any) =>
    apiClient.post('/automation/messages/config', config),

  getSummary: () =>
    apiClient.get('/automation/summary'),

  // Upselling (Dotb feature)
  configureUpsell: (config: {
    enabled: boolean;
    trigger: string;
    delay_days: number;
    message_template: string;
    max_items_to_suggest: number;
    daily_limit: number;
    exclude_categories?: string[];
  }) =>
    apiClient.post('/automation/upsell/config', config),

  executeUpsell: (order_ids: string[]) =>
    apiClient.post('/automation/upsell/execute', order_ids),

  getUpsellTemplates: () =>
    apiClient.get('/automation/upsell/templates'),
};

export const accountsAPI = {
  getAccounts: () =>
    apiClient.get<VintedAccount[]>('/accounts/list'),

  addAccount: (data: { nickname: string; cookie: string; user_agent: string }) =>
    apiClient.post('/accounts/add', data),

  vintedAutoLogin: (data: { email: string; password: string; nickname?: string; is_default?: boolean }) =>
    apiClient.post('/accounts/vinted-login', data),

  switchAccount: (accountId: string) =>
    apiClient.post(`/accounts/${accountId}/switch`),

  deleteAccount: (accountId: string) =>
    apiClient.delete(`/accounts/${accountId}`),
};

export const billingAPI = {
  createCheckout: (tier: string, success_url: string, cancel_url: string) =>
    apiClient.post('/billing/checkout', { tier, success_url, cancel_url }),

  createPortal: (return_url: string) =>
    apiClient.post('/billing/portal', { return_url }),

  getSubscription: () =>
    apiClient.get('/billing/subscription'),
};

export const vintedAPI = {
  saveSession: (cookie: string) =>
    apiClient.post('/vinted/auth/session', { cookie }),

  testSession: () =>
    apiClient.post('/vinted/session/test'),

  clearSession: () =>
    apiClient.delete('/vinted/auth/session'),
};

export const messagesAPI = {
  getThreads: (params?: { since?: string; limit?: number; offset?: number }) =>
    apiClient.get('/vinted/messages', { params }),

  getThreadMessages: (threadId: string, params?: { limit?: number; offset?: number }) =>
    apiClient.get(`/vinted/messages/${threadId}`, { params }),

  replyToThread: (threadId: string, data: { session_id: number; text: string; send_mode?: string }) =>
    apiClient.post(`/vinted/messages/${threadId}/reply`, data),

  sendAttachment: (formData: FormData) =>
    apiClient.post('/vinted/messages/send-attachment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  bulkMarkRead: (threadIds: string[]) =>
    apiClient.post('/vinted/messages/bulk-mark-read', { thread_ids: threadIds }),

  getNotifications: () =>
    apiClient.get('/vinted/messages/notifications'),
};

export const adminAPI = {
  // Users Management
  getUsers: (params?: { page?: number; page_size?: number; search?: string }) =>
    apiClient.get('/admin/users', { params }),

  getUsersStats: () =>
    apiClient.get('/admin/users/stats'),

  deleteUser: (userId: string) =>
    apiClient.delete(`/admin/users/${userId}`),

  changePlan: (userId: string, plan: string) =>
    apiClient.post(`/admin/users/${userId}/change-plan`, { plan }),

  impersonate: (userId: string) =>
    apiClient.post('/admin/impersonate', { user_id: userId }),

  // System Management
  getSystemStats: () =>
    apiClient.get('/admin/system/stats'),

  createBackup: () =>
    apiClient.post('/admin/system/backup'),

  getBackups: () =>
    apiClient.get('/admin/system/backups'),

  getSystemLogs: (params?: { level?: string; limit?: number }) =>
    apiClient.get('/admin/system/logs', { params }),

  getMetrics: () =>
    apiClient.get('/admin/system/metrics'),

  clearCache: () =>
    apiClient.post('/admin/system/cache/clear'),

  // Analytics & Monitoring
  getAllAnalytics: () =>
    apiClient.get('/admin/analytics/all'),

  getAICosts: () =>
    apiClient.get('/admin/ai/costs'),

  // Telegram (future)
  sendMessage: (userId: string, message: string) =>
    apiClient.post('/admin/message/send', { user_id: userId, message }),
};

export const ordersAPI = {
  // List orders with pagination and filtering
  listOrders: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiClient.get('/orders/list', { params }),

  // Get order statistics
  getStats: () =>
    apiClient.get('/orders/stats'),

  // Export orders to CSV
  exportCSV: (params?: { status?: string; from_date?: string; to_date?: string }) =>
    apiClient.get('/orders/export/csv', {
      params,
      responseType: 'blob'  // Important for file download
    }),

  // Send bulk feedback to multiple orders (Dotb feature)
  sendBulkFeedback: (data: {
    order_ids: string[];
    rating: number;
    comment: string;
    auto_mark_complete?: boolean;
  }) =>
    apiClient.post('/orders/bulk-feedback', data),

  // Get predefined feedback templates
  getFeedbackTemplates: () =>
    apiClient.get('/orders/feedback/templates'),

  // Bulk shipping labels download (Dotb feature)
  downloadBulkLabels: (order_ids: string[]) =>
    apiClient.post('/orders/bulk-labels', order_ids, {
      responseType: 'blob'  // For PDF download
    }),

  // Get orders with available shipping labels
  getAvailableLabels: (status: string = 'shipped') =>
    apiClient.get('/orders/labels/available', { params: { status } }),
};

export const imagesAPI = {
  // Bulk crop images to same dimensions (Dotb feature)
  bulkCrop: (data: {
    image_paths: string[];
    x: number;
    y: number;
    width: number;
    height: number;
  }) =>
    apiClient.post('/images/bulk/crop', data),

  // Bulk rotate images by same angle (Dotb feature)
  bulkRotate: (data: {
    image_paths: string[];
    angle: number;
  }) =>
    apiClient.post('/images/bulk/rotate', data),

  // Bulk adjust brightness/contrast/saturation (Dotb feature)
  bulkAdjust: (data: {
    image_paths: string[];
    brightness?: number;
    contrast?: number;
    saturation?: number;
  }) =>
    apiClient.post('/images/bulk/adjust', data),

  // Bulk add watermark to images (Dotb feature)
  bulkWatermark: (data: {
    image_paths: string[];
    text: string;
    position?: string;
    opacity?: number;
    font_size?: number;
  }) =>
    apiClient.post('/images/bulk/watermark', data),

  // Bulk remove background from images (Dotb feature)
  bulkRemoveBackground: (data: {
    image_paths: string[];
    mode?: string;
  }) =>
    apiClient.post('/images/bulk/remove-background', data),

  // Get predefined image editing presets
  getPresets: () =>
    apiClient.get('/images/presets'),
};
