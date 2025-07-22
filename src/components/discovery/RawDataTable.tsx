import React, { useState } from 'react';
import { Database } from 'lucide-react';

interface RawDataTableProps {
  data: unknown[];
  title?: string;
  getFieldHighlight?: (fieldName: string, assetId: string) => string;
  pageSize?: number;
  showLegend?: boolean;
}

const RawDataTable: React.FC<RawDataTableProps> = ({ 
  data, 
  title = "Imported Data View",
  getFieldHighlight = () => "",
  pageSize = 5,
  showLegend = true
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  // Get all unique column names from the data
  const getAllColumns = () => {
    if (data.length === 0) return [];
    
    const allColumns = new Set<string>();
    data.forEach(row => {
      Object.keys(row).forEach(key => allColumns.add(key));
    });
    
    // Sort columns to have important ones first
    const columnOrder = ['id', 'name', 'hostname', 'ipAddress', 'ip_address', 'type', 'asset_type', 'environment', 'department'];
    const sortedColumns = Array.from(allColumns).sort((a, b) => {
      const aIndex = columnOrder.indexOf(a);
      const bIndex = columnOrder.indexOf(b);
      
      if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
      if (aIndex !== -1) return -1;
      if (bIndex !== -1) return 1;
      return a.localeCompare(b);
    });
    
    return sortedColumns;
  };

  const formatColumnName = (columnName: string) => {
    return columnName
      .replace(/([A-Z])/g, ' $1') // Add space before capital letters
      .replace(/_/g, ' ') // Replace underscores with spaces
      .replace(/\b\w/g, l => l.toUpperCase()) // Capitalize first letter of each word
      .trim();
  };

  const getCellValue = (row: any, column: string) => {
    const value = row[column];
    if (value === null || value === undefined || value === '') {
      return '<empty>';
    }
    return String(value);
  };

  const getCurrentPageData = () => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return data.slice(startIndex, endIndex);
  };

  // Get asset identifier for highlighting
  const getAssetIdentifier = (row: unknown) => {
    return row.id || row.ID || row.asset_name || row.hostname || row.name || row.NAME || 'unknown';
  };

  // Get unique row key that combines asset identifier with row index to prevent duplicates
  const getRowKey = (row: any, index: number) => {
    const assetId = getAssetIdentifier(row);
    // Ensure uniqueness even if multiple rows have 'unknown' identifier
    return assetId === 'unknown' ? `unknown-${index}` : assetId;
  };

  const totalPages = Math.ceil(data.length / pageSize);

  if (data.length === 0) {
    return (
      <div className="mb-8">
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 text-center text-gray-500">
            <Database className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No data available to display</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Database className="h-6 w-6 text-gray-500" />
              <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
              <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                {data.length} total records
              </span>
            </div>
            {showLegend && (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-3 h-3 bg-orange-100 border border-orange-300 rounded"></div>
                  <span>Format Issue</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-3 h-3 bg-red-100 border border-red-300 rounded"></div>
                  <span>Missing Data</span>
                </div>
              </div>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Complete view of imported data. Scroll horizontally to see all columns.
          </p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {getAllColumns().map((column) => (
                  <th key={column} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                    {formatColumnName(column)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {getCurrentPageData().map((row, index) => {
                const assetId = getAssetIdentifier(row);
                return (
                  <tr key={getRowKey(row, index)} className="hover:bg-gray-50">
                    {getAllColumns().map((column) => {
                      // Get highlighting for this specific cell
                      const highlightClass = getFieldHighlight ? getFieldHighlight(column, assetId) : '';
                      const cellValue = getCellValue(row, column);
                      
                      return (
                        <td 
                          key={column} 
                          className={`px-4 py-4 whitespace-nowrap text-sm text-gray-900 ${highlightClass} ${
                            cellValue === '<empty>' ? 'text-gray-400 italic' : ''
                          }`}
                        >
                          {cellValue}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{' '}
                <span className="font-medium">{((currentPage - 1) * pageSize) + 1}</span>
                {' '}to{' '}
                <span className="font-medium">
                  {Math.min(currentPage * pageSize, data.length)}
                </span>
                {' '}of{' '}
                <span className="font-medium">{data.length}</span>
                {' '}results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let page;
                  if (totalPages <= 5) {
                    page = i + 1;
                  } else if (currentPage <= 3) {
                    page = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    page = totalPages - 4 + i;
                  } else {
                    page = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        page === currentPage
                          ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                          : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RawDataTable; 