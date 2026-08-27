import axios, { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import type { Analysis } from '../types/analysis';
import type { PedagogicalDesign } from '../types/pedagogical';
import type { Script } from '../types/script';
import type { QAResult } from '../types/qa';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 800;

const shouldRetry = (error: unknown, attempt: number): boolean => {
  if (attempt >= MAX_RETRIES) return false;
  const axiosErr = error as AxiosError | undefined;
  if (!axiosErr || !axiosErr.isAxiosError) return false;
  const status = axiosErr.response?.status;
  const code = axiosErr.code;
  if (!status) return true;
  if (code === 'ECONNABORTED' && status === undefined) return true;
  if (status >= 500) return true;
  if (status === 408 || status === 425 || status === 429) return true;
  return false;
};

export const api: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300_000,
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const method = String(config.method || 'GET').toUpperCase();
    const url = config.url || '';
    console.debug(`[API] → ${method} ${url} (timeout=${config.timeout ?? 300000}ms)`);
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response: AxiosResponse) => {
    const config = response.config as InternalAxiosRequestConfig;
    const method = String(config.method || 'GET').toUpperCase();
    const url = config.url || '';
    console.debug(
      `[API] ← ${method} ${url} ${response.status} ${
        typeof response.data?.success === 'boolean'
          ? `success=${String(response.data.success)}`
          : ''
      }`,
    );
    return response;
  },
  async (error: unknown) => {
    const axiosErr = error as AxiosError | undefined;
    const config = (axiosErr?.config || {}) as InternalAxiosRequestConfig & {
      __retryCount?: number;
    };
    config.__retryCount = (config.__retryCount ?? 0) + 1;
    if (shouldRetry(error, config.__retryCount)) {
      const delay = RETRY_DELAY_MS * 2 ** (config.__retryCount - 1);
      console.warn(
        `[API] Retrying ${config.method?.toUpperCase() || ''} ${config.url || ''} attempt #${config.__retryCount}/${MAX_RETRIES + 1} in ${delay}ms after error ${
          axiosErr?.response?.status || axiosErr?.code || 'NETWORK'
        }`,
      );
      await new Promise((r) => setTimeout(r, delay));
      return api.request(config as InternalAxiosRequestConfig);
    }
    const url = config.url || '';
    const status = axiosErr?.response?.status ?? 0;
    const code = axiosErr?.code || 'NETWORK_ERROR';
    const detail =
      (axiosErr?.response?.data as any)?.detail ||
      axiosErr?.message ||
      'Error de red al contactar el servidor. Revisa tu conexión o inténtalo de nuevo.';
    console.error(`[API] FAIL ${status || code} ${url} : ${detail}`);
    return Promise.reject(axiosErr ? axiosErr : error);
  },
);

export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  error: { code: string; message: string; details?: unknown } | null;
  meta: { request_id?: string; timestamp: string; [k: string]: unknown };
}

export async function request<T = unknown>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  config?: object,
): Promise<T> {
  const response = await api.request<ApiResponse<T>>({ method, url, ...config });
  if (!response.data.success) {
    const error = response.data.error;
    throw new Error(error?.message || 'API error');
  }
  return response.data.data;
}

export function get<T>(url: string, params?: object) {
  return request<T>('get', url, { params });
}

export function post<T>(url: string, data?: object, config?: object) {
  return request<T>('post', url, { data, ...config });
}

export function put<T>(url: string, data?: object, config?: object) {
  return request<T>('put', url, { data, ...config });
}

export function del<T>(url: string, config?: object) {
  return request<T>('delete', url, config);
}

interface WrappedAnalysis {
  analysis: Analysis;
  course_id: string;
}

export async function getAnalysis(courseId: string): Promise<Analysis> {
  const data = await get<WrappedAnalysis>(`/courses/${courseId}/analysis`);
  return data.analysis;
}

interface WrappedPedagogical {
  pedagogical_design: PedagogicalDesign;
  course_id: string;
}

export async function getPedagogical(courseId: string): Promise<PedagogicalDesign> {
  const data = await get<WrappedPedagogical>(`/courses/${courseId}/pedagogical-design`);
  return data.pedagogical_design;
}

interface WrappedScript {
  script: Script;
  course_id: string;
}

export async function getScript(courseId: string): Promise<Script> {
  const data = await get<WrappedScript>(`/courses/${courseId}/script`);
  return data.script;
}

interface WrappedQA {
  qa: QAResult;
  course_id: string;
}

export async function getQA(courseId: string): Promise<QAResult> {
  const data = await get<WrappedQA>(`/courses/${courseId}/qa`);
  return data.qa;
}

export interface CourseStatusResponse {
  course_id: string;
  status: string;
  progress: number;
  current_step?: string;
  video?: { url: string; thumbnail_url?: string; duration: number };
  qa?: { status: string; score: number };
  steps?: Record<string, unknown>;
}

export async function getCourseStatus(courseId: string): Promise<CourseStatusResponse> {
  return get<CourseStatusResponse>(`/courses/${courseId}/status`);
}
