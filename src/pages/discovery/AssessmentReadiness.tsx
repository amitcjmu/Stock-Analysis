import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Users, 
  FileText,
  RefreshCw,
  Eye,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Target,
  TrendingUp,
  Database,
  Network,
  Shield,
  Briefcase,
  ArrowRight,
  Calendar,
  Star,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';
import { apiCall, API_CONFIG } from '@/config/api';

interface ReadinessAssessment {
  overall_readiness: {
    readiness_score: number;
    readiness_state: string;
    readiness_color: string;
    recommended_action: string;
    critical_gaps: string[];
    recommended_timeline: string;
    confidence_level: number;
  };
  readiness_breakdown: {
    data_discovery: {
      discovery_readiness_score: number;
      asset_inventory_completeness: number;
      application_identification_completeness: number;
      dependency_mapping_completeness: number;
      data_quality_score: number;
      discovery_gaps: string[];
      discovery_recommendations: string[];
    };
    business_context: {
      business_context_score: number;
      stakeholder_input_completeness: number;
      business_criticality_mapping: number;
      risk_tolerance_clarity: number;
      migration_timeline_clarity: number;
      business_gaps: string[];
      stakeholder_engagement_recommendations: string[];
    };
    technical_analysis: {
      technical_analysis_score: number;
      tech_debt_assessment_completeness: number;
      application_complexity_completeness: number;
      infrastructure_analysis_completeness: number;
      security_assessment_completeness: number;
      technical_gaps: string[];
      technical_analysis_recommendations: string[];
    };
    workflow_progression: {
      workflow_progression_score: number;
      discovery_phase_completion: number;
      mapping_phase_completion: number;
      cleanup_phase_completion: number;
      validation_phase_completion: number;
      workflow_gaps: string[];
      workflow_acceleration_recommendations: string[];
    };
  };
  application_readiness: Array<{
    application_id: string;
    application_name: string;
    readiness_score: number;
    readiness_level: string;
    readiness_factors: any;
    blocking_issues: string[];
    assessment_priority: number;
  }>;
  prioritized_applications: Array<{
    application_id: string;
    application_name: string;
    readiness_score: number;
    assessment_priority_score: number;
    priority_justification: string;
    recommended_assessment_order: number;
    assessment_complexity: string;
    stakeholder_attention_required: string;
  }>;
  assessment_preparation: string[];
  outstanding_questions: Array<{
    question: string;
    assessment_impact_score: number;
    phase: string;
  }>;
  handoff_metadata: {
    assessment_readiness_score: number;
    applications_ready_for_assessment: number;
    critical_gaps: string[];
    recommended_timeline: string;
    assessment_timestamp: string;
  };
}

interface SignoffPackage {
  executive_summary: {
    assessment_readiness_status: string;
    applications_ready_for_assessment: number;
    total_applications: number;
    key_achievements: string[];
    remaining_gaps: string[];
    business_confidence: number;
  };
  validation_checkpoints: Array<{
    checkpoint: string;
    status: string;
    confidence: number;
  }>;
  assessment_risk_evaluation: {
    risk_level: string;
    risk_factors: string[];
  };
  recommended_actions: string[];
  stakeholder_decisions_required: string[];
  success_criteria: string[];
  signoff_metadata: {
    package_generated: string;
    assessment_confidence: number;
    stakeholder_input_level: number;
    recommended_signoff_date: string;
  };
}

const AssessmentReadiness: React.FC = () => {
  const [readinessAssessment, setReadinessAssessment] = useState<ReadinessAssessment | null>(null);
  const [signoffPackage, setSignoffPackage] = useState<SignoffPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [signoffDecision, setSignoffDecision] = useState<string>('');
  const [stakeholderConcerns, setStakeholderConcerns] = useState<string>('');
  const [isSubmittingSignoff, setIsSubmittingSignoff] = useState(false);

  useEffect(() => {
    fetchAssessmentReadiness();
  }, []);

  const fetchAssessmentReadiness = async () => {
    try {
      setLoading(true);
      setError(null);

      // First, get sample portfolio data - in real implementation this would come from the backend
      const portfolioData = {
        assets: [], // Would be populated from actual asset data
        applications: [], // Would be populated from application discovery
        dependencies: [] // Would be populated from dependency analysis
      };

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSESSMENT_READINESS, {
        method: 'POST',
        body: JSON.stringify({
          portfolio_data: portfolioData,
          stakeholder_context: {
            business_priorities: ["cost_optimization", "security_improvement"],
            risk_tolerance: "medium",
            timeline_constraints: "12_months"
          },
          assessment_type: "comprehensive"
        })
      });

      setReadinessAssessment(response.readiness_assessment);
      
      // Generate signoff package if readiness is sufficient
      if (response.readiness_assessment.overall_readiness.readiness_score >= 0.6) {
        await generateSignoffPackage(response.readiness_assessment);
      }

    } catch (err) {
      console.error('Failed to fetch assessment readiness:', err);
      setError('Failed to load assessment readiness data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateSignoffPackage = async (assessment: ReadinessAssessment) => {
    try {
      const signoffResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.STAKEHOLDER_SIGNOFF_PACKAGE, {
        method: 'POST',
        body: JSON.stringify({
          readiness_assessment: assessment,
          stakeholder_context: {
            business_priorities: ["cost_optimization", "security_improvement"],
            risk_tolerance: "medium"
          },
          package_type: "comprehensive"
        })
      });

      setSignoffPackage(signoffResponse.signoff_package);

    } catch (err) {
      console.error('Failed to generate signoff package:', err);
    }
  };

  const handleSignoffSubmission = async () => {
    if (!signoffDecision) {
      alert('Please select a signoff decision');
      return;
    }

    try {
      setIsSubmittingSignoff(true);

      const feedbackData = {
        feedback_type: "readiness_validation",
        signoff_decision: signoffDecision,
        stakeholder_concerns: stakeholderConcerns.split('\n').filter(concern => concern.trim()),
        additional_requirements: [],
        signoff_metadata: {
          signoff_timestamp: new Date().toISOString(),
          stakeholder_id: "current_user"
        }
      };

      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.STAKEHOLDER_SIGNOFF_FEEDBACK, {
        method: 'POST',
        body: JSON.stringify(feedbackData)
      });

      alert('Signoff feedback submitted successfully!');
      
      // Refresh assessment after feedback
      await fetchAssessmentReadiness();

    } catch (err) {
      console.error('Failed to submit signoff feedback:', err);
      alert('Failed to submit signoff feedback. Please try again.');
    } finally {
      setIsSubmittingSignoff(false);
    }
  };

  const getReadinessColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getReadinessBadgeVariant = (state: string) => {
    switch (state) {
      case 'assessment_ready': return 'default';
      case 'optimization_ready': return 'default';
      case 'partially_ready': return 'secondary';
      case 'not_ready': return 'destructive';
      default: return 'outline';
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5 animate-spin" />
              Assessing Portfolio Readiness...
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              Assessment Readiness Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchAssessmentReadiness} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry Assessment
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!readinessAssessment) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>Assessment Readiness</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">No assessment readiness data available.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      {/* Overall Readiness Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Assessment Readiness Dashboard
            </span>
            <Button onClick={fetchAssessmentReadiness} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="text-center">
              <div className={`text-3xl font-bold ${getReadinessColor(readinessAssessment.overall_readiness.readiness_score)}`}>
                {Math.round(readinessAssessment.overall_readiness.readiness_score * 100)}%
              </div>
              <div className="text-sm text-gray-600">Overall Readiness</div>
              <Badge variant={getReadinessBadgeVariant(readinessAssessment.overall_readiness.readiness_state)} className="mt-1">
                {readinessAssessment.overall_readiness.readiness_state.replace('_', ' ')}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {readinessAssessment.handoff_metadata.applications_ready_for_assessment}
              </div>
              <div className="text-sm text-gray-600">Apps Ready</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {readinessAssessment.outstanding_questions.length}
              </div>
              <div className="text-sm text-gray-600">Outstanding Questions</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getReadinessColor(readinessAssessment.overall_readiness.confidence_level)}`}>
                {Math.round(readinessAssessment.overall_readiness.confidence_level * 100)}%
              </div>
              <div className="text-sm text-gray-600">Confidence Level</div>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Assessment Readiness Progress</span>
              <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.overall_readiness.readiness_score)}`}>
                {Math.round(readinessAssessment.overall_readiness.readiness_score * 100)}%
              </span>
            </div>
            <Progress value={readinessAssessment.overall_readiness.readiness_score * 100} className="h-2" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">Recommended Action</h4>
              <p className="text-sm text-gray-700">{readinessAssessment.overall_readiness.recommended_action}</p>
            </div>
            <div>
              <h4 className="font-medium mb-2">Timeline</h4>
              <p className="text-sm text-gray-700">{readinessAssessment.overall_readiness.recommended_timeline}</p>
            </div>
          </div>

          {readinessAssessment.overall_readiness.critical_gaps.length > 0 && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="font-medium text-red-800 mb-2 flex items-center">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Critical Gaps
              </h4>
              <ul className="text-sm text-red-700 space-y-1">
                {readinessAssessment.overall_readiness.critical_gaps.map((gap, index) => (
                  <li key={index} className="flex items-start">
                    <span className="inline-block w-2 h-2 bg-red-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                    {gap}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="dashboard">Readiness Breakdown</TabsTrigger>
          <TabsTrigger value="applications">Application Priorities</TabsTrigger>
          <TabsTrigger value="preparation">Assessment Preparation</TabsTrigger>
          <TabsTrigger value="signoff">Stakeholder Sign-off</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Data Discovery */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-blue-600" />
                  Data Discovery
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Asset Inventory</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.data_discovery.asset_inventory_completeness)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.data_discovery.asset_inventory_completeness * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.data_discovery.asset_inventory_completeness * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Application Identification</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.data_discovery.application_identification_completeness)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.data_discovery.application_identification_completeness * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.data_discovery.application_identification_completeness * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Data Quality</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.data_discovery.data_quality_score)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.data_discovery.data_quality_score * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.data_discovery.data_quality_score * 100} className="h-2" />
                </div>

                {readinessAssessment.readiness_breakdown.data_discovery.discovery_gaps.length > 0 && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h5 className="font-medium text-yellow-800 mb-2">Gaps to Address</h5>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      {readinessAssessment.readiness_breakdown.data_discovery.discovery_gaps.map((gap, index) => (
                        <li key={index}>• {gap}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Business Context */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-green-600" />
                  Business Context
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Stakeholder Input</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.business_context.stakeholder_input_completeness)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.business_context.stakeholder_input_completeness * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.business_context.stakeholder_input_completeness * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Business Criticality</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.business_context.business_criticality_mapping)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.business_context.business_criticality_mapping * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.business_context.business_criticality_mapping * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Risk Tolerance</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.business_context.risk_tolerance_clarity)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.business_context.risk_tolerance_clarity * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.business_context.risk_tolerance_clarity * 100} className="h-2" />
                </div>

                {readinessAssessment.readiness_breakdown.business_context.business_gaps.length > 0 && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h5 className="font-medium text-yellow-800 mb-2">Gaps to Address</h5>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      {readinessAssessment.readiness_breakdown.business_context.business_gaps.map((gap, index) => (
                        <li key={index}>• {gap}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Technical Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-purple-600" />
                  Technical Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Tech Debt Assessment</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.technical_analysis.tech_debt_assessment_completeness)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.technical_analysis.tech_debt_assessment_completeness * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.technical_analysis.tech_debt_assessment_completeness * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Security Assessment</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.technical_analysis.security_assessment_completeness)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.technical_analysis.security_assessment_completeness * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.technical_analysis.security_assessment_completeness * 100} className="h-2" />
                </div>
              </CardContent>
            </Card>

            {/* Workflow Progression */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-orange-600" />
                  Workflow Progression
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Discovery Phase</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.workflow_progression.discovery_phase_completion)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.workflow_progression.discovery_phase_completion * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.workflow_progression.discovery_phase_completion * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Mapping Phase</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.workflow_progression.mapping_phase_completion)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.workflow_progression.mapping_phase_completion * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.workflow_progression.mapping_phase_completion * 100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Cleanup Phase</span>
                    <span className={`text-sm font-medium ${getReadinessColor(readinessAssessment.readiness_breakdown.workflow_progression.cleanup_phase_completion)}`}>
                      {Math.round(readinessAssessment.readiness_breakdown.workflow_progression.cleanup_phase_completion * 100)}%
                    </span>
                  </div>
                  <Progress value={readinessAssessment.readiness_breakdown.workflow_progression.cleanup_phase_completion * 100} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="applications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Prioritized Applications for Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {readinessAssessment.prioritized_applications.slice(0, 10).map((app, index) => (
                  <div key={app.application_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                          {app.recommended_assessment_order}
                        </div>
                        <h3 className="font-semibold text-lg">{app.application_name}</h3>
                        <Badge variant="outline">
                          Priority: {Math.round(app.assessment_priority_score * 100)}%
                        </Badge>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-medium ${getReadinessColor(app.readiness_score)}`}>
                          {Math.round(app.readiness_score * 100)}% Ready
                        </span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Complexity:</span>
                        <span className="ml-1 font-medium">{app.assessment_complexity}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Stakeholder Attention:</span>
                        <span className="ml-1 font-medium">{app.stakeholder_attention_required}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Readiness Level:</span>
                        <Badge variant={getReadinessBadgeVariant(app.readiness_level)} className="ml-1">
                          {app.readiness_level.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      <p className="text-sm text-gray-700">{app.priority_justification}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preparation" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  Assessment Preparation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {readinessAssessment.assessment_preparation.map((item, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                      <span className="text-sm">{item}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-orange-600" />
                  Outstanding Questions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {readinessAssessment.outstanding_questions.map((question, index) => (
                    <div key={index} className="border-l-4 border-orange-400 pl-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-500 uppercase">{question.phase}</span>
                        <span className="text-xs text-orange-600">
                          Impact: {Math.round(question.assessment_impact_score * 100)}%
                        </span>
                      </div>
                      <p className="text-sm">{question.question}</p>
                    </div>
                  ))}
                  
                  {readinessAssessment.outstanding_questions.length === 0 && (
                    <div className="text-center py-4 text-gray-500">
                      <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-600" />
                      <p>All questions have been resolved!</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="signoff" className="space-y-6">
          {signoffPackage ? (
            <div className="space-y-6">
              {/* Executive Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="h-5 w-5 text-yellow-600" />
                    Executive Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {signoffPackage.executive_summary.applications_ready_for_assessment}
                      </div>
                      <div className="text-sm text-gray-600">
                        of {signoffPackage.executive_summary.total_applications} Apps Ready
                      </div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${getReadinessColor(signoffPackage.executive_summary.business_confidence)}`}>
                        {Math.round(signoffPackage.executive_summary.business_confidence * 100)}%
                      </div>
                      <div className="text-sm text-gray-600">Business Confidence</div>
                    </div>
                    <div className="text-center">
                      <Badge variant={getReadinessBadgeVariant(signoffPackage.executive_summary.assessment_readiness_status)} className="text-lg px-3 py-1">
                        {signoffPackage.executive_summary.assessment_readiness_status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-2 text-green-800">Key Achievements</h4>
                      <ul className="text-sm space-y-1">
                        {signoffPackage.executive_summary.key_achievements.map((achievement, index) => (
                          <li key={index} className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
                            {achievement}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2 text-orange-800">Remaining Gaps</h4>
                      <ul className="text-sm space-y-1">
                        {signoffPackage.executive_summary.remaining_gaps.map((gap, index) => (
                          <li key={index} className="flex items-start">
                            <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 mr-2 flex-shrink-0" />
                            {gap}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Assessment */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-purple-600" />
                    Risk Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <span className="text-sm text-gray-600">Assessment Phase Risk Level: </span>
                    <span className={`font-medium ${getRiskColor(signoffPackage.assessment_risk_evaluation.risk_level)}`}>
                      {signoffPackage.assessment_risk_evaluation.risk_level.toUpperCase()}
                    </span>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2">Risk Factors</h4>
                    <ul className="text-sm space-y-1">
                      {signoffPackage.assessment_risk_evaluation.risk_factors.map((factor, index) => (
                        <li key={index} className="flex items-start">
                          <span className="inline-block w-2 h-2 bg-purple-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                          {factor}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Signoff Decision */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-600" />
                    Stakeholder Sign-off Decision
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Decision</label>
                      <div className="space-y-2">
                        <label className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name="signoff"
                            value="approve"
                            checked={signoffDecision === 'approve'}
                            onChange={(e) => setSignoffDecision(e.target.value)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm">Approve - Proceed to Assessment Phase</span>
                        </label>
                        <label className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name="signoff"
                            value="conditional"
                            checked={signoffDecision === 'conditional'}
                            onChange={(e) => setSignoffDecision(e.target.value)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm">Conditional Approval - Address concerns first</span>
                        </label>
                        <label className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name="signoff"
                            value="reject"
                            checked={signoffDecision === 'reject'}
                            onChange={(e) => setSignoffDecision(e.target.value)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm">Reject - Continue Discovery Phase</span>
                        </label>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Comments/Concerns (Optional)</label>
                      <textarea
                        value={stakeholderConcerns}
                        onChange={(e) => setStakeholderConcerns(e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows={4}
                        placeholder="Enter any concerns or additional requirements..."
                      />
                    </div>

                    <Button
                      onClick={handleSignoffSubmission}
                      disabled={!signoffDecision || isSubmittingSignoff}
                      className="w-full"
                    >
                      {isSubmittingSignoff ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        <>
                          <ArrowRight className="h-4 w-4 mr-2" />
                          Submit Signoff Decision
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Stakeholder Sign-off</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Clock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600">
                    Signoff package will be available when readiness score reaches 60% or higher.
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Current readiness: {Math.round(readinessAssessment.overall_readiness.readiness_score * 100)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AssessmentReadiness; 