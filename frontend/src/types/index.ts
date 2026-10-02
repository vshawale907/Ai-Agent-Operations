/* ============================================================================
   TypeScript types for the AI Business Operations Agent
   ============================================================================ */

// --- Auth ---
export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// --- Dashboard ---
export interface KPI {
  label: string;
  value: number;
  change_percent?: number;
  trend?: 'up' | 'down' | 'stable';
  prefix?: string;
  suffix?: string;
}

export interface DashboardData {
  kpis: KPI[];
  monthly_revenue: MonthlyRevenue[];
  revenue_by_region: RegionData[];
  top_products: ProductData[];
  revenue_by_category: CategoryData[];
  expense_trend: ExpenseTrend[];
  recent_orders: RecentOrder[];
}

export interface MonthlyRevenue {
  month: string;
  month_label: string;
  revenue: number;
  order_count: number;
}

export interface RegionData {
  region: string;
  revenue: number;
  order_count: number;
  avg_order_value: number;
}

export interface ProductData {
  name: string;
  category: string;
  revenue: number;
  units_sold: number;
  order_count: number;
}

export interface CategoryData {
  category: string;
  revenue: number;
  units_sold: number;
  order_count: number;
}

export interface ExpenseTrend {
  month: string;
  month_label: string;
  total_expense: number;
}

export interface RecentOrder {
  id: number;
  customer: string;
  amount: number;
  date: string;
  status: string;
  region: string;
}

// --- Chat & Citations ---
export interface CitationItem {
  source_type: 'database' | 'document' | 'analytics';
  title: string;
  page_number?: number;
  chunk_index?: number;
  excerpt?: string;
  reference: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chart_data?: ChartData | null;
  table_data?: Record<string, unknown>[] | null;
  citations?: CitationItem[] | null;
  metadata?: ChatMetadata | null;
  timestamp: string;
}

export interface ChartData {
  chart_type: 'line' | 'bar' | 'pie' | 'donut' | 'table';
  title: string;
  data: Record<string, unknown>[];
  x_key?: string;
  y_key?: string;
  keys?: string[];
}

export interface ChatMetadata {
  sql_query?: string;
  execution_time_ms?: number;
  data_sources?: string[];
  intent?: string;
  row_count?: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message: string;
  chart_data?: ChartData | null;
  table_data?: Record<string, unknown>[] | null;
  citations?: CitationItem[] | null;
  metadata?: ChatMetadata | null;
  error?: string;
  conversation_id?: string;
  timestamp: string;
}

// --- Documents (RAG) ---
export interface DocumentItem {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: 'processing' | 'ready' | 'failed';
  created_at: string;
}

export interface DocumentChunkItem {
  chunk_id: number;
  chunk_index: number;
  page_number?: number;
  token_count?: number;
  content_preview: string;
}

export interface DocumentDetailResponse extends DocumentItem {
  chunks: DocumentChunkItem[];
}

export interface DocumentSearchResult {
  chunk_id: number;
  document_id: number;
  filename: string;
  page_number?: number;
  content: string;
  score: number;
  citation: string;
}

// --- Executive Reports ---
export interface ExecutiveReportData {
  title: string;
  period: string;
  generated_at: string;
  executive_summary: string;
  revenue_performance: string;
  customer_performance: string;
  product_performance: string;
  expense_performance: string;
  anomalies_summary: string;
  key_insights: string[];
  identified_risks: string[];
  investigation_recommendations: string[];
  supporting_metrics: Record<string, unknown>;
}
