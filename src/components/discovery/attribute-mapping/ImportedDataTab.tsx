import React from 'react'
import { useState } from 'react'
import { useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import {
  Database,
  FileText,
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { API_CONFIG } from '../../../config/api'
import { apiCall } from '../../../config/api'
import { useToast } from '../../../hooks/use-toast';
import { useAuth } from '../../../contexts/AuthContext';

interface SessionInfo {
  flowId: string | null;
  availableDataImports: Array<{ id: string; name?: string; [key: string]: unknown }>;
  selectedDataImportId: string | null;
  hasMultipleSessions: boolean;
  importCategory?: string;
  preferredColumns?: string[];
}

interface ImportedDataTabProps {
  className?: string;
  sessionInfo?: SessionInfo;
}

interface ImportRecord {
  id: string; // Internal ID for React keys only
  raw_data: Record<string, unknown>; // Original uploaded data only
  processed_data?: Record<string, unknown>;
  is_processed: boolean;
  is_valid: boolean;
  created_at?: string;
}

interface ImportMetadata {
  filename: string;
  import_type: string;
  imported_at: string;
  total_records: number;
}

const ImportedDataTab: React.FC<ImportedDataTabProps> = ({ className = "", sessionInfo }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [recordsPerPage] = useState(10);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { client, engagement, getAuthHeaders } = useAuth();

  // Get flow_id from sessionInfo
  const flow_id = sessionInfo?.flowId;
  const preferredColumns = sessionInfo?.preferredColumns;
  const importCategory = sessionInfo?.importCategory;

  // 🚀 React Query with context-aware caching - now uses flow-specific endpoint
  const {
    data: importResponse,
    isLoading,
    error: queryError,
    isStale,
    refetch
  } = useQuery({
    queryKey: ['imported-data', client?.id, engagement?.id, flow_id],
    queryFn: async () => {
      try {
        const headers = getAuthHeaders();
        if (client?.id) {
          headers['X-Client-Account-ID'] = client.id;
        }
        if (engagement?.id) {
          headers['X-Engagement-ID'] = engagement.id;
        }

        // Use flow-specific endpoint if flow_id is available
        if (flow_id) {
          return await apiCall(`/api/v1/data-import/flows/${flow_id}/import-data`, {
            method: 'GET',
            headers
          });
        } else {
          // Fallback to latest-import endpoint if no flow_id
          return await apiCall('/api/v1/data-import/latest-import', {
            method: 'GET',
            headers
          });
        }
      } catch (error: unknown) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const hasErrorStatus = (err: unknown): err is { status: number; response?: { status: number } } => {
          return typeof err === 'object' && err !== null && 'status' in err;
        };

        const hasResponseStatus = (err: unknown): err is { response: { status: number } } => {
          return typeof err === 'object' && err !== null && 'response' in err &&
                 typeof (err as { response: unknown }).response === 'object' && (err as { response: unknown }).response !== null &&
                 'status' in (err as { response: { status: unknown } }).response;
        };

        if ((hasErrorStatus(error) && error.status === 404) ||
            (hasResponseStatus(error) && error.response.status === 404)) {
          console.log('Import endpoint not available yet');
          return { success: false, data: [], import_metadata: null, message: 'No data imports found' };
        }
        throw error;
      }
    },
    enabled: !!client && !!engagement,
    staleTime: 30000,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    refetchOnReconnect: false,
    retry: (failureCount, error: unknown) => {
      // Don't retry on 404 errors
      const hasErrorStatus = (err: unknown): err is { status: number; response?: { status: number } } => {
        return typeof err === 'object' && err !== null && 'status' in err;
      };

      const hasResponseStatus = (err: unknown): err is { response: { status: number } } => {
        if (typeof err !== 'object' || err === null) return false;
        if (!('response' in err)) return false;
        const response = (err as Record<string, unknown>).response;
        return typeof response === 'object' && response !== null && 'status' in response;
      };

      if ((hasErrorStatus(error) && error.status === 404) ||
          (hasResponseStatus(error) && error.response.status === 404)) {
        return false;
      }
      return failureCount < 3;
    }
  });

  // 🔄 Refresh function that clears both React Query and SQLAlchemy caches
  const handleRefresh = async (): void => {
    setIsRefreshing(true);
    try {
      // 1. Clear React Query cache for imported data with context and flow_id
      queryClient.removeQueries({
        queryKey: ['imported-data', client?.id, engagement?.id, flow_id]
      });

      // 2. Call backend to clear SQLAlchemy cache with context headers
      try {
        const headers = getAuthHeaders();
        if (client?.id) {
          headers['X-Client-Account-ID'] = client.id;
        }
        if (engagement?.id) {
          headers['X-Engagement-ID'] = engagement.id;
        }

        await apiCall('/api/v1/data-import/clear-cache', {
          method: 'POST',
          headers
        });
      } catch (cacheError) {
        console.warn('Cache clear failed (non-critical):', cacheError);
      }

      // 3. Trigger fresh data fetch
      await refetch();

      toast({
        title: "Data Refreshed",
        description: "Imported data has been refreshed successfully.",
      });
    } catch (error) {
      console.error('Refresh failed:', error);
      toast({
        title: "Refresh Failed",
        description: "Failed to refresh imported data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  // Transform and memoize data to prevent unnecessary recalculations
  const { importData, importMetadata, error } = useMemo(() => {
    if (queryError) {
      return {
        importData: [],
        importMetadata: null,
        error: 'Failed to load imported data'
      };
    }

    if (!importResponse || !importResponse.success) {
      return {
        importData: [],
        importMetadata: null,
        error: importResponse?.message || 'Failed to load imported data'
      };
    }

    // Transform the raw data array into ImportRecord format - preserve original data only
    const transformedData = (importResponse.data || []).map((rawRecord: unknown, index: number) => ({
      id: `record_${index}`, // Internal ID for React keys only, not displayed
      raw_data: rawRecord, // Only the original uploaded data
      is_processed: true,
      is_valid: true,
      created_at: new Date().toISOString()
    }));

    return {
      importData: transformedData,
      importMetadata: importResponse.import_metadata || null,
      error: null
    };
  }, [importResponse, queryError]);

  const allColumns = useMemo(
    () => (importData.length > 0 ? Object.keys(importData[0].raw_data) : []),
    [importData]
  );

  // Set default columns when data loads (memoized)
  useEffect(() => {
    if (importData.length === 0) return;

    if (preferredColumns && preferredColumns.length > 0) {
      const availablePreferred = preferredColumns.filter(col => allColumns.includes(col));
      if (availablePreferred.length > 0) {
        setSelectedColumns(availablePreferred);
        return;
      }
    }

    if (selectedColumns.length === 0) {
      setSelectedColumns(allColumns.slice(0, 6));
    }
  }, [importData, preferredColumns, allColumns, selectedColumns.length]);

  const filteredData = importData.filter(record => {
    if (!searchTerm) return true;

    const searchLower = searchTerm.toLowerCase();
    return Object.values(record.raw_data).some(value =>
      String(value).toLowerCase().includes(searchLower)
    );
  });

  const paginatedData = filteredData.slice(
    (currentPage - 1) * recordsPerPage,
    currentPage * recordsPerPage
  );

  const totalPages = Math.ceil(filteredData.length / recordsPerPage);

  const toggleColumn = (column: string): unknown => {
    setSelectedColumns(prev =>
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const exportData = (): void => {
    if (filteredData.length === 0) return;

    const csvContent = [
      selectedColumns.join(','),
      ...filteredData.map(record =>
        selectedColumns.map(col =>
          JSON.stringify(record.raw_data[col] || '')
        ).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `imported_data_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!client || !engagement) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Database className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
          <span className="text-gray-600">Loading context...</span>
        </div>
      </div>
    );
  }

  // Show informative message if no flow_id is available and no data to show
  if (!flow_id && !isLoading && (!importResponse || importResponse.data?.length === 0)) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex flex-col items-center justify-center py-8">
          <div className="flex items-center text-gray-600 mb-4">
            <Database className="w-8 h-8 mr-3 text-gray-400" />
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Flow Context Required</h3>
              <p className="text-sm text-gray-500 mb-4">
                A discovery flow ID is required to display imported data.
              </p>
              <p className="text-xs text-gray-400">
                Please start a discovery flow first or navigate from a valid flow context.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Database className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
          <span className="text-gray-600">Loading imported data for {engagement?.name}...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex flex-col items-center justify-center py-8">
          <div className="flex items-center text-red-600 mb-4">
            <FileText className="w-6 h-6 mr-2" />
            <span>{error}</span>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Retry'}</span>
          </button>
        </div>
      </div>
    );
  }

  // Show better message when no data is available
  if (importData.length === 0) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex flex-col items-center justify-center py-8">
          <div className="flex items-center text-gray-600 mb-4">
            <Database className="w-8 h-8 mr-3 text-gray-400" />
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Imported Yet</h3>
              <p className="text-sm text-gray-500 mb-4">
                {importMetadata?.filename
                  ? `Import file "${importMetadata.filename}" was found but contains no records.`
                  : "No data has been imported for this engagement yet."
                }
              </p>
              <p className="text-xs text-gray-400">
                To see imported data here, please upload a CSV file through the Data Import section first.
              </p>
            </div>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Checking for Data...' : 'Check for Data'}</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-blue-500" />
            <h3 className="font-medium text-gray-900">Imported Data</h3>
            {importMetadata && (
              <span className="text-sm text-gray-500">
                {importMetadata.filename} • {importData.length} records
              </span>
            )}
            {isStale && (
              <span className="text-xs text-orange-500 bg-orange-50 px-2 py-1 rounded">
                Data may be outdated
              </span>
            )}
              {importCategory === 'app_discovery' && (
                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                  Application dependency import • spotlight on&nbsp;
                  {(preferredColumns && preferredColumns.length > 0)
                    ? preferredColumns.join(', ')
                    : 'application, hostname, dependency'}
                </span>
              )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Refresh data and clear cache"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
            </button>
            <button
              onClick={exportData}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search data..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Column Selector */}
          <div className="relative">
            <select
              multiple
              value={selectedColumns}
              onChange={(e) => setSelectedColumns(Array.from(e.target.selectedOptions, option => option.value))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              size={Math.min(allColumns.length, 8)}
            >
              {allColumns.map(column => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              {selectedColumns.map(column => (
                <th key={column} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((record) => (
              <tr key={record.id} className="hover:bg-gray-50">
                {selectedColumns.map(column => (
                  <td key={column} className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                    {String(record.raw_data[column] || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * recordsPerPage) + 1} to {Math.min(currentPage * recordsPerPage, filteredData.length)} of {filteredData.length} results
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-md border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-md border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Metadata Footer */}
      {importMetadata && (
        <div className="px-4 py-3 border-t bg-gray-50 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <span>File: {importMetadata.filename}</span>
            <span>Imported: {new Date(importMetadata.imported_at).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportedDataTab;
