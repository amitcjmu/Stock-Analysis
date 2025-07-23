import React from 'react';
import type { Server, Database, Cpu, Router } from 'lucide-react';
import { ClassificationCard } from './ClassificationCard';
import type { InventoryProgress } from '../../types/inventory.types';

interface ClassificationCardsProps {
  inventoryProgress: InventoryProgress;
  selectedAssetType: string;
  onAssetTypeSelect: (type: string) => void;
}

export const ClassificationCards: React.FC<ClassificationCardsProps> = ({
  inventoryProgress,
  selectedAssetType,
  onAssetTypeSelect
}) => {
  const classificationCards = [
    {
      type: 'servers',
      label: 'Servers',
      count: inventoryProgress.servers,
      icon: Server,
      color: 'blue',
      filterValue: 'Server'
    },
    {
      type: 'applications',
      label: 'Applications',
      count: inventoryProgress.applications,
      icon: Cpu,
      color: 'green',
      filterValue: 'Application'
    },
    {
      type: 'databases',
      label: 'Databases',
      count: inventoryProgress.databases,
      icon: Database,
      color: 'purple',
      filterValue: 'Database'
    },
    {
      type: 'devices',
      label: 'Network Devices',
      count: inventoryProgress.devices,
      icon: Router,
      color: 'orange',
      filterValue: 'Device'
    }
  ];

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-4">Asset Classification</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {classificationCards.map((card) => (
          <ClassificationCard
            key={card.type}
            type={card.type}
            label={card.label}
            count={card.count}
            Icon={card.icon}
            color={card.color}
            isActive={selectedAssetType === card.filterValue}
            onClick={() => onAssetTypeSelect(
              selectedAssetType === card.filterValue ? 'all' : card.filterValue
            )}
          />
        ))}
      </div>
    </div>
  );
};