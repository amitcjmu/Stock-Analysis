import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Download, CheckCircle, FileText, RefreshCw } from 'lucide-react';
import { ReadinessAssessment, SignoffPackage } from '../types';
import { getReadinessColor, getRiskColor, getRiskBadgeVariant } from '../utils';

interface ReadinessTabsProps {
  assessment: ReadinessAssessment & {
    readiness_breakdown?: Array<{
      category: string;
      score: number;
      status: string;
    }>;
    risk_assessment?: {
      overall_risk: string;
      risk_factors: Array<{
        id: string;
        title: string;
        description: string;
        impact: string;
        likelihood: string;
        risk_level: string;
        recommended_action: string;
      }>;
    };
    critical_gaps?: Array<{
      id: string;
      title: string;
      description: string;
      priority: 'high' | 'medium' | 'low';
      status: 'pending' | 'in-progress' | 'completed';
      category: string;
      estimated_effort: string;
      impact: string;
    }>;
  };
  signoffPackage: SignoffPackage | null;
  activeTab: string;
  onTabChange: (tab: string) => void;
  isReadyForSignoff: boolean;
  isGeneratingSignoff: boolean;
  isSubmittingApproval: boolean;
  onGenerateSignoff: () => void;
  onDownloadSignoff: () => void;
  onSubmitForApproval: () => void;
  children?: React.ReactNode;
}

export const ReadinessTabs = ({
  assessment,
  signoffPackage,
  activeTab,
  onTabChange,
  isReadyForSignoff,
  isGeneratingSignoff,
  isSubmittingApproval,
  onGenerateSignoff,
  onDownloadSignoff,
  onSubmitForApproval,
  children,
}: ReadinessTabsProps) => {
  return (
    <Tabs value={activeTab} onValueChange={onTabChange} className="space-y-4">
      <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="breakdown">Readiness Breakdown</TabsTrigger>
        <TabsTrigger value="risks">Risk Assessment</TabsTrigger>
        <TabsTrigger value="actions">Recommended Actions</TabsTrigger>
        <TabsTrigger value="signoff">Signoff</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium mb-4">Assessment Summary</h3>
            <p className="text-gray-600 mb-4">
              {assessment.overall_readiness.recommended_action}
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div>
                <h4 className="font-medium mb-2">Key Strengths</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  {assessment.workflow_progression?.workflow_recommendations
                    ?.slice(0, 3)
                    .map((item, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span>{item}</span>
                      </li>
                    )) || (
                      <li className="text-gray-400 italic">No workflow recommendations available</li>
                    )}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Critical Gaps</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  {assessment.overall_readiness.critical_gaps.length > 0 ? (
                    assessment.overall_readiness.critical_gaps
                      .slice(0, 3)
                      .map((item, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-red-500 mr-2">!</span>
                          <span>{item}</span>
                        </li>
                      ))
                  ) : (
                    <li className="text-gray-400 italic">No critical gaps identified</li>
                  )}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {children}
      </TabsContent>

      <TabsContent value="breakdown">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium mb-4">Readiness Breakdown</h3>
            <div className="space-y-6">
              {Object.entries(assessment.readiness_breakdown).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <h4 className="font-medium capitalize">
                    {key.replace('_', ' ')}
                    <span className="ml-2 text-sm text-gray-500">
                      ({Math.round(value.score * 100)}%)
                    </span>
                  </h4>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getReadinessColor(value.score)}`}
                      style={{ width: `${value.score * 100}%` }}
                    />
                  </div>
                  
                  {value.gaps && value.gaps.length > 0 && (
                    <div className="mt-2 text-sm text-gray-600">
                      <p className="font-medium">Areas for Improvement:</p>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        {value.gaps!.slice(0, 3).map((gap: string, i: number) => (
                          <li key={i}>{gap}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="risks">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium mb-4">Risk Assessment</h3>
            {assessment.risk_assessment ? (
              <div className="space-y-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium">Overall Risk Level</h4>
                    <Badge variant={getRiskBadgeVariant(assessment.risk_assessment.overall_risk)}>
                      {assessment.risk_assessment.overall_risk}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">
                    {assessment.risk_assessment.overall_risk.toLowerCase() === 'low' 
                      ? 'Your migration path has a low overall risk profile.' 
                      : assessment.risk_assessment.overall_risk.toLowerCase() === 'medium'
                      ? 'Your migration path has a moderate overall risk profile.'
                      : 'Your migration path has a high overall risk profile.'}
                  </p>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">Key Risk Factors</h4>
                  <div className="space-y-3">
                    {assessment.risk_assessment.risk_factors.map((risk) => (
                      <Card key={risk.id} className="border-l-4 border-yellow-400">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <h5 className="font-medium">{risk.title}</h5>
                              <p className="text-sm text-gray-600">{risk.description}</p>
                            </div>
                            <Badge 
                              variant={getRiskBadgeVariant(risk.risk_level)}
                              className="ml-2"
                            >
                              {risk.risk_level}
                            </Badge>
                          </div>
                          
                          <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">Impact:</span>{' '}
                              <span className="font-medium">{risk.impact}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Likelihood:</span>{' '}
                              <span className="font-medium">{risk.likelihood}</span>
                            </div>
                          </div>
                          
                          <div className="mt-3 text-sm">
                            <span className="text-gray-500">Recommended Action:</span>{' '}
                            <span className="font-medium">{risk.recommended_action}</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No risk assessment data available.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="actions">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium mb-4">Recommended Actions</h3>
            <div className="space-y-4">
              {assessment.recommendations.map((action) => (
                <div key={action.id} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium">{action.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                    </div>
                    <Badge 
                      variant={action.priority === 'high' ? 'destructive' : 
                              action.priority === 'medium' ? 'secondary' : 'outline'}
                      className="ml-2"
                    >
                      {action.priority}
                    </Badge>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
                    <span>Effort: {action.estimated_effort}</span>
                    <span>Impact: {action.impact}</span>
                    <span className="bg-gray-100 px-2 py-1 rounded">{action.category}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="signoff">
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Signoff & Approval</h3>
              <div className="flex items-center space-x-2">
                <Button size="sm" onClick={onGenerateSignoff} disabled={!isReadyForSignoff}>
                  Generate Signoff Package
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={onDownloadSignoff}
                  disabled={!signoffPackage}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>

            {signoffPackage ? (
              <div className="space-y-6">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                    Signoff Package Generated
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Generated on {new Date(signoffPackage.signoff_metadata.package_generated).toLocaleDateString()}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-2">Executive Summary</h4>
                    <div className="space-y-2 text-sm">
                      <p>{signoffPackage.executive_summary.assessment_readiness_status}</p>
                      <p>
                        {signoffPackage.executive_summary.applications_ready_for_assessment} of {signoffPackage.executive_summary.total_applications} applications are ready for assessment.
                      </p>
                      <p>Business Confidence: {signoffPackage.signoff_metadata.assessment_confidence * 100}%</p>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Approval Status</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Approval Progress</span>
                        <span className="text-sm font-medium">
                          {signoffPackage.signoff_metadata.stakeholder_input_level * 100}%
                        </span>
                      </div>
                      <Progress 
                        value={signoffPackage.signoff_metadata.stakeholder_input_level * 100} 
                        className="h-2" 
                      />
                      
                      <div className="mt-4">
                        <Button 
                          className="w-full" 
                          onClick={onSubmitForApproval}
                          disabled={isSubmittingApproval}
                        >
                          {isSubmittingApproval ? (
                            <>
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                              Submitting...
                            </>
                          ) : (
                            'Submit for Approval'
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 mx-auto text-gray-400" />
                <h4 className="mt-2 font-medium">No Signoff Package Generated</h4>
                <p className="text-sm text-gray-500 mt-1">
                  Generate a signoff package to proceed with the approval process.
                </p>
                <Button 
                  className="mt-4" 
                  onClick={onGenerateSignoff}
                  disabled={!isReadyForSignoff}
                >
                  Generate Signoff Package
                </Button>
                
                {!isReadyForSignoff && (
                  <p className="text-xs text-orange-600 mt-2">
                    Complete all required readiness checks before generating the signoff package.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
};
