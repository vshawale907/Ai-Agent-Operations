/* ============================================================================
   API Service — Axios-based HTTP client with JWT auth
   ============================================================================ */

import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  DashboardData,
  DocumentDetailResponse,
  DocumentItem,
  DocumentSearchResult,
  ExecutiveReportData,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from '../types';

const API_BASE = '/api';

// --- Axios instance ---
const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

// --- Attach JWT to every request ---
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Handle 401 globally ---
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// =============================================================================
// Auth
// =============================================================================

export const authApi = {
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const res = await api.post<TokenResponse>('/auth/register', data);
    return res.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const res = await api.post<TokenResponse>('/auth/login', data);
    return res.data;
  },

  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
};

// =============================================================================
// Analytics
// =============================================================================

export const analyticsApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const res = await api.get<DashboardData>('/analytics/dashboard');
    return res.data;
  },

  getRevenue: async (months = 12) => {
    const res = await api.get(`/analytics/revenue?months=${months}`);
    return res.data;
  },

  getProducts: async () => {
    const res = await api.get('/analytics/products');
    return res.data;
  },

  getRegions: async () => {
    const res = await api.get('/analytics/regions');
    return res.data;
  },
};

// =============================================================================
// Chat
// =============================================================================

export const chatApi = {
  send: async (data: ChatRequest): Promise<ChatResponse> => {
    const res = await api.post<ChatResponse>('/chat', data);
    return res.data;
  },
};

// =============================================================================
// Documents (RAG)
// =============================================================================

export const documentsApi = {
  list: async (): Promise<{ documents: DocumentItem[] }> => {
    const res = await api.get<{ documents: DocumentItem[] }>('/documents');
    return res.data;
  },

  upload: async (file: File): Promise<{ message: string; document: DocumentItem }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  get: async (id: number): Promise<DocumentDetailResponse> => {
    const res = await api.get<DocumentDetailResponse>(`/documents/${id}`);
    return res.data;
  },

  delete: async (id: number): Promise<{ message: string }> => {
    const res = await api.delete(`/documents/${id}`);
    return res.data;
  },

  search: async (query: string, topK = 4): Promise<{ query: string; count: number; results: DocumentSearchResult[] }> => {
    const res = await api.post('/documents/search', { query, top_k: topK });
    return res.data;
  },

  seed: async (): Promise<{ message: string }> => {
    const res = await api.post('/documents/seed');
    return res.data;
  },
};

// =============================================================================
// Reports
// =============================================================================

export const reportsApi = {
  generate: async (period = 'Trailing 12 Months'): Promise<ExecutiveReportData> => {
    const res = await api.post<ExecutiveReportData>('/reports/generate', { period });
    return res.data;
  },

  exportCsv: async (period = 'Trailing 12 Months'): Promise<Blob> => {
    const res = await api.get(`/reports/export/csv?period=${encodeURIComponent(period)}`, {
      responseType: 'blob',
    });
    return res.data;
  },

  exportPdf: async (period = 'Trailing 12 Months'): Promise<Blob> => {
    const res = await api.get(`/reports/export/pdf?period=${encodeURIComponent(period)}`, {
      responseType: 'blob',
    });
    return res.data;
  },
};

// =============================================================================
// Health
// =============================================================================

export const healthApi = {
  check: async () => {
    const res = await api.get('/health');
    return res.data;
  },
};

export default api;
