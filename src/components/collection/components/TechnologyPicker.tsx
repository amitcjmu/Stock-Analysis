/**
 * Technology Picker Component
 *
 * Provides autocomplete functionality for vendor/product selection with normalization
 * Supports fallback free-entry with agent normalization
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Check, ChevronDown, Plus, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TechnologySelectionOption, VendorProduct } from '../types';

interface TechnologyPickerProps {
  value?: VendorProduct | VendorProduct[];
  onChange: (value: VendorProduct | VendorProduct[] | undefined) => void;
  placeholder?: string;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  helpText?: string;
}

// Mock data for technology options - in real implementation, this would come from API
const MOCK_TECHNOLOGY_OPTIONS: TechnologySelectionOption[] = [
  {
    value: 'microsoft_sqlserver_2019',
    label: 'Microsoft SQL Server 2019',
    vendor: 'Microsoft',
    product: 'SQL Server',
    version: '2019',
    category: 'Database',
    confidence_score: 0.95
  },
  {
    value: 'oracle_database_19c',
    label: 'Oracle Database 19c',
    vendor: 'Oracle',
    product: 'Database',
    version: '19c',
    category: 'Database',
    confidence_score: 0.95
  },
  {
    value: 'apache_tomcat_9',
    label: 'Apache Tomcat 9',
    vendor: 'Apache',
    product: 'Tomcat',
    version: '9',
    category: 'Application Server',
    confidence_score: 0.90
  },
  {
    value: 'vmware_vsphere_7',
    label: 'VMware vSphere 7',
    vendor: 'VMware',
    product: 'vSphere',
    version: '7',
    category: 'Virtualization',
    confidence_score: 0.95
  },
  {
    value: 'redhat_enterprise_linux_8',
    label: 'Red Hat Enterprise Linux 8',
    vendor: 'Red Hat',
    product: 'Enterprise Linux',
    version: '8',
    category: 'Operating System',
    confidence_score: 0.95
  }
];

export const TechnologyPicker: React.FC<TechnologyPickerProps> = ({
  value,
  onChange,
  placeholder = 'Search for vendor/product...',
  multiple = false,
  disabled = false,
  className,
  helpText
}) => {
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [customEntry, setCustomEntry] = useState('');
  const [showCustomEntry, setShowCustomEntry] = useState(false);

  const selectedValues = multiple
    ? (Array.isArray(value) ? value : [])
    : (value ? [value] : []);

  // Filter options based on search term
  const filteredOptions = MOCK_TECHNOLOGY_OPTIONS.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    option.vendor?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    option.product?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = useCallback((option: TechnologySelectionOption) => {
    const newValue: VendorProduct = {
      vendor_name: option.vendor || '',
      product_name: option.product || '',
      product_version: option.version || '',
      category: option.category || '',
      normalized_vendor: option.vendor || '',
      normalized_product: option.product || '',
      confidence_score: option.confidence_score || 0.8
    };

    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      const exists = currentValues.some(v =>
        v.vendor_name === newValue.vendor_name &&
        v.product_name === newValue.product_name &&
        v.product_version === newValue.product_version
      );

      if (!exists) {
        onChange([...currentValues, newValue]);
      }
    } else {
      onChange(newValue);
    }

    setOpen(false);
    setSearchTerm('');
  }, [value, onChange, multiple]);

  const handleCustomEntry = useCallback(() => {
    if (!customEntry.trim()) return;

    // Parse custom entry - try to extract vendor/product from format "Vendor Product Version"
    const parts = customEntry.trim().split(' ');
    const vendor = parts[0] || '';
    const product = parts.slice(1, -1).join(' ') || parts.slice(1).join(' ') || '';
    const version = parts.length > 2 ? parts[parts.length - 1] : '';

    const newValue: VendorProduct = {
      vendor_name: vendor,
      product_name: product || customEntry,
      product_version: version,
      category: 'Unknown',
      confidence_score: 0.5 // Lower confidence for manual entry
    };

    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      onChange([...currentValues, newValue]);
    } else {
      onChange(newValue);
    }

    setCustomEntry('');
    setShowCustomEntry(false);
    setOpen(false);
  }, [customEntry, value, onChange, multiple]);

  const handleRemove = useCallback((toRemove: VendorProduct) => {
    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      const filtered = currentValues.filter(v =>
        !(v.vendor_name === toRemove.vendor_name &&
          v.product_name === toRemove.product_name &&
          v.product_version === toRemove.product_version)
      );
      onChange(filtered);
    } else {
      onChange(undefined);
    }
  }, [value, onChange, multiple]);

  const displayValue = selectedValues.length > 0
    ? selectedValues.map(v => `${v.vendor_name} ${v.product_name} ${v.product_version}`.trim()).join(', ')
    : '';

  return (
    <div className={cn('space-y-2', className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between text-left font-normal"
            disabled={disabled}
          >
            <span className={cn(!displayValue && 'text-muted-foreground')}>
              {displayValue || placeholder}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0" align="start">
          <Command>
            <CommandInput
              placeholder="Search technologies..."
              value={searchTerm}
              onValueChange={setSearchTerm}
            />
            <CommandList>
              <CommandEmpty>
                <div className="p-2 space-y-2">
                  <p className="text-sm text-muted-foreground">No technologies found</p>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => setShowCustomEntry(true)}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add custom entry
                  </Button>
                </div>
              </CommandEmpty>
              <CommandGroup>
                {filteredOptions.map((option) => (
                  <CommandItem
                    key={option.value}
                    onSelect={() => handleSelect(option)}
                    className="cursor-pointer"
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex-1">
                        <div className="font-medium">{option.label}</div>
                        <div className="text-xs text-muted-foreground">
                          {option.category}
                        </div>
                      </div>
                      {option.confidence_score && (
                        <Badge variant="outline" className="text-xs">
                          {Math.round(option.confidence_score * 100)}%
                        </Badge>
                      )}
                    </div>
                  </CommandItem>
                ))}
                {filteredOptions.length > 0 && (
                  <CommandItem
                    onSelect={() => setShowCustomEntry(true)}
                    className="cursor-pointer border-t"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add custom technology
                  </CommandItem>
                )}
              </CommandGroup>
            </CommandList>
          </Command>

          {showCustomEntry && (
            <div className="border-t p-3 space-y-2">
              <Input
                placeholder="Enter vendor product version..."
                value={customEntry}
                onChange={(e) => setCustomEntry(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleCustomEntry();
                  }
                }}
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleCustomEntry}>
                  Add
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setShowCustomEntry(false);
                    setCustomEntry('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </PopoverContent>
      </Popover>

      {/* Selected Items Display */}
      {selectedValues.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedValues.map((item, index) => (
            <Badge key={index} variant="secondary" className="flex items-center gap-1">
              <span>{`${item.vendor_name} ${item.product_name} ${item.product_version}`.trim()}</span>
              {!disabled && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-auto p-0 w-4 h-4"
                  onClick={() => handleRemove(item)}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </Badge>
          ))}
        </div>
      )}

      {helpText && (
        <p className="text-xs text-muted-foreground">
          {helpText}
        </p>
      )}
    </div>
  );
};
