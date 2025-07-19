import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

// Import existing collection components
import { DataIntegrationView } from '@/components/collection/DataIntegrationView';
import { ConflictResolver } from '@/components/collection/components/ConflictResolver';
import { ValidationDisplay } from '@/components/collection/ValidationDisplay';
import { ProgressTracker } from '@/components/collection/ProgressTracker';

// Import types
import type { 
  DataConflict, 
  ConflictResolution, 
  FormValidationResult,
  ProgressMilestone 
} from '@/components/collection/types';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

/**
 * Data Integration page
 * Handles conflict resolution and data validation from multiple sources
 */
const DataIntegration: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State management
  const [conflicts, setConflicts] = useState<DataConflict[]>([]);
  const [validation, setValidation] = useState<FormValidationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [resolvedConflicts, setResolvedConflicts] = useState<string[]>([]);

  // Mock data - in real implementation this would come from API
  useEffect(() => {
    const mockConflicts: DataConflict[] = [
      {
        id: 'conflict-1',
        attributeName: 'application_type',
        attributeLabel: 'Application Type',
        conflictingValues: [
          {
            value: 'web',
            source: 'automated',
            sourceId: 'scanner-001',
            confidenceScore: 0.85,
            collectedAt: '2025-07-19T10:30:00Z'
          },
          {
            value: 'desktop',
            source: 'manual',
            sourceId: 'form-001',
            confidenceScore: 0.95,
            collectedAt: '2025-07-19T11:45:00Z'
          }
        ],
        recommendedResolution: 'desktop',
        requiresUserReview: true
      },
      {
        id: 'conflict-2',
        attributeName: 'technology_stack',
        attributeLabel: 'Technology Stack',
        conflictingValues: [
          {
            value: ['Java', 'Spring'],
            source: 'automated',
            sourceId: 'scanner-002',
            confidenceScore: 0.78,
            collectedAt: '2025-07-19T10:30:00Z'
          },
          {
            value: ['Java', 'Spring Boot', 'MySQL'],
            source: 'manual',
            sourceId: 'form-002',
            confidenceScore: 0.92,
            collectedAt: '2025-07-19T12:00:00Z'
          },
          {
            value: ['Java 11', 'Spring Boot 2.5'],
            source: 'bulk',
            sourceId: 'upload-001',
            confidenceScore: 0.88,
            collectedAt: '2025-07-19T12:30:00Z'
          }
        ],
        recommendedResolution: 'Java, Spring Boot, MySQL',
        requiresUserReview: false
      },
      {
        id: 'conflict-3',
        attributeName: 'business_criticality',
        attributeLabel: 'Business Criticality',
        conflictingValues: [
          {
            value: 'high',
            source: 'manual',
            sourceId: 'form-003',
            confidenceScore: 0.95,
            collectedAt: '2025-07-19T11:00:00Z'
          },
          {
            value: 'medium',
            source: 'template',
            sourceId: 'template-001',
            confidenceScore: 0.70,
            collectedAt: '2025-07-19T10:45:00Z'
          }
        ],
        recommendedResolution: 'high',
        requiresUserReview: true
      }
    ];

    const mockValidation: FormValidationResult = {
      formId: 'data-integration',
      isValid: false,
      overallConfidenceScore: 0.87,
      completionPercentage: 73,
      fieldResults: {},
      crossFieldErrors: [
        {
          fieldId: 'application_type',
          fieldLabel: 'Application Type',
          errorCode: 'CONFLICTING_VALUES',
          errorMessage: 'Multiple conflicting values detected from different sources',
          severity: 'warning'
        }
      ],
      businessRuleViolations: []
    };

    setTimeout(() => {
      setConflicts(mockConflicts);
      setValidation(mockValidation);
      setIsLoading(false);
    }, 1000);
  }, []);

  // Progress milestones
  const progressMilestones: ProgressMilestone[] = [
    {
      id: 'data-loaded',
      title: 'Data Sources Loaded',
      description: 'All data sources have been loaded and analyzed',
      achieved: !isLoading,
      achievedAt: !isLoading ? new Date().toISOString() : undefined,
      weight: 0.2,
      required: true
    },
    {
      id: 'conflicts-identified',
      title: 'Conflicts Identified',
      description: 'Data conflicts have been identified and categorized',
      achieved: conflicts.length > 0,
      weight: 0.3,
      required: true
    },
    {
      id: 'conflicts-resolved',
      title: 'Conflicts Resolved',
      description: 'All data conflicts have been resolved',
      achieved: resolvedConflicts.length === conflicts.length && conflicts.length > 0,
      weight: 0.3,
      required: true
    },
    {
      id: 'validation-passed',
      title: 'Final Validation',
      description: 'All data has passed final validation checks',
      achieved: validation?.isValid || false,
      weight: 0.2,
      required: true
    }
  ];

  const handleConflictResolve = (conflictId: string, resolution: ConflictResolution) => {
    setResolvedConflicts(prev => [...prev, conflictId]);
    
    // Update conflicts list
    setConflicts(prev => prev.filter(c => c.id !== conflictId));

    toast({
      title: 'Conflict Resolved',
      description: `Selected ${resolution.selectedValue} from ${resolution.selectedSource} source.`
    });

    // Check if all conflicts are resolved
    if (resolvedConflicts.length + 1 === conflicts.length) {
      // Update validation to mark as valid
      setValidation(prev => prev ? { ...prev, isValid: true } : null);
      
      toast({
        title: 'All Conflicts Resolved',
        description: 'Data integration is complete. Ready to proceed to discovery phase.'
      });
    }
  };

  const handleRefreshData = async () => {
    setIsLoading(true);
    try {
      // Simulate API call to refresh data
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: 'Data Refreshed',
        description: 'Latest data has been loaded from all sources.'
      });
    } catch (error) {
      toast({
        title: 'Refresh Failed',
        description: 'Failed to refresh data. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleProceedToDiscovery = async () => {
    if (!validation?.isValid) {
      toast({
        title: 'Validation Required',
        description: 'Please resolve all conflicts before proceeding.',
        variant: 'destructive'
      });
      return;
    }

    setIsProcessing(true);
    try {
      // Simulate handoff to discovery phase
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: 'Handoff Successful',
        description: 'Data has been successfully transferred to discovery phase.'
      });

      navigate('/discovery?source=collection&integrated=true');
    } catch (error) {
      toast({
        title: 'Handoff Failed',
        description: 'Failed to transfer data to discovery phase.',
        variant: 'destructive'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const getConflictStatusCounts = () => {
    const total = conflicts.length + resolvedConflicts.length;
    const resolved = resolvedConflicts.length;
    const pending = conflicts.length;
    const highPriority = conflicts.filter(c => c.requiresUserReview).length;

    return { total, resolved, pending, highPriority };
  };

  const statusCounts = getConflictStatusCounts();
  const overallProgress = statusCounts.total > 0 ? (statusCounts.resolved / statusCounts.total) * 100 : 0;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => navigate('/collection')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Collection
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Data Integration & Validation</h1>
            <p className="text-muted-foreground">
              Resolve conflicts and validate data from multiple collection sources
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            onClick={handleRefreshData}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Data
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Conflicts</p>
                <p className="text-2xl font-bold">{statusCounts.total}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Resolved</p>
                <p className="text-2xl font-bold text-green-600">{statusCounts.resolved}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold text-orange-600">{statusCounts.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">High Priority</p>
                <p className="text-2xl font-bold text-red-600">{statusCounts.highPriority}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Progress Tracker Sidebar */}
        <div className="lg:col-span-1">
          <ProgressTracker
            formId="data-integration"
            totalSections={4}
            completedSections={progressMilestones.filter(m => m.achieved).length}
            overallCompletion={overallProgress}
            confidenceScore={validation?.overallConfidenceScore || 0}
            milestones={progressMilestones}
            timeSpent={0}
            estimatedTimeRemaining={statusCounts.pending * 120000} // 2 min per conflict
          />
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Validation Display */}
          {validation && (
            <ValidationDisplay 
              validation={validation}
              showWarnings={true}
              onErrorClick={(fieldId) => {
                console.log('Navigate to conflict:', fieldId);
              }}
            />
          )}

          {/* Main Content Tabs */}
          <Tabs defaultValue="conflicts" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="conflicts" className="relative">
                Conflict Resolution
                {statusCounts.pending > 0 && (
                  <Badge variant="destructive" className="ml-2 text-xs">
                    {statusCounts.pending}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="overview">Data Overview</TabsTrigger>
            </TabsList>

            <TabsContent value="conflicts" className="space-y-6">
              {isLoading ? (
                <Card>
                  <CardContent className="p-8">
                    <div className="flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                        <p className="text-muted-foreground">Loading data conflicts...</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : conflicts.length > 0 ? (
                <ConflictResolver
                  conflicts={conflicts}
                  onResolve={handleConflictResolve}
                />
              ) : (
                <Card>
                  <CardContent className="p-8">
                    <div className="text-center">
                      <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">All Conflicts Resolved</h3>
                      <p className="text-muted-foreground">
                        Great! All data conflicts have been resolved. You can now proceed to the discovery phase.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="overview" className="space-y-6">
              <DataIntegrationView />
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/collection')}
            >
              Save and Return
            </Button>
            <Button 
              onClick={handleProceedToDiscovery}
              disabled={!validation?.isValid || isProcessing}
            >
              {isProcessing ? 'Processing...' : 'Proceed to Discovery Phase'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataIntegration;