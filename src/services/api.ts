import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { getAuthToken } from '../contexts/AuthContext';

// Create axios instance with base URL
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error: AxiosError) => {
    if (error.response) {
      // Handle HTTP errors
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request
      console.error('Request error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Generic API call function
 * @param endpoint - API endpoint
 * @param config - Axios request config
 * @param useAuth - Whether to include auth token (default: true)
 */
export const apiCall = async <T>(
  endpoint: string,
  config: AxiosRequestConfig = {},
  useAuth: boolean = true
): Promise<T> => {
  try {
    const response = await api({
      url: endpoint,
      ...config,
      headers: {
        ...(useAuth && { Authorization: `Bearer ${getAuthToken()}` }),
        ...config.headers,
      },
    });
    return response as T;
  } catch (error) {
    console.error(`API call to ${endpoint} failed:`, error);
    throw error;
  }
};

export default api;
