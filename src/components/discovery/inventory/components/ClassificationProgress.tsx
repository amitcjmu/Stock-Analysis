import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Brain, RefreshCw } from 'lucide-react';
import type { InventoryProgress } from '../types/inventory.types';

interface ClassificationProgressProps {
  inventoryProgress: InventoryProgress;
  onRefresh?: () => void;
  needsClassification?: boolean;
}

export const ClassificationProgress: React.FC<ClassificationProgressProps> = ({ 
  inventoryProgress, 
  onRefresh,
  needsClassification = false
}) => {
  const completionPercentage = Math.round(
    (inventoryProgress.classified_assets / inventoryProgress.total_assets) * 100
  );

  return (
    <Card className="mb-6">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          AI-Powered Classification Progress
        </CardTitle>
        {onRefresh && (
          <Button 
            variant={needsClassification ? "default" : "outline"} 
            size="sm" 
            onClick={onRefresh}
            className={needsClassification ? "bg-orange-600 hover:bg-orange-700" : ""}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {needsClassification ? "Run Classification" : "Refresh"}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-gray-600">
                {inventoryProgress.classified_assets} of {inventoryProgress.total_assets} assets
              </span>
            </div>
            <Progress value={completionPercentage} className="h-3" />
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Classification Accuracy</span>
              <p className="font-semibold text-green-600">
                {inventoryProgress.classification_accuracy}%
              </p>
            </div>
            <div>
              <span className="text-gray-600">Completion Status</span>
              <p className="font-semibold">
                {completionPercentage === 100 ? 'Complete' : 'In Progress'}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};