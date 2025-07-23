import React from 'react'
import type { useState } from 'react'
import { useEffect } from 'react'
import type { useParams } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import type { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ArchitectureStandardsForm } from '@/components/assessment/ArchitectureStandardsForm';
import { TemplateSelector } from '@/components/assessment/TemplateSelector';
import { ApplicationOverrides } from '@/components/assessment/ApplicationOverrides';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Save, ArrowRight } from 'lucide-react';

const ArchitecturePage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const {
    state,
    updateArchitectureStandards,
    resumeFlow
  } = useAssessmentFlow(flowId);
  
  const [standards, setStandards] = useState(state.engagementStandards);
  const [overrides, setOverrides] = useState(state.applicationOverrides);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDraft, setIsDraft] = useState(false);
  
  // Update local state when flow state changes
  useEffect(() => {
    setStandards(state.engagementStandards);
    setOverrides(state.applicationOverrides);
  }, [state.engagementStandards, state.applicationOverrides]);
  
  const handleSaveDraft = async () => {
    setIsDraft(true);
    try {
      await updateArchitectureStandards(standards, overrides);
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsDraft(false);
    }
  };
  
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await updateArchitectureStandards(standards, overrides);
      await resumeFlow({ standards, overrides });
    } catch (error) {
      console.error('Failed to submit architecture standards:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const hasChanges = () => {
    return JSON.stringify(standards) !== JSON.stringify(state.engagementStandards) ||
           JSON.stringify(overrides) !== JSON.stringify(state.applicationOverrides);
  };
  
  return (
    <SidebarProvider>
      <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Architecture Standards
          </h1>
          <p className="text-gray-600">
            Define engagement-level architecture minimums and application-specific exceptions
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
            <p className="text-sm text-blue-600">
              AI agents are analyzing your architecture standards...
            </p>
          </div>
        )}
        
        {/* Template Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Template Selection</CardTitle>
            <CardDescription>
              Start with a pre-defined template or create custom standards
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TemplateSelector 
              onTemplateSelect={(template) => setStandards(template.standards)}
            />
          </CardContent>
        </Card>
        
        {/* Architecture Standards Form */}
        <Card>
          <CardHeader>
            <CardTitle>Engagement-Level Standards</CardTitle>
            <CardDescription>
              Define the minimum architecture requirements for all applications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ArchitectureStandardsForm
              standards={standards}
              onChange={setStandards}
            />
          </CardContent>
        </Card>
        
        {/* Application Overrides */}
        <Card>
          <CardHeader>
            <CardTitle>Application-Specific Overrides</CardTitle>
            <CardDescription>
              Define exceptions for specific applications that cannot meet the engagement standards
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ApplicationOverrides
              applications={state.selectedApplicationIds}
              overrides={overrides}
              onChange={setOverrides}
            />
          </CardContent>
        </Card>
        
        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {hasChanges() && (
              <Button 
                variant="outline" 
                onClick={handleSaveDraft}
                disabled={isDraft}
              >
                <Save className="h-4 w-4 mr-2" />
                {isDraft ? 'Saving...' : 'Save Draft'}
              </Button>
            )}
          </div>
          
          <Button 
            onClick={handleSubmit}
            disabled={isSubmitting || state.isLoading}
            size="lg"
          >
            {isSubmitting ? (
              'Processing...'
            ) : (
              <>
                Continue to Tech Debt Analysis
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
      </AssessmentFlowLayout>
    </SidebarProvider>
  );
};


export default ArchitecturePage;