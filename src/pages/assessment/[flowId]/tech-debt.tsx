import React from 'react'
import { useState } from 'react'
import { useEffect, useMemo } from 'react'
import type { GetServerSideProps } from 'next/router';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ComponentIdentificationPanel } from '@/components/assessment/ComponentIdentificationPanel';
import { TechDebtAnalysisGrid } from '@/components/assessment/TechDebtAnalysisGrid';
import { SeverityFilter } from '@/components/assessment/SeverityFilter';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { RealTimeProgressIndicator } from '@/components/assessment/RealTimeProgressIndicator';
import { UserModificationForm } from '@/components/assessment/UserModificationForm';
import type { TechDebtItem, ApplicationComponent } from '@/hooks/useAssessmentFlow';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Save, ArrowRight, Loader2, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TechDebtPageProps {
  flowId: string;
}

type SeverityLevel = 'critical' | 'high' | 'medium' | 'low';

const TechDebtPage: React.FC<TechDebtPageProps> = ({ flowId }) => {
  const {
    state,
    updateApplicationComponents,
    updateTechDebtAnalysis,
    resumeFlow
  } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<SeverityLevel | 'all'>('all');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDraft, setIsDraft] = useState(false);
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [editingTechDebt, setEditingTechDebt] = useState<string | null>(null);

  // Set first application as selected by default
  useEffect(() => {
    if (state.selectedApplicationIds.length > 0 && !selectedApp) {
      setSelectedApp(state.selectedApplicationIds[0]);
    }
  }, [state.selectedApplicationIds, selectedApp]);

  // Get current application data
  const currentAppComponents = selectedApp ? state.applicationComponents[selectedApp] || [] : [];
  const currentAppTechDebt = selectedApp ? state.techDebtAnalysis[selectedApp] || [] : [];

  // Filter tech debt by severity
  const filteredTechDebt = useMemo(() => {
    if (severityFilter === 'all') return currentAppTechDebt;
    return currentAppTechDebt.filter(item => item.severity === severityFilter);
  }, [currentAppTechDebt, severityFilter]);

  // Calculate statistics
  const techDebtStats = useMemo(() => {
    const stats = {
      total: currentAppTechDebt.length,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      totalEffort: 0,
      avgTechDebtScore: 0
    };

    currentAppTechDebt.forEach(item => {
      stats[item.severity]++;
      stats.totalEffort += item.remediation_effort_hours || 0;
    });

    const totalScore = currentAppTechDebt.reduce((sum, item) => sum + (item.tech_debt_score || 0), 0);
    stats.avgTechDebtScore = stats.total > 0 ? totalScore / stats.total : 0;

    return stats;
  }, [currentAppTechDebt]);

  const handleSaveDraft = async (): void => {
    if (!selectedApp) return;

    setIsDraft(true);
    try {
      await updateApplicationComponents(selectedApp, currentAppComponents);
      await updateTechDebtAnalysis(selectedApp, currentAppTechDebt);
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsDraft(false);
    }
  };

  const handleSubmit = async (): void => {
    setIsSubmitting(true);
    try {
      // Save all application data
      for (const appId of state.selectedApplicationIds) {
        const components = state.applicationComponents[appId] || [];
        const techDebt = state.techDebtAnalysis[appId] || [];

        await updateApplicationComponents(appId, components);
        await updateTechDebtAnalysis(appId, techDebt);
      }

      await resumeFlow({
        components: state.applicationComponents,
        techDebtAnalysis: state.techDebtAnalysis
      });
    } catch (error) {
      console.error('Failed to submit tech debt analysis:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateComponents = (components: ApplicationComponent[]): void => {
    if (!selectedApp) return;
    updateApplicationComponents(selectedApp, components);
  };

  const updateTechDebt = (techDebt: TechDebtItem[]): void => {
    if (!selectedApp) return;
    updateTechDebtAnalysis(selectedApp, techDebt);
  };

  const getSeverityColor = (severity: SeverityLevel): any => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  if (state.selectedApplicationIds.length === 0) {
    return (
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 text-center">
          <AlertCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Applications Selected</h2>
          <p className="text-gray-600">Please return to the previous step to select applications for analysis.</p>
        </div>
      </AssessmentFlowLayout>
    );
  }

  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Technical Debt Analysis
          </h1>
          <p className="text-gray-600">
            Review component identification and technical debt analysis for selected applications
          </p>
        </div>

        {/* Status Alert */}
        {state.status === 'error' && (
          <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-600">{state.error}</p>
          </div>
        )}

        {state.status === 'processing' && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
              <p className="text-sm text-blue-600">
                AI agents are analyzing technical debt and component architecture...
              </p>
            </div>
          </div>
        )}

        {/* Real-time Progress */}
        {state.status === 'processing' && (
          <RealTimeProgressIndicator
            agentUpdates={state.agentUpdates}
            currentPhase="tech_debt_analysis"
          />
        )}

        {/* Application Selection */}
        <ApplicationTabs
          applications={state.selectedApplicationIds}
          selectedApp={selectedApp}
          onAppSelect={setSelectedApp}
          getApplicationName={(appId) => appId} // In real implementation, get from application data
        />

        {selectedApp && (
          <>
            {/* Tech Debt Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>Technical Debt Overview</span>
                </CardTitle>
                <CardDescription>
                  Summary statistics for {selectedApp}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{techDebtStats.total}</div>
                    <div className="text-sm text-gray-600">Total Issues</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{techDebtStats.critical}</div>
                    <div className="text-sm text-gray-600">Critical</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{techDebtStats.high}</div>
                    <div className="text-sm text-gray-600">High</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{techDebtStats.medium}</div>
                    <div className="text-sm text-gray-600">Medium</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{techDebtStats.low}</div>
                    <div className="text-sm text-gray-600">Low</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Math.round(techDebtStats.avgTechDebtScore)}
                    </div>
                    <div className="text-sm text-gray-600">Avg Score</div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total Remediation Effort:</span>
                    <span className="font-semibold">{techDebtStats.totalEffort} hours</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Main Content Tabs */}
            <Tabs defaultValue="components" className="space-y-4">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="components">
                  Component Identification ({currentAppComponents.length})
                </TabsTrigger>
                <TabsTrigger value="tech-debt">
                  Technical Debt ({currentAppTechDebt.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="components" className="space-y-4">
                <ComponentIdentificationPanel
                  components={currentAppComponents}
                  onComponentsChange={updateComponents}
                  editingComponent={editingComponent}
                  onEditComponent={setEditingComponent}
                />
              </TabsContent>

              <TabsContent value="tech-debt" className="space-y-4">
                {/* Severity Filter */}
                <SeverityFilter
                  selectedSeverity={severityFilter}
                  onSeverityChange={setSeverityFilter}
                  counts={{
                    all: techDebtStats.total,
                    critical: techDebtStats.critical,
                    high: techDebtStats.high,
                    medium: techDebtStats.medium,
                    low: techDebtStats.low
                  }}
                />

                {/* Tech Debt Grid */}
                <TechDebtAnalysisGrid
                  techDebtItems={filteredTechDebt}
                  onTechDebtChange={updateTechDebt}
                  editingItem={editingTechDebt}
                  onEditItem={setEditingTechDebt}
                />
              </TabsContent>
            </Tabs>

            {/* User Modifications */}
            {(editingComponent || editingTechDebt) && (
              <UserModificationForm
                type={editingComponent ? 'component' : 'tech-debt'}
                item={editingComponent ?
                  currentAppComponents.find(c => c.component_name === editingComponent) :
                  currentAppTechDebt.find(t => t.category === editingTechDebt)
                }
                onSave={(updatedItem) => {
                  if (editingComponent) {
                    const updatedComponents = currentAppComponents.map(c =>
                      c.component_name === editingComponent ? updatedItem : c
                    );
                    updateComponents(updatedComponents);
                    setEditingComponent(null);
                  } else {
                    const updatedTechDebt = currentAppTechDebt.map(t =>
                      t.category === editingTechDebt ? updatedItem : t
                    );
                    updateTechDebt(updatedTechDebt);
                    setEditingTechDebt(null);
                  }
                }}
                onCancel={() => {
                  setEditingComponent(null);
                  setEditingTechDebt(null);
                }}
              />
            )}
          </>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={handleSaveDraft}
              disabled={isDraft || !selectedApp}
            >
              <Save className="h-4 w-4 mr-2" />
              {isDraft ? 'Saving...' : 'Save Progress'}
            </Button>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || state.isLoading}
            size="lg"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Continue to 6R Strategy Review
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </AssessmentFlowLayout>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  return {
    props: {
      flowId: context.params?.flowId as string
    }
  };
};

export default TechDebtPage;
