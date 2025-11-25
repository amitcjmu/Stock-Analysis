import { apiCall } from '@/lib/api/apiClient';

export type ImportCategory =
  | 'cmdb_export'
  | 'app_discovery'
  | 'infrastructure'
  | 'sensitive_data';

export interface UploadDataImportOptions {
  processingConfig?: Record<string, any>;
}

export interface UploadDataImportResponse {
  data_import_id: string;
  master_flow_id: string;
  records_stored: number;
  status: string;
  message?: string;
  import_category: ImportCategory;
  processing_config?: Record<string, any>;
}

/**
 * Upload a data import file to the multi-category import endpoint.
 */
export const uploadDataImport = async (
  file: File,
  importCategory: ImportCategory,
  options: UploadDataImportOptions = {},
): Promise<UploadDataImportResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('import_category', importCategory);

  if (options.processingConfig && Object.keys(options.processingConfig).length > 0) {
    formData.append('processing_config', JSON.stringify(options.processingConfig));
  }

  const response = await apiCall('/api/v1/data-import/upload', {
    method: 'POST',
    body: formData,
  });

  return response as UploadDataImportResponse;
};
