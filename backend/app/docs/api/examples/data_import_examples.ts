/**
 * Data Import API Examples - TypeScript/JavaScript Client Implementation
 * 
 * This file provides complete working examples for all data import API endpoints.
 */

interface FileMetadata {
  filename: string;
  size: number;
  type: string;
}

interface UploadContext {
  intended_type: string;
  validation_flow_id?: string;
  upload_timestamp: string;
}

interface DataImportRequest {
  file_data: Record<string, unknown>[];
  metadata: FileMetadata;
  upload_context: UploadContext;
  client_id?: string;
  engagement_id?: string;
}

interface DataImportResponse {
  success: boolean;
  message: string;
  data_import_id: string;
  flow_id: string;
  total_records: number;
  import_type: string;
  next_steps: string[];
}

interface ImportStatus {
  import_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  current_phase?: string;
  updated_at: string;
}

class DataImportClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(
    baseUrl: string,
    token: string,
    clientId: string,
    engagementId: string
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'X-Client-Account-ID': clientId,
      'X-Engagement-ID': engagementId,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Import CSV data directly
   */
  async importData(
    data: Record<string, unknown>[],
    filename: string,
    importType: string
  ): Promise<DataImportResponse> {
    const request: DataImportRequest = {
      file_data: data,
      metadata: {
        filename,
        size: JSON.stringify(data).length,
        type: 'text/csv'
      },
      upload_context: {
        intended_type: importType,
        upload_timestamp: new Date().toISOString()
      }
    };

    const response = await fetch(`${this.baseUrl}/api/v1/data-import/store-import`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Import failed: ${error.message || response.statusText}`);
    }

    return response.json();
  }

  /**
   * Import CSV file from browser file input
   */
  async importFile(file: File, importType: string): Promise<DataImportResponse> {
    // Parse CSV file
    const text = await file.text();
    const data = this.parseCSV(text);

    const request: DataImportRequest = {
      file_data: data,
      metadata: {
        filename: file.name,
        size: file.size,
        type: file.type || 'text/csv'
      },
      upload_context: {
        intended_type: importType,
        upload_timestamp: new Date().toISOString()
      }
    };

    const response = await fetch(`${this.baseUrl}/api/v1/data-import/store-import`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Import failed: ${error.message || response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get import status
   */
  async getImportStatus(importId: string): Promise<ImportStatus> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/data-import/import/${importId}/status`,
      { headers: this.headers }
    );

    if (!response.ok) {
      throw new Error(`Failed to get status: ${response.statusText}`);
    }

    const result = await response.json();
    return result.import_status;
  }

  /**
   * Get latest import for current context
   */
  async getLatestImport(): Promise<DataImportResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/data-import/latest-import`,
      { headers: this.headers }
    );

    if (!response.ok) {
      throw new Error(`Failed to get latest import: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Wait for import completion with polling
   */
  async waitForCompletion(
    importId: string,
    options: { timeout?: number; pollInterval?: number } = {}
  ): Promise<ImportStatus> {
    const { timeout = 300000, pollInterval = 5000 } = options;
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const status = await this.getImportStatus(importId);
      
      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Import ${importId} did not complete within ${timeout}ms`);
  }

  /**
   * Cancel an import
   */
  async cancelImport(importId: string): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/data-import/import/${importId}`,
      {
        method: 'DELETE',
        headers: this.headers
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to cancel import: ${response.statusText}`);
    }
  }

  /**
   * Retry a failed import
   */
  async retryImport(importId: string): Promise<DataImportResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/data-import/import/${importId}/retry`,
      {
        method: 'POST',
        headers: this.headers
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to retry import: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Parse CSV text to array of objects
   */
  private parseCSV(text: string): Record<string, unknown>[] {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length === 0) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const data: Record<string, unknown>[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const row: Record<string, unknown> = {};
      
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      
      data.push(row);
    }

    return data;
  }
}

// Example Usage
async function demonstrateDataImportAPI() {
  // Initialize client
  const client = new DataImportClient(
    'https://api.yourdomain.com',
    'your-bearer-token',
    '1',
    '1'
  );

  console.log('=== Data Import API Examples ===\n');

  // Example 1: Direct data import
  console.log('Example 1: Direct Server Data Import');
  console.log('-'.repeat(50));

  const serverData = [
    {
      server_name: 'prod-web-01',
      ip_address: '10.0.1.10',
      os: 'Ubuntu 20.04',
      cpu_cores: 8,
      memory_gb: 16,
      storage_gb: 500,
      environment: 'production',
      business_unit: 'Sales',
      application: 'Web Portal'
    },
    {
      server_name: 'prod-db-01',
      ip_address: '10.0.1.20',
      os: 'RHEL 8',
      cpu_cores: 16,
      memory_gb: 64,
      storage_gb: 2000,
      environment: 'production',
      business_unit: 'Sales',
      application: 'Customer Database'
    }
  ];

  try {
    const result = await client.importData(
      serverData,
      'servers_inventory.csv',
      'servers'
    );
    
    console.log('Import successful!');
    console.log(`Import ID: ${result.data_import_id}`);
    console.log(`Flow ID: ${result.flow_id}`);
    console.log(`Total Records: ${result.total_records}`);
    console.log('Next Steps:', result.next_steps);

    // Wait for completion
    console.log('\nWaiting for import to complete...');
    const finalStatus = await client.waitForCompletion(result.data_import_id);
    console.log(`Import completed with status: ${finalStatus.status}`);

  } catch (error: unknown) {
    console.error('Import failed:', error.message);
  }

  console.log();

  // Example 2: File upload from browser
  console.log('Example 2: Browser File Upload');
  console.log('-'.repeat(50));

  // Simulate file input
  const csvContent = `app_name,version,server_name,technology_stack,criticality
CustomerPortal,2.3.4,prod-web-01,Java Spring Boot,High
InventoryAPI,1.8.2,prod-app-01,Python FastAPI,Medium
AnalyticsEngine,3.0.1,prod-analytics-01,Apache Spark,High`;

  const file = new File([csvContent], 'applications.csv', { type: 'text/csv' });

  try {
    const result = await client.importFile(file, 'applications');
    console.log('Applications import successful!');
    console.log(`Import ID: ${result.data_import_id}`);
  } catch (error: unknown) {
    console.error('File import failed:', error.message);
  }

  console.log();

  // Example 3: React component example
  console.log('Example 3: React Component Integration');
  console.log('-'.repeat(50));
  console.log(`
import React, { useState } from 'react';
import { DataImportClient } from './DataImportClient';

function DataImportComponent() {
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const client = new DataImportClient(
    process.env.REACT_APP_API_URL!,
    localStorage.getItem('authToken')!,
    localStorage.getItem('clientId')!,
    localStorage.getItem('engagementId')!
  );

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImporting(true);
    setError(null);

    try {
      // Import the file
      const result = await client.importFile(file, 'servers');
      
      // Monitor progress
      const pollProgress = setInterval(async () => {
        try {
          const status = await client.getImportStatus(result.data_import_id);
          setProgress(status.progress || 0);
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollProgress);
            setImporting(false);
            
            if (status.status === 'failed') {
              setError('Import failed');
            }
          }
        } catch (err) {
          clearInterval(pollProgress);
          setImporting(false);
          setError('Failed to check status');
        }
      }, 2000);

    } catch (err: any) {
      setImporting(false);
      setError(err.message);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".csv"
        onChange={handleFileUpload}
        disabled={importing}
      />
      
      {importing && (
        <div>
          <progress value={progress} max={100} />
          <span>{progress}%</span>
        </div>
      )}
      
      {error && <div className="error">{error}</div>}
    </div>
  );
}
`);

  console.log();

  // Example 4: Error handling
  console.log('Example 4: Comprehensive Error Handling');
  console.log('-'.repeat(50));

  try {
    // Attempt import with invalid data
    await client.importData(
      [{ invalid: 'data' }],
      'invalid.csv',
      'servers'
    );
  } catch (error: unknown) {
    if (error.message.includes('incomplete_discovery_flow_exists')) {
      console.log('Handling existing flow conflict:');
      console.log('1. Show user the existing flow');
      console.log('2. Offer to cancel or complete it');
      console.log('3. Retry after resolution');
    } else if (error.message.includes('validation_error')) {
      console.log('Handling validation error:');
      console.log('1. Parse error details');
      console.log('2. Highlight problematic fields');
      console.log('3. Guide user to fix issues');
    } else {
      console.log('Generic error handling:', error.message);
    }
  }

  console.log();

  // Example 5: Batch operations with progress
  console.log('Example 5: Batch Import with Real-time Progress');
  console.log('-'.repeat(50));

  // Generate large dataset
  const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
    server_name: `server-${String(i).padStart(3, '0')}`,
    ip_address: `10.0.${Math.floor(i / 256)}.${i % 256}`,
    os: i % 2 === 0 ? 'Ubuntu 20.04' : 'RHEL 8',
    cpu_cores: 4 + (i % 4) * 4,
    memory_gb: 8 + (i % 8) * 8,
    storage_gb: 100 + (i % 10) * 100
  }));

  try {
    console.log(`Importing ${largeDataset.length} servers...`);
    const result = await client.importData(
      largeDataset,
      'large_inventory.csv',
      'servers'
    );

    // Create progress bar
    const progressBar = (percent: number) => {
      const filled = Math.floor(percent / 2);
      const empty = 50 - filled;
      return `[${'='.repeat(filled)}${' '.repeat(empty)}] ${percent}%`;
    };

    // Monitor with visual progress
    let lastProgress = 0;
    while (true) {
      const status = await client.getImportStatus(result.data_import_id);
      const progress = status.progress || 0;
      
      if (progress !== lastProgress) {
        process.stdout.write(`\r${progressBar(progress)} - ${status.current_phase || 'Processing'}`);
        lastProgress = progress;
      }

      if (status.status === 'completed' || status.status === 'failed') {
        console.log('\nImport completed!');
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }

  } catch (error: unknown) {
    console.error('Batch import failed:', error.message);
  }
}

// Run examples
if (typeof window === 'undefined') {
  // Node.js environment
  demonstrateDataImportAPI().catch(console.error);
}

// Export for use in other modules
export { DataImportClient, demonstrateDataImportAPI };