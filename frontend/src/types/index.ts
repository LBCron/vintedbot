export interface User {
  id: number;
  email: string;
  name: string;
  plan: string;
  status: string;
  created_at: string;
  quotas_used: {
    drafts: number;
    publications_month: number;
    ai_analyses_month: number;
    photos_storage_mb: number;
  };
  quotas_limit: {
    drafts: number;
    publications_month: number;
    ai_analyses_month: number;
    photos_storage_mb: number;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface TokenResponse {
  access_token: string;
}

export interface Draft {
  id: string;
  title: string;
  description: string;
  price: number;
  category: string;
  condition: string;
  color: string;
  brand: string;
  size: string;
  photos: string[];
  status: string;
  confidence?: number;
  created_at: string;
  updated_at: string;
  user_id?: string;
  // Stock Management (Dotb feature)
  sku?: string;
  location?: string;
  stock_quantity?: number;
}

export interface DraftListResponse {
  drafts: Draft[];
  total: number;
  page: number;
  page_size: number;
}

export interface BulkUploadResponse {
  ok: boolean;
  job_id: string;
  total_photos: number;
  estimated_items: number;
  status: string;
  message: string;
}

export interface BulkJobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  total_photos: number;
  total_items: number;
  completed_items: number;
  failed_items: number;
  drafts: string[];
  errors: string[];
  started_at?: string;
  completed_at?: string;
}

export interface DashboardStats {
  total_listings: number;
  active_listings: number;
  total_views: number;
  views_today: number;
  views_week: number;
  total_likes: number;
  likes_today: number;
  total_messages: number;
  avg_conversion_rate: number;
  best_performing: ListingStats[];
  worst_performing: ListingStats[];
}

export interface ListingStats {
  listing_id: string;
  title: string;
  views: number;
  likes: number;
  messages: number;
  conversion_rate: number;
  price: number;
}

export interface PerformanceHeatmap {
  day_of_week: number;
  hour: number;
  views: number;
  likes: number;
  messages: number;
}

export interface CategoryPerformance {
  category: string;
  listings_count: number;
  total_views: number;
  total_likes: number;
  avg_price: number;
  sold_count: number;
}

export interface AnalyticsResponse {
  dashboard: DashboardStats;
  heatmap: PerformanceHeatmap[];
  by_category: CategoryPerformance[];
  top_listings: ListingStats[];
}

export interface AutomationRule {
  id: string;
  user_id: string;
  type: 'bump' | 'follow' | 'message' | 'favorite';
  config: any;
  enabled: boolean;
  created_at: string;
  last_run?: string;
  next_run?: string;
}

export interface BumpConfig {
  enabled: boolean;
  interval_hours: number;
  target_listings: string[];
  daily_limit: number;
  randomize_order: boolean;
}

export interface FollowConfig {
  enabled: boolean;
  target_categories: string[];
  target_brands: string[];
  daily_limit: number;
  min_listings: number;
  unfollow_after_days: number;
  blacklist_users: string[];
}

export interface MessageTemplate {
  id: string;
  name: string;
  trigger: 'like' | 'follow' | 'message';
  template: string;
  delay_minutes: number;
  enabled: boolean;
}

export interface MessageConfig {
  enabled: boolean;
  templates: MessageTemplate[];
  daily_limit: number;
  blacklist_users: string[];
}

export interface VintedAccount {
  id: string;
  name: string;
  email?: string;
  is_active: boolean;
  created_at: string;
  last_used?: string;
}
