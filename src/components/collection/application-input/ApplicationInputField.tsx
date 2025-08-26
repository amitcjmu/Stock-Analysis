import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Check, AlertTriangle, Plus, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type {
  ApplicationSuggestion,
  ApplicationInputState,
  DuplicateDetectionState,
  SimilarityMatch,
  DEFAULT_DEDUPLICATION_CONFIG,
} from '@/types/collection/canonical-applications';
import { useApplicationSuggestions } from '@/hooks/collection/deduplication/useApplicationSuggestions';
import { useDuplicateDetection } from '@/hooks/collection/deduplication/useDuplicateDetection';

interface ApplicationInputFieldProps {
  value: string;
  onChange: (value: string) => void;
  onApplicationSelected: (suggestion: ApplicationSuggestion | null, userInput: string) => void;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  className?: string;
  showConfidenceScores?: boolean;
  maxSuggestions?: number;
  confidenceThresholds?: typeof DEFAULT_DEDUPLICATION_CONFIG.confidence_thresholds;
}

/**
 * ApplicationInputField Component
 *
 * A smart input field that provides real-time application suggestions with
 * confidence scoring and duplicate detection. Handles keyboard navigation,
 * accessibility, and integrates with the deduplication system.
 */
export const ApplicationInputField: React.FC<ApplicationInputFieldProps> = ({
  value,
  onChange,
  onApplicationSelected,
  placeholder = "Enter application name...",
  disabled = false,
  autoFocus = false,
  className,
  showConfidenceScores = false,
  maxSuggestions = 8,
  confidenceThresholds,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Custom hooks for functionality
  const {
    suggestions,
    isLoading,
    error,
    searchSuggestions,
    clearSuggestions,
  } = useApplicationSuggestions({
    maxResults: maxSuggestions,
    confidenceThresholds,
  });

  const {
    duplicateMatches,
    isDuplicateDetected,
    checkForDuplicates,
    clearDuplicateState,
  } = useDuplicateDetection({
    confidenceThresholds,
  });

  // Handle input changes with debounced suggestions
  const handleInputChange = useCallback((newValue: string) => {
    onChange(newValue);
    setSelectedIndex(-1);

    if (newValue.trim().length >= 2) {
      searchSuggestions(newValue.trim());
      setShowSuggestions(true);
    } else {
      clearSuggestions();
      setShowSuggestions(false);
    }
  }, [onChange, searchSuggestions, clearSuggestions]);

  // Handle input blur with delay to allow for suggestion clicks
  const handleInputBlur = useCallback(() => {
    // Delay hiding suggestions to allow clicks to register
    setTimeout(() => {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }, 150);
  }, []);

  // Handle input focus
  const handleInputFocus = useCallback(() => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  }, [suggestions.length]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (event.key === 'Enter' && value.trim()) {
        // Check for duplicates before allowing manual entry
        checkForDuplicates(value.trim());
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;

      case 'ArrowUp':
        event.preventDefault();
        setSelectedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;

      case 'Enter':
        event.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          const selectedSuggestion = suggestions[selectedIndex];
          handleSuggestionSelect(selectedSuggestion);
        } else if (value.trim()) {
          // Check for duplicates before allowing manual entry
          checkForDuplicates(value.trim());
        }
        break;

      case 'Escape':
        event.preventDefault();
        setShowSuggestions(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;

      case 'Tab':
        // Allow natural tab behavior, but hide suggestions
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  }, [showSuggestions, suggestions, selectedIndex, value, checkForDuplicates]);

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback((suggestion: ApplicationSuggestion) => {
    onChange(suggestion.display_text);
    onApplicationSelected(suggestion, suggestion.display_text);
    setShowSuggestions(false);
    setSelectedIndex(-1);
    clearDuplicateState();
  }, [onChange, onApplicationSelected, clearDuplicateState]);

  // Handle manual entry (when user doesn't select a suggestion)
  const handleManualEntry = useCallback(() => {
    if (value.trim()) {
      onApplicationSelected(null, value.trim());
      setShowSuggestions(false);
      setSelectedIndex(-1);
      clearDuplicateState();
    }
  }, [value, onApplicationSelected, clearDuplicateState]);

  // Get confidence indicator styles and icon
  const getConfidenceIndicator = (confidence: number) => {
    if (confidence >= (confidenceThresholds?.auto_suggest || 0.95)) {
      return {
        icon: Check,
        className: "text-green-600 bg-green-100",
        label: "Exact match"
      };
    } else if (confidence >= (confidenceThresholds?.duplicate_warning || 0.80)) {
      return {
        icon: AlertTriangle,
        className: "text-yellow-600 bg-yellow-100",
        label: "Similar match"
      };
    } else {
      return {
        icon: Search,
        className: "text-blue-600 bg-blue-100",
        label: "Possible match"
      };
    }
  };

  // Auto-focus effect
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  // Scroll selected suggestion into view
  useEffect(() => {
    if (selectedIndex >= 0 && suggestionsRef.current) {
      const selectedElement = suggestionsRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    }
  }, [selectedIndex]);

  return (
    <div className={cn("relative w-full", className)}>
      {/* Input Field */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "pl-10 pr-4",
            error && "border-red-300 focus:border-red-500 focus:ring-red-500"
          )}
          aria-expanded={showSuggestions}
          aria-haspopup="listbox"
          aria-autocomplete="list"
          role="combobox"
          aria-describedby={error ? "input-error" : undefined}
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div id="input-error" className="mt-1 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto"
          role="listbox"
        >
          {suggestions.map((suggestion, index) => {
            const indicator = getConfidenceIndicator(suggestion.confidence_score);
            const Icon = indicator.icon;

            return (
              <div
                key={`${suggestion.id}-${index}`}
                className={cn(
                  "flex items-center justify-between px-4 py-3 cursor-pointer transition-colors",
                  selectedIndex === index
                    ? "bg-blue-50 border-l-2 border-blue-500"
                    : "hover:bg-gray-50",
                  "focus:bg-blue-50 focus:outline-none"
                )}
                role="option"
                aria-selected={selectedIndex === index}
                onClick={() => handleSuggestionSelect(suggestion)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <div
                      className={cn(
                        "flex items-center justify-center w-5 h-5 rounded-full",
                        indicator.className
                      )}
                    >
                      <Icon className="w-3 h-3" />
                    </div>
                    <div className="font-medium text-gray-900 truncate">
                      {suggestion.highlighted_text ? (
                        <span
                          dangerouslySetInnerHTML={{
                            __html: suggestion.highlighted_text
                          }}
                        />
                      ) : (
                        suggestion.display_text
                      )}
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    {suggestion.canonical_application.metadata.total_variants} variant
                    {suggestion.canonical_application.metadata.total_variants !== 1 ? 's' : ''}
                    {suggestion.canonical_application.metadata.last_collected_at && (
                      <span className="ml-2">
                        • Last collected {new Date(suggestion.canonical_application.metadata.last_collected_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {showConfidenceScores && (
                    <Badge variant="outline" className="text-xs">
                      {suggestion.confidence_score != null && !isNaN(suggestion.confidence_score)
                        ? Math.round(suggestion.confidence_score * 100)
                        : 0}%
                    </Badge>
                  )}
                  <Badge variant="secondary" className="text-xs">
                    {suggestion.match_type.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
            );
          })}

          {/* Manual entry option */}
          {value.trim() && (
            <div className="border-t border-gray-200">
              <div
                className={cn(
                  "flex items-center justify-between px-4 py-3 cursor-pointer transition-colors",
                  selectedIndex === suggestions.length
                    ? "bg-blue-50 border-l-2 border-blue-500"
                    : "hover:bg-gray-50"
                )}
                onClick={handleManualEntry}
                onMouseEnter={() => setSelectedIndex(suggestions.length)}
              >
                <div className="flex items-center gap-2">
                  <div className="flex items-center justify-center w-5 h-5 rounded-full bg-gray-100">
                    <Plus className="w-3 h-3 text-gray-600" />
                  </div>
                  <span className="text-gray-700">
                    Create new: "<span className="font-medium">{value.trim()}</span>"
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
