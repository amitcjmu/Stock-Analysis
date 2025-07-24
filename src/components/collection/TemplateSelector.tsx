/**
 * Template Selector Component
 * 
 * Interface for selecting and applying templates to forms
 * Agent Team B3 - Task B3.4 Frontend Implementation
 */

import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Star, Clock, Target, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

import type { TemplateOption, TemplateMatchResult } from './types';

interface TemplateSelectorProps {
  templates: TemplateOption[];
  recommendations?: TemplateMatchResult[];
  onSelect: (templateId: string) => void;
  className?: string;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  recommendations = [],
  onSelect,
  className
}) => {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  return (
    <div className={cn('space-y-4', className)}>
      <div>
        <h3 className="text-lg font-semibold">Application Templates</h3>
        <p className="text-sm text-muted-foreground">
          Choose a template to speed up data collection for similar applications
        </p>
      </div>

      {recommendations.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-green-700">Recommended for You</h4>
          {recommendations.slice(0, 2).map(rec => (
            <Card key={rec.templateId} className="border-green-200 bg-green-50">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{rec.templateName}</CardTitle>
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    {Math.round(rec.matchScore * 100)}% match
                  </Badge>
                </div>
                <CardDescription>
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="h-3 w-3" />
                    Save ~{rec.estimatedTimeSavings}min
                  </div>
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">
                    {rec.applicableReasons.join(' • ')}
                  </div>
                  <Button size="sm" onClick={() => onSelect(rec.templateId)}>
                    Use Template
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map(template => (
          <Card 
            key={template.id} 
            className={cn(
              'cursor-pointer transition-colors hover:bg-muted/50',
              selectedTemplate === template.id && 'ring-2 ring-primary'
            )}
            onClick={() => setSelectedTemplate(template.id)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{template.name}</CardTitle>
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4 text-amber-500" />
                  <span className="text-sm font-medium">
                    {template.effectivenessScore.toFixed(1)}
                  </span>
                </div>
              </div>
              <CardDescription className="text-sm">
                {template.description}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="pt-0">
              <div className="space-y-2">
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Target className="h-3 w-3" />
                    {template.fieldCount} fields
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {template.applicableTypes.length} app types
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-1">
                  {template.applicableTypes.slice(0, 3).map(type => (
                    <Badge key={type} variant="outline" className="text-xs">
                      {type}
                    </Badge>
                  ))}
                  {template.applicableTypes.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{template.applicableTypes.length - 3} more
                    </Badge>
                  )}
                </div>
                
                <Button 
                  size="sm" 
                  className="w-full"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelect(template.id);
                  }}
                >
                  Apply Template
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};