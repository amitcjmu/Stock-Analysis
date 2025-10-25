/**
 * Question Filter Controls Component
 *
 * Provides UI controls for:
 * - Filtering questions by answered status
 * - Filtering questions by section
 * - Displaying question counts
 * - Agent-based question pruning
 * - Agent analysis status
 *
 * Issue #796 - Frontend UI Integration for Dynamic Questions
 */

import React from 'react';
import { RefreshCw, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

export interface QuestionFilterControlsProps {
  // Question counts
  totalQuestionsCount: number;
  unansweredQuestionsCount: number;
  filteredQuestionsCount: number;
  prunedQuestionsCount?: number;

  // Filter state
  answeredFilter: 'all' | 'answered' | 'unanswered';
  onAnsweredFilterChange: (value: 'all' | 'answered' | 'unanswered') => void;

  sectionFilter: string; // 'all' or section id
  onSectionFilterChange: (value: string) => void;

  availableSections: Array<{ id: string; title: string }>;

  // Agent pruning state
  agentPruningEnabled: boolean;
  onAgentPruningToggle: (enabled: boolean) => void;
  onRefreshQuestions: () => void;

  agentStatus: 'not_requested' | 'analyzing' | 'completed' | 'fallback' | null;
  isRefreshing?: boolean;

  className?: string;
}

export const QuestionFilterControls: React.FC<QuestionFilterControlsProps> = ({
  totalQuestionsCount,
  unansweredQuestionsCount,
  filteredQuestionsCount,
  prunedQuestionsCount,
  answeredFilter,
  onAnsweredFilterChange,
  sectionFilter,
  onSectionFilterChange,
  availableSections,
  agentPruningEnabled,
  onAgentPruningToggle,
  onRefreshQuestions,
  agentStatus,
  isRefreshing = false,
  className
}) => {
  const getAgentStatusDisplay = () => {
    if (!agentStatus || agentStatus === 'not_requested') return null;

    if (agentStatus === 'analyzing') {
      return (
        <div
          className="flex items-center gap-2 text-sm text-blue-600"
          data-testid="agent-analysis-indicator"
        >
          <RefreshCw className="h-4 w-4 animate-spin" />
          Agent analyzing questions...
        </div>
      );
    }

    if (agentStatus === 'completed') {
      return (
        <div
          className="flex items-center gap-2 text-sm text-green-600"
          data-testid="agent-pruning-complete"
        >
          <CheckCircle className="h-4 w-4" />
          Analysis complete
          {prunedQuestionsCount !== undefined && prunedQuestionsCount > 0 && (
            <Badge variant="outline" className="ml-1" data-testid="pruned-questions-count">
              {prunedQuestionsCount} questions pruned
            </Badge>
          )}
        </div>
      );
    }

    if (agentStatus === 'fallback') {
      return (
        <div
          className="flex items-center gap-2 text-sm text-amber-600"
          data-testid="agent-fallback-message"
        >
          <AlertCircle className="h-4 w-4" />
          Agent analysis timed out - showing all questions
        </div>
      );
    }

    return null;
  };

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Question Filters</span>
          <div className="flex items-center gap-4">
            <Badge variant="outline" data-testid="total-questions-count">
              {totalQuestionsCount} total
            </Badge>
            <Badge variant="outline" className="text-amber-600" data-testid="unanswered-questions-count">
              {unansweredQuestionsCount} unanswered
            </Badge>
            {filteredQuestionsCount !== totalQuestionsCount && (
              <Badge variant="outline" className="text-blue-600" data-testid="filtered-questions-count">
                {filteredQuestionsCount} shown
              </Badge>
            )}
          </div>
        </CardTitle>
        <CardDescription>
          Filter questions and use AI to identify most relevant ones
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filter Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Answered Filter */}
          <div className="space-y-2">
            <Label htmlFor="answered-filter">Show Questions</Label>
            <Select
              value={answeredFilter}
              onValueChange={(value) => onAnsweredFilterChange(value as 'all' | 'answered' | 'unanswered')}
            >
              <SelectTrigger id="answered-filter" data-testid="answered-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Questions</SelectItem>
                <SelectItem value="unanswered">Unanswered Only</SelectItem>
                <SelectItem value="answered">Answered Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Section Filter */}
          <div className="space-y-2">
            <Label htmlFor="section-filter">Filter by Section</Label>
            <Select
              value={sectionFilter}
              onValueChange={onSectionFilterChange}
            >
              <SelectTrigger id="section-filter" data-testid="section-filter">
                <SelectValue placeholder="Select section" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sections</SelectItem>
                {availableSections.map((section) => (
                  <SelectItem key={section.id} value={section.id}>
                    {section.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Agent Pruning Controls */}
        <div className="pt-3 border-t space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600" />
              <Label htmlFor="agent-pruning" className="font-medium">
                AI Question Pruning
              </Label>
            </div>
            <Switch
              id="agent-pruning"
              checked={agentPruningEnabled}
              onCheckedChange={onAgentPruningToggle}
              data-testid="agent-pruning-toggle"
            />
          </div>

          {agentPruningEnabled && (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">
                Uses AI to identify and show only the most relevant questions for this asset type
              </p>

              <Button
                variant="outline"
                size="sm"
                onClick={onRefreshQuestions}
                disabled={isRefreshing || agentStatus === 'analyzing'}
                className="w-full"
                data-testid="refresh-questions-button"
              >
                {isRefreshing || agentStatus === 'analyzing' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh Questions with AI
                  </>
                )}
              </Button>

              {getAgentStatusDisplay()}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
