import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Database, FileText, Download, Search } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall, API_CONFIG } from '../../../config/api';

interface ImportedDataTabProps {
  className?: string;
}

interface ImportRecord {
  id: string;
  row_number: number;
  record_id: string;
  raw_data: Record<string, any>;
  processed_data?: Record<string, any>;
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

const ImportedDataTab: React.FC<ImportedDataTabProps> = ({ className = "" }) => {
  const { getAuthHeaders } = useAuth();
  const [importData, setImportData] = useState<ImportRecord[]>([]);
  const [importMetadata, setImportMetadata] = useState<ImportMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  
  const recordsPerPage = 50;
  const totalPages = Math.ceil(importData.length / recordsPerPage);

  useEffect(() => {
    fetchImportedData();
  }, []);

  const fetchImportedData = async () => {
    try {
      setIsLoading(true);
      
      const authHeaders = getAuthHeaders();
      
      // Get the latest import data
      const response = await apiCall(API_CONFIG.ENDPOINTS.DATA_IMPORT.LATEST_IMPORT, {
        method: 'GET',
        headers: authHeaders
      });

      if (response.success) {
        setImportData(response.data || []);
        setImportMetadata(response.import_metadata || null);
        
        // Set default visible columns (first 6 columns)
        if (response.data && response.data.length > 0) {
          const columns = Object.keys(response.data[0]);
          setSelectedColumns(columns.slice(0, 6));
        }
      } else {
        setError(response.message || 'Failed to load imported data');
      }
    } catch (err) {
      console.error('Error fetching imported data:', err);
      setError('Failed to load imported data');
    } finally {
      setIsLoading(false);
    }
  };

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

  const allColumns = importData.length > 0 ? Object.keys(importData[0].raw_data) : [];

  const toggleColumn = (column: string) => {
    setSelectedColumns(prev => 
      prev.includes(column) 
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const exportData = () => {
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

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Database className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
          <span className="text-gray-600">Loading imported data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8 text-red-600">
          <FileText className="w-6 h-6 mr-2" />
          <span>{error}</span>
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
          </div>
          <button
            onClick={exportData}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Row #
              </th>
              {selectedColumns.map(column => (
                <th key={column} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((record, index) => (
              <tr key={record.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">
                  {(currentPage - 1) * recordsPerPage + index + 1}
                </td>
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