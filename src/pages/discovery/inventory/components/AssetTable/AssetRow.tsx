import React from 'react';
import { Asset } from '@/types/discovery';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ColumnVisibility } from '../../types';

interface AssetRowProps {
  asset: Asset;
  isSelected: boolean;
  onSelect: (id: string) => void;
  columnVisibility: ColumnVisibility;
}

const getStatusBadgeVariant = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'active':
      return 'success';
    case 'inactive':
      return 'secondary';
    case 'pending':
      return 'warning';
    case 'error':
      return 'destructive';
    default:
      return 'outline';
  }
};

export const AssetRow: React.FC<AssetRowProps> = ({
  asset,
  isSelected,
  onSelect,
  columnVisibility
}) => {
  const renderCell = (key: string, content: React.ReactNode) => {
    if (!columnVisibility[key]) return null;
    
    return (
      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
        {content}
      </td>
    );
  };

  return (
    <tr className={isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'}>
      <td className="px-4 py-4 whitespace-nowrap">
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          checked={isSelected}
          onChange={() => onSelect(asset.id)}
        />
      </td>
      
      {renderCell('name', (
        <div className="flex items-center">
          <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-md bg-blue-100 text-blue-600">
            {asset.type === 'server' ? (
              <Server className="h-5 w-5" />
            ) : asset.type === 'database' ? (
              <Database className="h-5 w-5" />
            ) : (
              <HardDrive className="h-5 w-5" />
            )}
          </div>
          <div className="ml-4">
            <div className="font-medium text-gray-900">{asset.name}</div>
            <div className="text-gray-500 text-xs">{asset.ip_address || 'No IP'}</div>
          </div>
        </div>
      ))}
      
      {renderCell('type', (
        <Badge variant="outline" className="capitalize">
          {asset.type || 'Unknown'}
        </Badge>
      ))}
      
      {renderCell('environment', (
        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
          {asset.environment || 'N/A'}
        </span>
      ))}
      
      {renderCell('department', asset.department || '—')}
      
      {renderCell('criticality', (
        <Badge variant={getStatusBadgeVariant(asset.criticality || '')}>
          {asset.criticality || 'Not Set'}
        </Badge>
      ))}
      
      {renderCell('last_seen', (
        <span className="text-sm text-gray-500">
          {asset.last_seen ? new Date(asset.last_seen).toLocaleDateString() : 'Never'}
        </span>
      ))}
      
      <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex justify-end space-x-2">
          <Button variant="ghost" size="sm" className="h-8">
            <Eye className="h-4 w-4 mr-1" />
            View
          </Button>
          <Button variant="ghost" size="sm" className="h-8">
            <Edit2 className="h-4 w-4 mr-1" />
            Edit
          </Button>
        </div>
      </td>
    </tr>
  );
};
