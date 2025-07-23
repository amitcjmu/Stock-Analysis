import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { TrendingUp, Target, Activity, CheckCircle } from 'lucide-react';
import type { InventoryProgress } from '../types/inventory.types';

interface InventoryOverviewProps {
  inventoryProgress: InventoryProgress;
}

export const InventoryOverview: React.FC<InventoryOverviewProps> = ({ inventoryProgress }) => {
  const overviewCards = [
    {
      title: 'Total IT Assets',
      value: inventoryProgress.total_assets,
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Classified Assets',
      value: inventoryProgress.classified_assets,
      icon: Target,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Accuracy Score',
      value: `${inventoryProgress.classification_accuracy}%`,
      icon: Activity,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'Completion',
      value: inventoryProgress.total_assets > 0 
        ? `${Math.round((inventoryProgress.classified_assets / inventoryProgress.total_assets) * 100)}%`
        : '0%',
      icon: CheckCircle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {overviewCards.map((card, index) => (
        <Card key={index}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${card.bgColor}`}>
                <card.icon className={`h-6 w-6 ${card.color}`} />
              </div>
              <span className={`text-2xl font-bold ${card.color}`}>
                {card.value}
              </span>
            </div>
            <h3 className="text-sm font-medium text-gray-600">{card.title}</h3>
            {card.title === 'Completion' && (
              <Progress 
                value={inventoryProgress.total_assets > 0 
                  ? (inventoryProgress.classified_assets / inventoryProgress.total_assets) * 100
                  : 0} 
                className="mt-2 h-2" 
              />
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};