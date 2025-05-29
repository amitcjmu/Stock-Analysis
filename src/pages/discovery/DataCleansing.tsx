import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Wrench, CheckCircle, AlertTriangle, Lightbulb, 
  RefreshCw, Save, Bot, User, ArrowRight, Filter, Eye,
  ThumbsUp, ThumbsDown, MessageSquare, Zap, Target,
  ArrowLeft, Info, FileCheck
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

interface DataIssue {
  id: string;
  assetId: string;
  assetName: string;
  field: string;
  currentValue: string;
  suggestedValue: string;
  confidence: number;
  category: 'misclassification' | 'missing_data' | 'incorrect_mapping' | 'duplicate';
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected' | 'fixed';
}

interface ValidationRule {
  id: string;
  field: string;
  rule: string;
  description: string;
  enabled: boolean;
}

const DataCleansing = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [issues, setIssues] = useState<DataIssue[]>([]);
  const [validationRules, setValidationRules] = useState<ValidationRule[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<DataIssue | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('issues');
  const [filterCategory, setFilterCategory] = useState('all');
  const [progress, setProgress] = useState({ fixed: 0, pending: 0, total: 0 });
  const [fromDataImport, setFromDataImport] = useState(false);
  const [importedIssues, setImportedIssues] = useState<DataIssue[]>([]);

  useEffect(() => {
    // Check if we came from Data Import with issues
    const state = location.state as any;
    if (state?.dataQualityIssues && state?.fromDataImport) {
      setFromDataImport(true);
      setImportedIssues(state.dataQualityIssues);
      setIssues(state.dataQualityIssues);
      setProgress({
        fixed: 0,
        pending: state.dataQualityIssues.length,
        total: state.dataQualityIssues.length
      });
      setIsLoading(false);
    } else {
      fetchDataIssues();
    }
    
    fetchValidationRules();
  }, [location.state]);

  const fetchDataIssues = async () => {
    try {
      setIsLoading(true);
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/data-issues`);
      setIssues(response.issues || []);
      setProgress(response.progress || { fixed: 0, pending: 0, total: 0 });
    } catch (error) {
      console.error('Failed to fetch data issues:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchValidationRules = async () => {
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/validation-rules`);
      setValidationRules(response.rules || []);
    } catch (error) {
      console.error('Failed to fetch validation rules:', error);
    }
  };

  const handleApproveIssue = async (issueId: string) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/data-issues/${issueId}/approve`, {
        method: 'POST'
      });
      
      setIssues(prev => prev.map(issue => 
        issue.id === issueId ? { ...issue, status: 'approved' } : issue
      ));
      
      // Update progress
      setProgress(prev => ({
        ...prev,
        fixed: prev.fixed + 1,
        pending: prev.pending - 1
      }));
      
    } catch (error) {
      console.error('Failed to approve issue:', error);
    }
  };

  const handleRejectIssue = async (issueId: string, feedback?: string) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/data-issues/${issueId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback })
      });
      
      setIssues(prev => prev.map(issue => 
        issue.id === issueId ? { ...issue, status: 'rejected' } : issue
      ));
      
    } catch (error) {
      console.error('Failed to reject issue:', error);
    }
  };

  const runDataValidation = async () => {
    try {
      setIsLoading(true);
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/validate-data`, {
        method: 'POST'
      });
      await fetchDataIssues();
    } catch (error) {
      console.error('Failed to run validation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'misclassification': return <Target className="h-5 w-5" />;
      case 'missing_data': return <AlertTriangle className="h-5 w-5" />;
      case 'incorrect_mapping': return <ArrowRight className="h-5 w-5" />;
      case 'duplicate': return <Filter className="h-5 w-5" />;
      default: return <Eye className="h-5 w-5" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'misclassification': return 'text-red-600 bg-red-100';
      case 'missing_data': return 'text-yellow-600 bg-yellow-100';
      case 'incorrect_mapping': return 'text-blue-600 bg-blue-100';
      case 'duplicate': return 'text-purple-600 bg-purple-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredIssues = issues.filter(issue => 
    filterCategory === 'all' || issue.category === filterCategory
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Cleansing & Validation</h1>
                  <p className="text-lg text-gray-600">
                    Human-in-the-loop data quality improvement powered by AI insights
                  </p>
                </div>
                {fromDataImport && (
                  <button
                    onClick={() => navigate('/discovery/data-import')}
                    className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    <span>Back to Data Import</span>
                  </button>
                )}
              </div>
              
              {fromDataImport && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <Info className="h-6 w-6 text-blue-600 mt-0.5" />
                    <div>
                      <h3 className="font-medium text-blue-900 mb-1">Data Quality Issues Detected</h3>
                      <p className="text-sm text-blue-800">
                        Our AI crew identified {importedIssues.length} data quality issues during the import process. 
                        Review and approve the AI's suggestions below to improve your data quality before proceeding.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Progress Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">{progress.total}</h3>
                    <p className="text-sm text-gray-600">Total Issues</p>
                  </div>
                  <Wrench className="h-8 w-8 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-yellow-600">{progress.pending}</h3>
                    <p className="text-sm text-gray-600">Pending Review</p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-yellow-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-green-600">{progress.fixed}</h3>
                    <p className="text-sm text-gray-600">Fixed</p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-green-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-blue-600">
                      {Math.round((progress.fixed / (progress.total || 1)) * 100)}%
                    </h3>
                    <p className="text-sm text-gray-600">Completion</p>
                  </div>
                  <Target className="h-8 w-8 text-blue-500" />
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex justify-between items-center">
                <div className="flex space-x-4">
                  <button
                    onClick={runDataValidation}
                    disabled={isLoading}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Run Validation</span>
                  </button>
                  
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Categories</option>
                    <option value="misclassification">Misclassification</option>
                    <option value="missing_data">Missing Data</option>
                    <option value="incorrect_mapping">Incorrect Mapping</option>
                    <option value="duplicate">Duplicates</option>
                  </select>
                </div>
                
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Bot className="h-4 w-4" />
                  <span>AI-powered suggestions ready for review</span>
                </div>
              </div>
            </div>

            {/* Issues List */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Data Quality Issues</h2>
                
                {filteredIssues.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Issues Found</h3>
                    <p className="text-gray-600">Your data quality looks good!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredIssues.map((issue) => (
                      <div key={issue.id} className="border border-gray-200 rounded-lg p-6">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-lg ${getCategoryColor(issue.category)}`}>
                              {getCategoryIcon(issue.category)}
                            </div>
                            <div>
                              <h3 className="font-medium text-gray-900">{issue.assetName}</h3>
                              <p className="text-sm text-gray-600">Field: {issue.field}</p>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <span className={`text-sm font-medium ${getConfidenceColor(issue.confidence)}`}>
                              {Math.round(issue.confidence * 100)}% confidence
                            </span>
                            <div className={`px-2 py-1 rounded-full text-xs ${
                              issue.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              issue.status === 'approved' ? 'bg-green-100 text-green-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {issue.status}
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                            <label className="text-sm font-medium text-gray-700">Current Value</label>
                            <div className="mt-1 p-3 bg-red-50 border border-red-200 rounded-lg">
                              <span className="text-red-800">{issue.currentValue}</span>
                            </div>
                          </div>
                          
                          <div>
                            <label className="text-sm font-medium text-gray-700">Suggested Value</label>
                            <div className="mt-1 p-3 bg-green-50 border border-green-200 rounded-lg">
                              <span className="text-green-800">{issue.suggestedValue}</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="mb-4">
                          <label className="text-sm font-medium text-gray-700">AI Reasoning</label>
                          <div className="mt-1 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="flex items-start space-x-2">
                              <Lightbulb className="h-4 w-4 text-blue-600 mt-0.5" />
                              <p className="text-sm text-blue-800">{issue.reasoning}</p>
                            </div>
                          </div>
                        </div>
                        
                        {issue.status === 'pending' && (
                          <div className="flex justify-end space-x-3">
                            <button
                              onClick={() => handleRejectIssue(issue.id)}
                              className="flex items-center space-x-2 px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
                            >
                              <ThumbsDown className="h-4 w-4" />
                              <span>Reject</span>
                            </button>
                            
                            <button
                              onClick={() => handleApproveIssue(issue.id)}
                              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                            >
                              <ThumbsUp className="h-4 w-4" />
                              <span>Approve & Fix</span>
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default DataCleansing; 