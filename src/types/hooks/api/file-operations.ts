/**
 * File Operations Hook Types
 * 
 * Hook types for file upload and download operations,
 * including chunked uploads and progress tracking.
 */

import type { RequestConfig } from './shared';

// Upload response interface
export interface UploadResponse {
  success: boolean;
  data?: {
    url?: string;
    key?: string;
    filename?: string;
    size?: number;
    type?: string;
  };
  error?: string;
  message?: string;
}

// File Upload Hook Types
export interface UseFileUploadParams {
  endpoint: string;
  method?: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  maxFileSize?: number;
  allowedTypes?: string[];
  multiple?: boolean;
  autoUpload?: boolean;
  chunkSize?: number;
  resumable?: boolean;
  validateFile?: (file: File) => ValidationResult;
  transformFile?: (file: File) => File | Promise<File>;
  onProgress?: (progress: UploadProgress) => void;
  onSuccess?: (response: UploadResponse, file: File) => void;
  onError?: (error: Error, file: File) => void;
  onComplete?: (results: UploadResult[]) => void;
}

export interface UseFileUploadReturn {
  files: UploadFile[];
  uploading: boolean;
  progress: number;
  completed: number;
  total: number;
  errors: UploadError[];
  addFiles: (files: File[] | FileList) => void;
  removeFile: (id: string) => void;
  clearFiles: () => void;
  upload: (files?: File[]) => Promise<UploadResult[]>;
  uploadFile: (file: File) => Promise<UploadResult>;
  pauseUpload: (id: string) => void;
  resumeUpload: (id: string) => void;
  cancelUpload: (id: string) => void;
  retryUpload: (id: string) => Promise<UploadResult>;
}

// Supporting Types
export interface UploadConfig extends RequestConfig {
  onProgress?: (progress: UploadProgress) => void;
  chunkSize?: number;
  resumable?: boolean;
}

export interface DownloadConfig extends RequestConfig {
  onProgress?: (progress: DownloadProgress) => void;
  filename?: string;
}

export interface UploadFile {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  error?: Error;
  result?: unknown;
  url?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  rate: number;
  estimated: number;
}

export interface UploadResult {
  id: string;
  success: boolean;
  data?: unknown;
  error?: Error;
  url?: string;
}

export interface UploadError {
  id: string;
  file: File;
  error: Error;
}

export interface DownloadProgress {
  loaded: number;
  total: number;
  percentage: number;
  rate: number;
  estimated: number;
}

export type UploadStatus = 'pending' | 'uploading' | 'paused' | 'completed' | 'failed' | 'cancelled';
export interface ValidationResult { valid: boolean; errors?: string[] }