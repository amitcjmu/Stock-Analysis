/**
 * AssetTypeIcon - Reusable icon component for asset types
 *
 * Phase 4: Assessment Architecture Enhancement
 *
 * Displays appropriate icon based on asset type (server, database, network_device, application, device)
 * Used across ApplicationGroupsWidget and ReadinessDashboardWidget for consistent visualization.
 *
 * @example
 * ```tsx
 * <AssetTypeIcon type="server" className="text-blue-500" />
 * <AssetTypeIcon type="database" className="h-6 w-6" />
 * ```
 */

import React from 'react';
import {
  Server,
  Database,
  Network,
  Package,
  Smartphone,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AssetTypeIconProps {
  type: string;
  className?: string;
}

/**
 * Asset Type Icon Component
 *
 * Maps asset types to appropriate Lucide React icons:
 * - server → Server icon
 * - database → Database icon
 * - network / network_device → Network icon
 * - application → Package icon
 * - device → Smartphone icon
 * - default → Package icon
 */
export const AssetTypeIcon: React.FC<AssetTypeIconProps> = ({ type, className }) => {
  const iconProps = { className: cn('h-4 w-4', className) };

  switch (type.toLowerCase()) {
    case 'server':
      return <Server {...iconProps} />;
    case 'database':
      return <Database {...iconProps} />;
    case 'network':
    case 'network_device':
      return <Network {...iconProps} />;
    case 'application':
      return <Package {...iconProps} />;
    case 'device':
      return <Smartphone {...iconProps} />;
    default:
      return <Package {...iconProps} />;
  }
};

export default AssetTypeIcon;
