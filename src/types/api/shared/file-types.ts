/**
 * File API Types
 * 
 * Types for file upload, download, and file management operations.
 */

import type { BaseApiRequest, BaseApiResponse } from './base-types';
import type { MultiTenantContext } from './tenant-types';
import type { CompressionOptions, EncryptionOptions } from './file-processing-types';

// File upload/download
export interface FileUploadRequest extends BaseApiRequest {
  file: File | Blob;
  fileName?: string;
  contentType?: string;
  context: MultiTenantContext;
  metadata?: Record<string, string | number | boolean | null>;
  tags?: string[];
  encryption?: EncryptionOptions;
  virusScan?: boolean;
  overwrite?: boolean;
}

export interface FileUploadResponse extends BaseApiResponse<FileInfo> {
  data: FileInfo;
  uploaded: boolean;
  location: string;
  virusScanResult?: VirusScanResult;
}

export interface FileDownloadRequest extends BaseApiRequest {
  fileId: string;
  context: MultiTenantContext;
  version?: string;
  format?: string;
  transformation?: TransformationOptions;
  includeMetadata?: boolean;
}

export interface FileDownloadResponse {
  file: Blob;
  fileName: string;
  contentType: string;
  size: number;
  lastModified: string;
  etag: string;
  metadata?: FileMetadata;
}

// File information and metadata
export interface FileInfo {
  id: string;
  name: string;
  originalName: string;
  size: number;
  mimeType: string;
  extension: string;
  hash: string;
  url: string;
  downloadUrl: string;
  thumbnail?: string;
  metadata: FileMetadata;
  uploadedAt: string;
  uploadedBy: string;
  virusScanResult?: VirusScanResult;
}

export interface FileMetadata {
  width?: number;
  height?: number;
  duration?: number;
  pages?: number;
  encoding?: string;
  colorSpace?: string;
  compression?: string;
  custom?: Record<string, string | number | boolean | null>;
}

export interface VirusScanResult {
  scanned: boolean;
  clean: boolean;
  threats?: ThreatInfo[];
  scanEngine: string;
  scanTime: string;
  signature: string;
}

export interface ThreatInfo {
  name: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description?: string;
}


export interface TransformationOptions {
  resize?: {
    width?: number;
    height?: number;
    fit?: 'cover' | 'contain' | 'fill' | 'inside' | 'outside';
    position?: string;
  };
  crop?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  rotate?: number;
  format?: string;
  quality?: number;
  compress?: boolean;
}

