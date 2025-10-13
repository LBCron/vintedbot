// Auto-generated TypeScript types from VintedBot API
// Generated from OpenAPI specification
// DO NOT EDIT - This file is auto-generated


export interface Body_import_csv_import_csv_post {
  file: string;
}

export interface Body_ingest_photos_ingest_photos_post {
  request?: PhotoIngestRequest | any;
  files?: Array<string> | any;
}

export type Condition = "new_with_tags" | "new_without_tags" | "very_good" | "good" | "satisfactory";

export interface Draft {
  title: string;
  description: string;
  brand?: string | any;
  category_guess?: string | any;
  condition?: Condition | any;
  size_guess?: string | any;
  keywords?: Array<string>;
  price_suggestion: PriceSuggestion;
  image_urls?: Array<string>;
  possible_duplicate?: boolean;
  estimated_sale_score?: number | any;
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface HealthResponse {
  status: string;
  uptime_seconds: number;
  version: string;
  scheduler_jobs: number;
}

export interface Item {
  id: string;
  title: string;
  description: string;
  brand?: string | any;
  category?: string | any;
  size?: string | any;
  condition?: Condition | any;
  price: number;
  price_suggestion?: PriceSuggestion | any;
  price_history?: PriceHistory[];
  keywords?: Array<string>;
  image_urls?: Array<string>;
  image_hash?: string | any;
  status?: ItemStatus;
  possible_duplicate?: boolean;
  estimated_sale_score?: number | any;
  created_at?: string;
  updated_at?: string;
}

export type ItemStatus = "draft" | "listed" | "sold" | "archived";

export interface PhotoIngestRequest {
  urls?: Array<string> | any;
}

export interface PriceHistory {
  date: string;
  old_price: number;
  new_price: number;
  reason?: string;
}

export interface PriceSimulation {
  initial_price: number;
  min_price: number;
  days?: number;
}

export interface PriceSuggestion {
  min: number;
  max: number;
  target: number;
  justification: string;
}

export interface SimulationResult {
  day: number;
  price: number;
  drop_percentage?: number;
}

export interface StatsResponse {
  total_items: number;
  total_value: number;
  avg_price: number;
  top_brands: Array<string>;
  duplicates_detected: number;
  avg_days_since_creation: number;
}

export interface ValidationError {
  loc: Array<string | number>;
  msg: string;
  type: string;
}
