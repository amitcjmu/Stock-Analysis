/**
 * Asset Selector Component
 *
 * A specialized component for selecting assets with metadata about completeness,
 * gaps, and types. Designed for asset-aware collection in migration workflows.
 * CC: Frontend component for asset selection with type filtering and search
 */

import React, { useState, useMemo } from 'react';
import { Search, Filter, Check } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import type { FieldOption } from './types';

interface AssetSelectorProps {
  options: FieldOption[];
  value: string | string[];
  onChange: (value: string | string[]) => void;
  multiple?: boolean;
  required?: boolean;
  showCompleteness?: boolean;
  showTypeFilter?: boolean;
  allowSearch?: boolean;
  placeholder?: string;
  className?: string;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  options,
  value,
  onChange,
  multiple = false,
  showCompleteness = true,
  showTypeFilter = true,
  allowSearch = true,
  placeholder = "Select assets...",
  className,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  // Ensure value is always an array for easier handling
  const selectedValues = useMemo(() => {
    if (Array.isArray(value)) return value;
    return value ? [value] : [];
  }, [value]);

  // Filter options based on search and type
  const filteredOptions = useMemo(() => {
    return options.filter(opt => {
      const matchesSearch = !searchTerm ||
        opt.label.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = !typeFilter ||
        opt.metadata?.type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [options, searchTerm, typeFilter]);

  // Get unique asset types for filter
  const assetTypes = useMemo(() => {
    const types = new Set(options.map(opt => opt.metadata?.type).filter(Boolean));
    return Array.from(types).sort();
  }, [options]);

  const handleSelectOption = (optionValue: string) => {
    if (multiple) {
      const newValues = selectedValues.includes(optionValue)
        ? selectedValues.filter(v => v !== optionValue)
        : [...selectedValues, optionValue];
      onChange(newValues);
    } else {
      onChange(optionValue);
      setIsOpen(false);
    }
  };

  const getCompletenessColor = (completeness: number) => {
    if (completeness >= 0.8) return 'text-green-600';
    if (completeness >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={cn("space-y-2", className)}>
      {/* Type Filter */}
      {showTypeFilter && assetTypes.length > 1 && (
        <Select value={typeFilter || "all"} onValueChange={(v) => setTypeFilter(v === "all" ? null : v)}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Filter by type..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {assetTypes.map(type => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {/* Search Input */}
      {allowSearch && (
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search assets..."
            className="pl-8"
          />
        </div>
      )}

      {/* Asset Selection Area */}
      <div className="relative">
        <div
          className="min-h-[2.5rem] rounded-md border border-input bg-background px-3 py-2 cursor-pointer"
          onClick={() => setIsOpen(!isOpen)}
        >
          {selectedValues.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {selectedValues.map(val => {
                const option = options.find(opt => opt.value === val);
                return option ? (
                  <Badge key={val} variant="secondary">
                    {option.label}
                  </Badge>
                ) : null;
              })}
            </div>
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
        </div>

        {/* Dropdown Options */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md max-h-64 overflow-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-sm text-muted-foreground">
                No assets found
              </div>
            ) : (
              filteredOptions.map(option => (
                <div
                  key={option.value}
                  className={cn(
                    "px-3 py-2 cursor-pointer hover:bg-accent",
                    selectedValues.includes(option.value) && "bg-accent"
                  )}
                  onClick={() => handleSelectOption(option.value)}
                >
                  <div className="flex items-start gap-2">
                    {multiple && (
                      <Checkbox
                        checked={selectedValues.includes(option.value)}
                        className="mt-1"
                      />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{option.label}</span>
                        {option.metadata?.type && (
                          <Badge variant="outline" className="text-xs">
                            {option.metadata.type}
                          </Badge>
                        )}
                      </div>
                      {showCompleteness && option.metadata?.completeness !== undefined && (
                        <div className="flex items-center gap-2 mt-1">
                          <Progress
                            value={option.metadata.completeness * 100}
                            className="h-2 flex-1"
                          />
                          <span className={cn(
                            "text-xs font-medium",
                            getCompletenessColor(option.metadata.completeness)
                          )}>
                            {Math.round(option.metadata.completeness * 100)}%
                          </span>
                          {option.metadata.gap_count && option.metadata.gap_count > 0 && (
                            <Badge variant="destructive" className="text-xs">
                              {option.metadata.gap_count} gaps
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};
