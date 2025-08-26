import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Users,
  Layers,
  ArrowRight,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  SimilarityMatch,
  DuplicateDecision,
  CanonicalApplication,
  ApplicationVariant,
} from '@/types/collection/canonical-applications';

interface DuplicateDetectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  userInput: string;
  detectedMatches: SimilarityMatch[];
  onDecision: (
    decision: DuplicateDecision,
    selectedMatch?: SimilarityMatch,
    canonicalApplication?: CanonicalApplication
  ) => void;
  isProcessing?: boolean;
}

/**
 * DuplicateDetectionModal Component
 *
 * Shows when potential duplicate applications are detected. Provides a clear
 * comparison between user input and existing applications, with confidence
 * scores and detailed information to help users make informed decisions.
 */
export const DuplicateDetectionModal: React.FC<DuplicateDetectionModalProps> = ({
  isOpen,
  onClose,
  userInput,
  detectedMatches,
  onDecision,
  isProcessing = false,
}) => {
  const [selectedMatch, setSelectedMatch] = useState<SimilarityMatch | null>(
    detectedMatches.length > 0 ? detectedMatches[0] : null
  );

  // Get confidence color and label
  const getConfidenceDisplay = (confidence: number) => {
    if (confidence >= 0.95) {
      return {
        color: "text-green-600 bg-green-100",
        label: "Very High",
        description: "Almost certainly the same application"
      };
    } else if (confidence >= 0.85) {
      return {
        color: "text-yellow-600 bg-yellow-100",
        label: "High",
        description: "Likely the same application"
      };
    } else if (confidence >= 0.75) {
      return {
        color: "text-orange-600 bg-orange-100",
        label: "Medium",
        description: "Possibly the same application"
      };
    } else {
      return {
        color: "text-blue-600 bg-blue-100",
        label: "Low",
        description: "Some similarity detected"
      };
    }
  };

  // Format match reasons for display
  const formatMatchReasons = (reasons: string[]) => {
    return reasons.map(reason => {
      switch (reason) {
        case 'exact_match':
          return 'Exact name match';
        case 'case_insensitive':
          return 'Case-insensitive match';
        case 'punctuation_normalized':
          return 'Punctuation differences only';
        case 'fuzzy_high':
          return 'Very similar spelling';
        case 'fuzzy_medium':
          return 'Similar spelling';
        case 'partial_token':
          return 'Contains same words';
        case 'acronym_match':
          return 'Acronym or abbreviation';
        default:
          return reason.replace('_', ' ');
      }
    });
  };

  // Handle decision actions
  const handleUseExisting = () => {
    if (selectedMatch) {
      onDecision('use_existing', selectedMatch, selectedMatch.canonical_application);
    }
  };

  const handleCreateNew = () => {
    onDecision('create_new');
  };

  const handleCancel = () => {
    onDecision('cancelled');
    onClose();
  };

  if (!isOpen || detectedMatches.length === 0) {
    return null;
  }

  const topMatch = selectedMatch || detectedMatches[0];
  const confidenceDisplay = getConfidenceDisplay(topMatch.confidence_score);
  const matchReasons = formatMatchReasons(topMatch.match_reasons);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            Potential Duplicate Detected
          </DialogTitle>
          <DialogDescription>
            We found {detectedMatches.length} existing application{detectedMatches.length > 1 ? 's' : ''}
            that might be the same as "<strong>{userInput}</strong>".
            Please review and decide whether to use an existing application or create a new one.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Confidence Alert */}
          <Alert className={cn("border-l-4", confidenceDisplay.color.includes('green') ? "border-l-green-500" :
                              confidenceDisplay.color.includes('yellow') ? "border-l-yellow-500" :
                              confidenceDisplay.color.includes('orange') ? "border-l-orange-500" :
                              "border-l-blue-500")}>
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>
              <div className="flex items-center justify-between">
                <span>
                  <strong>{confidenceDisplay.label} confidence match</strong> - {confidenceDisplay.description}
                </span>
                <Badge className={confidenceDisplay.color}>
                  {topMatch.confidence_score != null && !isNaN(topMatch.confidence_score)
                    ? Math.round(topMatch.confidence_score * 100)
                    : 0}% match
                </Badge>
              </div>
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: User Input */}
            <div className="space-y-4">
              <div className="border border-blue-200 bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Your Input</h3>
                <div className="text-lg font-medium text-blue-800">"{userInput}"</div>
                <div className="mt-2 text-sm text-blue-700">
                  This would create a new application entry
                </div>
              </div>

              {/* Match Reasons */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Why this might be a duplicate:</h4>
                <ul className="space-y-1">
                  {matchReasons.map((reason, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Right Column: Existing Applications */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Existing Applications</h3>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {detectedMatches.map((match, index) => {
                  const isSelected = selectedMatch?.canonical_application.id === match.canonical_application.id;
                  const matchConfidence = getConfidenceDisplay(match.confidence_score);

                  return (
                    <div
                      key={match.canonical_application.id}
                      className={cn(
                        "border rounded-lg p-4 cursor-pointer transition-all",
                        isSelected
                          ? "border-blue-500 bg-blue-50 shadow-md"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                      )}
                      onClick={() => setSelectedMatch(match)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">
                            {match.canonical_application.canonical_name}
                          </div>
                          {match.canonical_application.description && (
                            <div className="text-sm text-gray-600 mt-1">
                              {match.canonical_application.description}
                            </div>
                          )}
                        </div>
                        <Badge className={matchConfidence.color}>
                          {match.confidence_score != null && !isNaN(match.confidence_score)
                            ? Math.round(match.confidence_score * 100)
                            : 0}%
                        </Badge>
                      </div>

                      {/* Variants */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Layers className="h-3 w-3" />
                          <span>{match.canonical_application.variants.length} variant{match.canonical_application.variants.length !== 1 ? 's' : ''}:</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {match.canonical_application.variants.slice(0, 3).map((variant) => (
                            <Badge key={variant.id} variant="outline" className="text-xs">
                              {variant.variant_name}
                            </Badge>
                          ))}
                          {match.canonical_application.variants.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{match.canonical_application.variants.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Collection History */}
                      {match.canonical_application.metadata.last_collected_at && (
                        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          <span>
                            Last collected: {new Date(match.canonical_application.metadata.last_collected_at).toLocaleDateString()}
                          </span>
                          <span className="mx-1">•</span>
                          <span>
                            {match.canonical_application.metadata.collection_count} collection{match.canonical_application.metadata.collection_count !== 1 ? 's' : ''}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Selected Application Details */}
          {selectedMatch && (
            <div className="border border-green-200 bg-green-50 rounded-lg p-4">
              <h4 className="font-medium text-green-900 mb-2">
                Selected: {selectedMatch.canonical_application.canonical_name}
              </h4>
              <div className="text-sm text-green-800">
                Your input "{userInput}" will be added as a new variant to this application.
                This helps maintain consistency and improves future suggestions.
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-between gap-4 pt-4 border-t">
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={isProcessing}
              className="order-3 sm:order-1"
            >
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>

            <div className="flex flex-col sm:flex-row gap-2 order-1 sm:order-2">
              <Button
                variant="outline"
                onClick={handleCreateNew}
                disabled={isProcessing}
                className="w-full sm:w-auto"
              >
                Create New Application
              </Button>
              <Button
                onClick={handleUseExisting}
                disabled={!selectedMatch || isProcessing}
                className="w-full sm:w-auto"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    Use Existing Application
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Help Text */}
          <div className="text-xs text-gray-500 bg-gray-50 rounded p-3">
            <strong>Tip:</strong> Choosing "Use Existing" helps improve future suggestions and maintains
            consistency across your application inventory. The system will remember that "{userInput}"
            refers to the selected application.
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
