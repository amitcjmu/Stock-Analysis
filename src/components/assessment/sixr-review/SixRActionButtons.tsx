import React from 'react';
import { Save, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SixRActionButtonsProps {
  isDraft: boolean;
  isSubmitting: boolean;
  isLoading: boolean;
  selectedApp: string;
  onSaveDraft: () => void;
  onSubmit: () => void;
}

export const SixRActionButtons: React.FC<SixRActionButtonsProps> = ({
  isDraft,
  isSubmitting,
  isLoading,
  selectedApp,
  onSaveDraft,
  onSubmit
}) => {
  return (
    <div className="flex justify-between items-center pt-6 border-t border-gray-200">
      <div className="flex items-center space-x-2">
        <Button 
          variant="outline" 
          onClick={onSaveDraft}
          disabled={isDraft || !selectedApp}
        >
          <Save className="h-4 w-4 mr-2" />
          {isDraft ? 'Saving...' : 'Save Progress'}
        </Button>
      </div>
      
      <Button 
        onClick={onSubmit}
        disabled={isSubmitting || isLoading}
        size="lg"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            Continue to Application Review
            <ArrowRight className="h-4 w-4 ml-2" />
          </>
        )}
      </Button>
    </div>
  );
};