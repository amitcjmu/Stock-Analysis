import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import type { InventoryProgress } from '../types/inventory.types';

interface NextStepCardProps {
  inventoryProgress: InventoryProgress;
  onContinue?: () => void;
}

export const NextStepCard: React.FC<NextStepCardProps> = ({ 
  inventoryProgress, 
  onContinue 
}) => {
  const isComplete = inventoryProgress.classified_assets === inventoryProgress.total_assets;

  return (
    <Card className="mt-6 border-blue-200 bg-blue-50/50">
      <CardHeader>
        <CardTitle className="text-blue-900">Next Step</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-700 mb-4">
          {isComplete ? (
            <>
              Great! All {inventoryProgress.total_assets} assets have been classified. 
              You're ready to proceed to the Application Discovery phase where AI agents 
              will identify your applications and their dependencies.
            </>
          ) : (
            <>
              {inventoryProgress.classified_assets} of {inventoryProgress.total_assets} assets 
              have been classified. Complete the classification to proceed to Application Discovery.
            </>
          )}
        </p>
        {onContinue && isComplete && (
          <Button 
            onClick={onContinue}
            className="w-full md:w-auto"
          >
            Continue to Application Discovery
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
};