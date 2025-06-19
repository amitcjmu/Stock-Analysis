import React from 'react';
import { Button } from '../../ui/button';
import { ArrowLeft, ArrowRight } from 'lucide-react';

interface DataCleansingNavigationButtonsProps {
  canContinue: boolean;
  onBackToAttributeMapping: () => void;
  onContinueToInventory: () => void;
}

const DataCleansingNavigationButtons: React.FC<DataCleansingNavigationButtonsProps> = ({
  canContinue,
  onBackToAttributeMapping,
  onContinueToInventory
}) => {
  return (
    <div className="flex justify-between">
      <Button
        onClick={onBackToAttributeMapping}
        variant="outline"
        className="flex items-center space-x-2"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Attribute Mapping</span>
      </Button>

      {canContinue && (
        <Button
          onClick={onContinueToInventory}
          className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
        >
          <span>Continue to Inventory</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};

export default DataCleansingNavigationButtons; 