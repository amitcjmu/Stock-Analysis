import React from 'react';
import { useState } from 'react';
import { Server, Database, Cpu, Router, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ClassificationCard } from './ClassificationCard';
import { ApplicationSelectionModal } from '../ApplicationSelectionModal';
import type { InventoryProgress } from '../../types/inventory.types';

interface ClassificationCardsProps {
  inventoryProgress: InventoryProgress;
  selectedAssetType: string;
  onAssetTypeSelect: (type: string) => void;
  flowId?: string;
}

export const ClassificationCards: React.FC<ClassificationCardsProps> = ({
  inventoryProgress,
  selectedAssetType,
  onAssetTypeSelect,
  flowId
}) => {
  const [showApplicationModal, setShowApplicationModal] = useState(false);

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
      filterValue: 'Application',
      isApplicationCard: true
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

  const handleCardClick = (card: any) => {
    if (card.isApplicationCard) {
      // For Applications card, show selection modal
      setShowApplicationModal(true);
    }
    // Also trigger the normal filter behavior
    onAssetTypeSelect(
      selectedAssetType === card.filterValue ? 'all' : card.filterValue
    );
  };

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-4">Asset Classification</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {classificationCards.map((card) => (
          <div key={card.type} className="relative">
            <ClassificationCard
              type={card.type}
              label={card.label}
              count={card.count}
              Icon={card.icon}
              color={card.color}
              isActive={selectedAssetType === card.filterValue}
              onClick={() => handleCardClick(card)}
            />
            {card.isApplicationCard && inventoryProgress.applications > 0 && (
              <Button
                size="sm"
                variant="default"
                className="absolute bottom-2 right-2 z-10"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowApplicationModal(true);
                }}
              >
                Process for Assessment
                <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            )}
          </div>
        ))}
      </div>

      {/* Application Selection Modal */}
      {showApplicationModal && (
        <ApplicationSelectionModal
          isOpen={showApplicationModal}
          onClose={() => setShowApplicationModal(false)}
          flowId={flowId}
        />
      )}
    </div>
  );
};
