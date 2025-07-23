/**
 * Conflict Resolver Component
 * 
 * Interface for resolving data conflicts between sources
 * Agent Team B3 - Data conflict resolution component
 */

import React from 'react'
import type { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { FormInput } from 'lucide-react'
import { GitMerge, AlertTriangle, CheckCircle, Clock, User, Database, Upload } from 'lucide-react'
import { cn } from '@/lib/utils';

import type { ConflictResolverProps, DataConflict, ConflictingValue, ConflictResolution } from '../types';

export const ConflictResolver: React.FC<ConflictResolverProps> = ({
  conflicts,
  onResolve,
  className
}) => {
  const [selectedResolutions, setSelectedResolutions] = useState<Record<string, ConflictResolution>>({});
  const [justifications, setJustifications] = useState<Record<string, string>>({});

  const getSourceIcon = (source: ConflictingValue['source']) => {
    switch (source) {
      case 'automated':
        return <Database className="h-4 w-4 text-blue-600" />;
      case 'manual':
        return <FormInput className="h-4 w-4 text-green-600" />;
      case 'bulk':
        return <Upload className="h-4 w-4 text-purple-600" />;
      case 'template':
        return <User className="h-4 w-4 text-amber-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSourceBadge = (source: ConflictingValue['source']) => {
    const config = {
      automated: { label: 'Automated', className: 'bg-blue-100 text-blue-800' },
      manual: { label: 'Manual Form', className: 'bg-green-100 text-green-800' },
      bulk: { label: 'Bulk Upload', className: 'bg-purple-100 text-purple-800' },
      template: { label: 'Template', className: 'bg-amber-100 text-amber-800' }
    };
    
    const sourceConfig = config[source] || { label: source, className: 'bg-gray-100 text-gray-800' };
    
    return (
      <Badge variant="secondary" className={sourceConfig.className}>
        {sourceConfig.label}
      </Badge>
    );
  };

  const handleValueSelection = (conflictId: string, value: ConflictingValue) => {
    setSelectedResolutions(prev => ({
      ...prev,
      [conflictId]: {
        selectedValue: value.value,
        selectedSource: value.sourceId,
        userJustification: justifications[conflictId]
      }
    }));
  };

  const handleJustificationChange = (conflictId: string, justification: string) => {
    setJustifications(prev => ({
      ...prev,
      [conflictId]: justification
    }));
    
    // Update resolution if already selected
    if (selectedResolutions[conflictId]) {
      setSelectedResolutions(prev => ({
        ...prev,
        [conflictId]: {
          ...prev[conflictId],
          userJustification: justification
        }
      }));
    }
  };

  const handleResolveConflict = (conflictId: string) => {
    const resolution = selectedResolutions[conflictId];
    if (resolution) {
      onResolve(conflictId, resolution);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (conflicts.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center">
          <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-green-800">No conflicts detected</h3>
          <p className="text-green-600">All data sources are consistent</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <GitMerge className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-semibold">Data Conflicts</h3>
        <Badge variant="destructive">{conflicts.length} conflicts</Badge>
      </div>
      
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Review the conflicting data points below and select the most accurate value for each attribute. 
          Your selections will be used in the final integrated dataset.
        </AlertDescription>
      </Alert>

      {conflicts.map((conflict) => (
        <Card key={conflict.id} className="border-orange-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">{conflict.attributeLabel}</CardTitle>
                <CardDescription>
                  {conflict.conflictingValues.length} different values found from multiple sources
                </CardDescription>
              </div>
              
              {conflict.requiresUserReview && (
                <Badge variant="destructive">Manual Review Required</Badge>
              )}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Conflicting Values */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Select the correct value:</h4>
              
              <RadioGroup
                value={selectedResolutions[conflict.id]?.selectedSource || ''}
                onValueChange={(sourceId) => {
                  const value = conflict.conflictingValues.find(v => v.sourceId === sourceId);
                  if (value) {
                    handleValueSelection(conflict.id, value);
                  }
                }}
                className="space-y-3"
              >
                {conflict.conflictingValues.map((value, index) => (
                  <div 
                    key={`${conflict.id}-${index}`}
                    className={cn(
                      'flex items-start space-x-3 p-3 rounded-lg border transition-colors',
                      selectedResolutions[conflict.id]?.selectedSource === value.sourceId 
                        ? 'border-primary bg-primary/5' 
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <RadioGroupItem value={value.sourceId} id={`${conflict.id}-${index}`} className="mt-1" />
                    
                    <div className="flex-1 min-w-0">
                      <Label htmlFor={`${conflict.id}-${index}`} className="cursor-pointer">
                        <div className="flex items-center gap-2 mb-2">
                          {getSourceIcon(value.source)}
                          {getSourceBadge(value.source)}
                          <Badge variant="outline" className="text-xs">
                            {Math.round(value.confidenceScore * 100)}% confidence
                          </Badge>
                        </div>
                        
                        <div className="p-2 bg-muted rounded text-sm font-mono">
                          {typeof value.value === 'object' 
                            ? JSON.stringify(value.value, null, 2)
                            : String(value.value)
                          }
                        </div>
                        
                        <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          Collected: {formatTimestamp(value.collectedAt)}
                        </div>
                      </Label>
                    </div>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {/* Recommended Resolution */}
            {conflict.recommendedResolution && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h5 className="text-sm font-medium text-blue-900 mb-1">
                  System Recommendation
                </h5>
                <p className="text-sm text-blue-800">
                  {conflict.recommendedResolution}
                </p>
              </div>
            )}

            {/* Justification */}
            {selectedResolutions[conflict.id] && (
              <div className="space-y-2">
                <Label htmlFor={`justification-${conflict.id}`} className="text-sm font-medium">
                  Justification (optional)
                </Label>
                <Textarea
                  id={`justification-${conflict.id}`}
                  placeholder="Explain why you selected this value..."
                  value={justifications[conflict.id] || ''}
                  onChange={(e) => handleJustificationChange(conflict.id, e.target.value)}
                  className="h-20"
                />
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-2 border-t">
              <div className="text-xs text-muted-foreground">
                Attribute: {conflict.attributeName}
              </div>
              
              <Button
                onClick={() => handleResolveConflict(conflict.id)}
                disabled={!selectedResolutions[conflict.id]}
                size="sm"
              >
                Resolve Conflict
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
      
      {/* Bulk Actions */}
      {conflicts.length > 1 && (
        <Card className="border-dashed">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">Bulk Actions</h4>
                <p className="text-sm text-muted-foreground">
                  Apply resolution strategy to all conflicts
                </p>
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  Prefer Automated
                </Button>
                <Button variant="outline" size="sm">
                  Prefer Manual
                </Button>
                <Button variant="outline" size="sm">
                  Prefer Latest
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};