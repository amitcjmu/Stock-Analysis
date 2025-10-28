/**
 * Tier1GapFillingModal - Modal for collecting missing Tier 1 fields
 *
 * Part of Two-Tier Inline Gap-Filling Design (PR #816)
 * Shows when 6R analysis is blocked due to missing Tier 1 assessment-blocking fields.
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { AlertCircle } from 'lucide-react';
import type { Tier1GapDetail } from '@/lib/api/sixr';

interface Tier1GapFillingModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisId: string;
  tier1_gaps_by_asset: Record<string, Tier1GapDetail[]>;
  onSubmit: (assetId: string, answers: Record<string, string>) => Promise<void>;
}

// Field options for Tier 1 fields
const FIELD_OPTIONS: Record<string, Array<{ value: string; label: string }>> = {
  criticality: [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'critical', label: 'Critical' },
  ],
  business_criticality: [
    { value: 'low', label: 'Low Impact' },
    { value: 'medium', label: 'Medium Impact' },
    { value: 'high', label: 'High Impact' },
    { value: 'critical', label: 'Mission Critical' },
  ],
  application_type: [
    { value: 'custom', label: 'Custom' },
    { value: 'cots', label: 'COTS (Commercial Off-The-Shelf)' },
    { value: 'hybrid', label: 'Hybrid' },
  ],
  migration_priority: [
    { value: '1', label: 'Wave 1 (Highest Priority)' },
    { value: '2', label: 'Wave 2' },
    { value: '3', label: 'Wave 3' },
    { value: '4', label: 'Wave 4' },
    { value: '5', label: 'Wave 5 (Lowest Priority)' },
  ],
};

export function Tier1GapFillingModal({
  isOpen,
  onClose,
  analysisId,
  tier1_gaps_by_asset,
  onSubmit,
}: Tier1GapFillingModalProps) {
  const [answers, setAnswers] = useState<Record<string, Record<string, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentAssetIndex, setCurrentAssetIndex] = useState(0);

  const assetIds = Object.keys(tier1_gaps_by_asset);
  const currentAssetId = assetIds[currentAssetIndex];
  const currentGaps = tier1_gaps_by_asset[currentAssetId] || [];

  // Check if all fields for current asset are filled
  const isCurrentAssetComplete = currentGaps.every(
    (gap) => answers[currentAssetId]?.[gap.field_name]
  );

  // Check if all assets are complete
  const allAssetsComplete = assetIds.every((assetId) =>
    tier1_gaps_by_asset[assetId].every(
      (gap) => answers[assetId]?.[gap.field_name]
    )
  );

  const handleFieldChange = (fieldName: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentAssetId]: {
        ...(prev[currentAssetId] || {}),
        [fieldName]: value,
      },
    }));
  };

  const handleNext = () => {
    if (currentAssetIndex < assetIds.length - 1) {
      setCurrentAssetIndex((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentAssetIndex > 0) {
      setCurrentAssetIndex((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Submit answers for all assets
      for (const assetId of assetIds) {
        await onSubmit(assetId, answers[assetId] || {});
      }
      onClose();
    } catch (error) {
      console.error('Failed to submit gap answers:', error);
      alert('Failed to submit answers. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-500" />
            Required Information for 6R Analysis
          </DialogTitle>
          <DialogDescription>
            The following information is required to complete the 6R assessment.
            These fields are assessment-blocking and must be filled before AI
            agents can proceed with the analysis.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Progress indicator */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Application {currentAssetIndex + 1} of {assetIds.length}
            </span>
            <span>
              {Object.keys(answers).filter((id) =>
                tier1_gaps_by_asset[id]?.every(
                  (gap) => answers[id]?.[gap.field_name]
                )
              ).length}{' '}
              / {assetIds.length} complete
            </span>
          </div>

          {/* Current asset info */}
          <div className="rounded-lg border p-4 bg-muted/50">
            <h3 className="font-medium mb-1">Asset ID</h3>
            <p className="text-sm text-muted-foreground font-mono">
              {currentAssetId}
            </p>
          </div>

          {/* Gap fields */}
          <div className="space-y-4">
            {currentGaps.map((gap) => {
              const options = FIELD_OPTIONS[gap.field_name] || [];
              const currentValue = answers[currentAssetId]?.[gap.field_name];

              return (
                <div key={gap.field_name} className="space-y-2">
                  <Label htmlFor={gap.field_name}>
                    {gap.display_name}
                    <span className="text-red-500 ml-1">*</span>
                  </Label>
                  <Select
                    value={currentValue || ''}
                    onValueChange={(value) =>
                      handleFieldChange(gap.field_name, value)
                    }
                  >
                    <SelectTrigger id={gap.field_name}>
                      <SelectValue placeholder={`Select ${gap.display_name.toLowerCase()}`} />
                    </SelectTrigger>
                    <SelectContent>
                      {options.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground">
                    {gap.reason}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        <DialogFooter className="flex justify-between items-center">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentAssetIndex === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              onClick={handleNext}
              disabled={currentAssetIndex === assetIds.length - 1}
            >
              Next
            </Button>
          </div>

          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!allAssetsComplete || isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit & Start Analysis'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
