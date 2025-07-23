/**
 * Asset Card Component
 * 
 * Expandable card displaying asset details with technical and business information.
 */

import React from 'react'
import { useState } from 'react'
import { Info } from 'lucide-react'
import { ChevronDown, ChevronUp, Server, Database, Globe, Monitor, Cpu, Building } from 'lucide-react'
import { AssetDetails } from './types';
import { getCriticalityColor } from './utils';

interface AssetCardProps {
  componentName: string;
  asset: AssetDetails;
  isExpanded: boolean;
  onToggleExpanded: (componentName: string) => void;
}

const AssetCard: React.FC<AssetCardProps> = ({ 
  componentName, 
  asset, 
  isExpanded, 
  onToggleExpanded 
}) => {
  const getAssetIcon = () => {
    switch (asset.asset_type?.toLowerCase()) {
      case 'server': return <Server className="w-4 h-4 text-blue-600" />;
      case 'database': return <Database className="w-4 h-4 text-green-600" />;
      case 'application': return <Globe className="w-4 h-4 text-purple-600" />;
      default: return <Monitor className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className="border rounded-lg bg-gray-50 overflow-hidden">
      <div 
        className="p-3 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => onToggleExpanded(componentName)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              {getAssetIcon()}
              <span className="font-medium text-gray-900">{asset.name}</span>
            </div>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              {asset.asset_type}
            </span>
            {asset.environment && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                {asset.environment}
              </span>
            )}
          </div>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </div>
        
        {/* Brief summary when collapsed */}
        {!isExpanded && (
          <div className="mt-2 text-sm text-gray-600 space-y-1">
            {asset.hostname && (
              <div>🖥️ <span className="font-medium">Hostname:</span> {asset.hostname}</div>
            )}
            {asset.ip_address && (
              <div>🌐 <span className="font-medium">IP:</span> {asset.ip_address}</div>
            )}
            {asset.operating_system && (
              <div>💾 <span className="font-medium">OS:</span> {asset.operating_system}</div>
            )}
          </div>
        )}
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="border-t bg-white p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Technical Details */}
            <div>
              <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                <Cpu className="w-4 h-4 mr-2 text-blue-600" />
                Technical Details
              </h5>
              <div className="space-y-2 text-sm">
                {asset.hostname && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-600">Hostname:</span>
                    <span className="font-medium">{asset.hostname}</span>
                  </div>
                )}
                {asset.ip_address && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-600">IP Address:</span>
                    <span className="font-medium">{asset.ip_address}</span>
                  </div>
                )}
                {asset.operating_system && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-600">OS:</span>
                    <span className="font-medium">{asset.operating_system}</span>
                  </div>
                )}
                {asset.cpu_cores && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-600">CPU Cores:</span>
                    <span className="font-medium">{asset.cpu_cores}</span>
                  </div>
                )}
                {asset.memory_gb && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-600">Memory:</span>
                    <span className="font-medium">{asset.memory_gb} GB</span>
                  </div>
                )}
                {asset.storage_gb && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-600">Storage:</span>
                    <span className="font-medium">{asset.storage_gb} GB</span>
                  </div>
                )}
              </div>
            </div>

            {/* Business Details */}
            <div>
              <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                <Building className="w-4 h-4 mr-2 text-green-600" />
                Business Details
              </h5>
              <div className="space-y-2 text-sm">
                {asset.department && (
                  <div className="flex items-start">
                    <span className="w-24 text-gray-600">Department:</span>
                    <span className="font-medium">{asset.department}</span>
                  </div>
                )}
                {asset.business_criticality && (
                  <div className="flex items-start">
                    <span className="w-24 text-gray-600">Criticality:</span>
                    <span className={`font-medium ${getCriticalityColor(asset.business_criticality)}`}>
                      {asset.business_criticality}
                    </span>
                  </div>
                )}
                {asset.business_owner && (
                  <div className="flex items-start">
                    <span className="w-24 text-gray-600">Bus. Owner:</span>
                    <span className="font-medium">{asset.business_owner}</span>
                  </div>
                )}
                {asset.technical_owner && (
                  <div className="flex items-start">
                    <span className="w-24 text-gray-600">Tech Owner:</span>
                    <span className="font-medium">{asset.technical_owner}</span>
                  </div>
                )}
                {asset.location && (
                  <div className="flex items-start">
                    <span className="w-24 text-gray-600">Location:</span>
                    <span className="font-medium">{asset.location}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {asset.description && (
            <div className="mt-4 pt-4 border-t">
              <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                <Info className="w-4 h-4 mr-2 text-gray-600" />
                Description
              </h5>
              <p className="text-sm text-gray-600">{asset.description}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssetCard;