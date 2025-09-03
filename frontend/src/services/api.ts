/**
 * API Client Service
 * Axios-based API client with interceptors for request/response handling
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { PaginatedResponse } from '../types';

// API base URL - uses environment variable or defaults to local backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Create axios instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor
 * Adds auth tokens and logs requests in development
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available (future enhancement)
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log requests in development
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.params);
    }

    return config;
  },
  (error: AxiosError) => {
    console.error('[API] Request Error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 * Handles errors and transforms responses
 */
apiClient.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`[API] Response from ${response.config.url}:`, response.data);
    }
    return response;
  },
  async (error: AxiosError<any>) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && originalRequest) {
      localStorage.removeItem('authToken');
      // Future: redirect to login
    }

    // Enhanced error logging
    if (import.meta.env.DEV) {
      console.error('[API] Response Error:', {
        url: originalRequest?.url,
        status: error.response?.status,
        message: error.response?.data?.message || error.message,
        details: error.response?.data?.details,
      });
    }

    // Transform error for consistent handling
    const errorMessage = error.response?.data?.message ||
                        error.message ||
                        'An unexpected error occurred';

    return Promise.reject({
      status: error.response?.status,
      message: errorMessage,
      details: error.response?.data?.details,
      original: error,
    });
  }
);

/**
 * Generic API response handler
 * Extracts data from response wrapper
 */
export const handleApiResponse = <T>(response: any): T => {
  // If backend wraps in {success, data}, extract data
  if (response.data && typeof response.data.success !== 'undefined') {
    if (response.data.success === false) {
      throw new Error(response.data.message || 'API request failed');
    }
    return response.data.data || response.data;
  }
  // Otherwise return data directly
  return response.data;
};

/**
 * API Service Class
 * Provides typed methods for API calls
 */
class ApiService {
  /**
   * Generic GET request
   * 
   * @template T Response data type
   * @param url Endpoint URL
   * @param params Query parameters
   * @returns Promise with typed response
   */
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await apiClient.get<T>(url, { params });
    return handleApiResponse<T>(response);
  }

  /**
   * Generic POST request
   * 
   * @template T Response data type
   * @param url Endpoint URL
   * @param data Request body
   * @returns Promise with typed response
   */
  async post<T>(url: string, data?: any): Promise<T> {
    const response = await apiClient.post<T>(url, data);
    return handleApiResponse<T>(response);
  }

  /**
   * Generic PUT request
   * 
   * @template T Response data type
   * @param url Endpoint URL
   * @param data Request body
   * @returns Promise with typed response
   */
  async put<T>(url: string, data?: any): Promise<T> {
    const response = await apiClient.put<T>(url, data);
    return handleApiResponse<T>(response);
  }

  /**
   * Generic DELETE request
   * 
   * @template T Response data type
   * @param url Endpoint URL
   * @returns Promise with typed response
   */
  async delete<T>(url: string): Promise<T> {
    const response = await apiClient.delete<T>(url);
    return handleApiResponse<T>(response);
  }

  /**
   * Paginated GET request
   * 
   * @template T Item type
   * @param url Endpoint URL
   * @param params Query parameters including pagination
   * @returns Promise with paginated response
   */
  async getPaginated<T>(url: string, params?: any): Promise<PaginatedResponse<T>> {
    const response = await apiClient.get<PaginatedResponse<T>>(url, { params });
    return handleApiResponse<PaginatedResponse<T>>(response);
  }
}

/**
 * Export singleton instance
 */
export const api = new ApiService();

/**
 * Export the axios instance for direct use if needed
 */
export { apiClient };

/**
 * Utility function for building query strings
 * Handles arrays and undefined/null values properly
 * 
 * @param params Query parameters object
 * @returns Query string (with leading ?)
 */
export const buildQueryString = (params: Record<string, any>): string => {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => queryParams.append(key, String(v)));
      } else {
        queryParams.append(key, String(value));
      }
    }
  });

  const queryString = queryParams.toString();
  return queryString ? `?${queryString}` : '';
};

/**
 * Error handling utilities
 */
export const isApiError = (error: any): error is { status: number; message: string } => {
  return error && typeof error.status === 'number' && typeof error.message === 'string';
};

export const getErrorMessage = (error: any): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};
