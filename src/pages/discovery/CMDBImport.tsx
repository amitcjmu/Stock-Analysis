import React, { useState, useCallback } from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { Link, useNavigate } from 'react-router-dom';
import { apiCall, API_CONFIG } from '../../config/api';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import {
  Upload,
  FileSpreadsheet,
  Database,
  Monitor,
  FileText,
  Activity,
  Brain,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Zap,
  Users,
  Eye,
  Loader2,
  Clock,
  Bot,
  FileCheck,
  AlertCircle,
  Lightbulb,
  ExternalLink
} from 'lucide-react';

// Add custom CSS for animations
const styles = `
  @keyframes slide-in-right {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-slide-in-right {
    animation: slide-in-right 0.3s ease-out;
  }
  
  .animate-fade-in {
    animation: fade-in 0.5s ease-out;
  }
`;

interface UploadArea {
  id: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  acceptedTypes: string[];
  examples: string[];
}

interface UploadedFile {
  file: File;
  type: string;
  status: 'uploaded' | 'analyzing' | 'processed' | 'error';
  aiSuggestions?: string[];
  nextSteps?: Array<{
    label: string;
    route?: string;
    description?: string;
    isExternal?: boolean;
    dataQualityIssues?: any[];
  }>;
  confidence?: number;
  detectedFileType?: string;
  analysisSteps?: string[];
  currentStep?: number;
  processingMessages?: string[];
  analysisError?: string;
}

const DataImport = () => {
  const navigate = useNavigate();
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [selectedUploadType, setSelectedUploadType] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

const uploadAreas: UploadArea[] = [
    {
      id: 'cmdb',
      title: 'CMDB Data',
      description: 'Configuration Management Database exports with asset information',
      icon: Database,
      color: 'bg-blue-500',
      acceptedTypes: ['.csv', '.xlsx', '.json'],
      examples: ['ServiceNow exports', 'BMC Remedy data', 'Custom CMDB files']
    },
    {
      id: 'app-scan',
      title: 'Application Scan Data',
      description: 'Application discovery and dependency scan results',
      icon: Monitor,
      color: 'bg-green-500',
      acceptedTypes: ['.csv', '.json', '.xml'],
      examples: ['Appdynamics exports', 'Dynatrace data', 'New Relic reports']
    },
    {
      id: 'migration-discovery',
      title: 'Migration Discovery Data',
      description: 'Migration readiness assessments and infrastructure details',
      icon: Activity,
      color: 'bg-purple-500',
      acceptedTypes: ['.csv', '.xlsx', '.json'],
      examples: ['AWS Migration Hub', 'Azure Migrate data', 'Migration assessments']
    },
    {
      id: 'documentation',
      title: 'Documentation',
      description: 'Technical documentation, architecture diagrams, and runbooks',
      icon: FileText,
      color: 'bg-orange-500',
      acceptedTypes: ['.pdf', '.doc', '.docx', '.md'],
      examples: ['Architecture docs', 'Runbooks', 'Technical specifications']
    },
    {
      id: 'monitoring',
      title: 'Application Monitoring Data',
      description: 'Performance metrics, logs, and monitoring tool exports',
      icon: Activity,
      color: 'bg-red-500',
      acceptedTypes: ['.csv', '.json', '.log'],
      examples: ['Splunk exports', 'Prometheus data', 'CloudWatch logs']
    }
  ];

  const onDrop = useCallback((acceptedFiles: File[], uploadType: string) => {
    console.log('onDrop called with:', acceptedFiles.length, 'files, type:', uploadType);
    
    // Show immediate upload success feedback
    setShowUploadSuccess(true);
    setTimeout(() => setShowUploadSuccess(false), 3000);
    
    const newFiles = acceptedFiles.map(file => ({
      file,
      type: uploadType,
      status: 'uploaded' as const,
      detectedFileType: detectFileType(file),
      analysisSteps: [
        'Initial file scan',
        'Content structure analysis', 
        'Data pattern recognition',
        'Field mapping suggestions',
        'Quality assessment',
        'Next steps generation'
      ],
      currentStep: 0,
      processingMessages: []
    }));
    
    console.log('Created file objects:', newFiles);
    setUploadedFiles(prev => {
      console.log('Previous files:', prev.length, 'Adding:', newFiles.length);
      return [...prev, ...newFiles];
    });
    
    // Auto-analyze the files with a slight delay for better UX
    setTimeout(() => analyzeFiles(newFiles), 500);
  }, []);

  const detectFileType = (file: File): string => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    const size = file.size;
    
    if (extension === 'csv') {
      if (size > 10 * 1024 * 1024) return 'Large CSV Dataset';
      return 'CSV Data File';
    } else if (extension === 'xlsx' || extension === 'xls') {
      return 'Excel Spreadsheet';
    } else if (extension === 'json') {
      return 'JSON Data File';
    } else if (extension === 'xml') {
      return 'XML Configuration';
    } else if (extension === 'pdf') {
      return 'PDF Document';
    } else if (extension === 'doc' || extension === 'docx') {
      return 'Word Document';
    } else if (extension === 'md') {
      return 'Markdown Documentation';
    } else if (extension === 'log') {
      return 'Log File';
    }
    
    return 'Unknown File Type';
  };

  const analyzeFiles = async (files: UploadedFile[]) => {
    console.log('analyzeFiles called with:', files.length, 'files');
    setIsAnalyzing(true);
    
    for (const fileUpload of files) {
      console.log('Analyzing file:', fileUpload.file.name, 'intended type:', fileUpload.type);
      
      // Update status to analyzing
      setUploadedFiles(prev => 
        prev.map(f => f.file === fileUpload.file ? { 
          ...f, 
          status: 'analyzing',
          analysisError: undefined,
          processingMessages: ['🤖 AI crew initializing...']
        } : f)
      );
      
      try {
        // Send to the unified agent analysis endpoint
        const fileContent = await readFileContent(fileUpload.file);
        console.log('Sending file to AI crew for intelligent analysis:', fileUpload.file.name);

        const requestBody = {
          analysis_type: 'data_source_analysis',
          data_source: {
            file_data: btoa(fileContent), // Base64 encode the file content
            metadata: {
              filename: fileUpload.file.name,
              size: fileUpload.file.size,
              type: fileUpload.file.type,
              lastModified: fileUpload.file.lastModified,
              import_session_id: fileUpload.id, // Use the unique ID for this upload session
            },
          },
        };

        const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
          method: 'POST',
          body: JSON.stringify(requestBody),
        });

        console.log('AI crew intelligent analysis result:', result);

        if (result.agent_analysis?.status === 'error') {
          const errorMessage = result.agent_analysis.message || 'An unknown error occurred during analysis.';
          const errorDetails = result.agent_analysis.details ? `Details: ${result.agent_analysis.details.join(', ')}` : '';
          throw new Error(`${errorMessage} ${errorDetails}`);
        }

        // Simulate processing steps for better UX
        const messages = ['✅ AI crew analysis complete.'];
        for (let i = 0; i < messages.length; i++) {
          await new Promise(resolve => setTimeout(resolve, 700));
          setUploadedFiles(prev =>
            prev.map(f => f.file === fileUpload.file ? {
              ...f,
              currentStep: i + 1,
              processingMessages: [...(f.processingMessages || []), messages[i]]
            } : f)
          );
        }

        setUploadedFiles(prev =>
          prev.map(f => f.file === fileUpload.file ? {
            ...f,
            status: 'processed',
            aiSuggestions: result.agent_analysis?.suggestions || [],
            nextSteps: result.agent_analysis?.next_steps || [],
            confidence: result.agent_analysis?.confidence || 0
          } : f)
        );
        
        // Refresh agent panels after analysis
        setAgentRefreshTrigger(prev => prev + 1);

      } catch (error) {
        console.error("Error analyzing file:", error);
        setUploadedFiles(prev =>
          prev.map(f => f.file === fileUpload.file ? {
            ...f,
            status: 'error',
            analysisError: error instanceof Error ? error.message : 'An unknown error occurred.'
          } : f)
        );
      }
    }
    
    setIsAnalyzing(false);
    console.log('All files analyzed with intelligent AI crew');
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      reader.onerror = (e) => {
        reject(new Error('Failed to read file'));
      };
      reader.readAsText(file);
    });
  };

  const parseFileContent = (content: string, filename: string, parseAll: boolean = false) => {
    // Parse content based on file type for agent analysis or full data storage
    try {
      if (filename.endsWith('.csv')) {
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length === 0) return [];
        
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        const dataLines = parseAll ? lines.slice(1) : lines.slice(1, 6); // Parse all or first 5 rows
        
        return dataLines.map(line => {
          const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
          const row: any = {};
          headers.forEach((header, index) => {
            row[header] = values[index] || '';
          });
          return row;
        }).filter(row => Object.values(row).some(v => v)); // Remove empty rows
      } else if (filename.endsWith('.json')) {
        const parsed = JSON.parse(content);
        if (parseAll) {
          return Array.isArray(parsed) ? parsed : [parsed];
        } else {
          return Array.isArray(parsed) ? parsed.slice(0, 5) : [parsed];
        }
      } else {
        // For other file types, return a sample of the content
        return [{ content: parseAll ? content : content.substring(0, 1000) }];
      }
    } catch (error) {
      console.error('Error parsing file content:', error);
      return [{ content: content.substring(0, 500) }];
    }
  };

  const getUploadAreaInfo = (uploadType: string) => {
    const contextMap: { [key: string]: string } = {
      'cmdb': 'User intended this as CMDB/Configuration Management data',
      'app-scan': 'User intended this as Application Scan/Performance data', 
      'migration-discovery': 'User intended this as Migration Discovery/Assessment data',
      'documentation': 'User intended this as Documentation/Runbooks - analyze for application-related information',
      'monitoring': 'User intended this as Application Monitoring/Performance data'
    };
    
    return contextMap[uploadType] || 'User uploaded data for analysis';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <FileSpreadsheet className="h-5 w-5 text-gray-500" />;
      case 'analyzing':
        return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default:
        return <FileSpreadsheet className="h-5 w-5 text-gray-500" />;
    }
  };

  const FileUploadZone = ({ area }: { area: UploadArea }) => {
    const Icon = area.icon;
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    
    const handleZoneClick = () => {
      console.log('Upload zone clicked for:', area.title);
      setSelectedUploadType(area.id);
      fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      console.log('File input changed:', e.target.files);
      if (e.target.files && e.target.files.length > 0) {
        console.log('Processing files:', Array.from(e.target.files).map(f => f.name));
        onDrop(Array.from(e.target.files), area.id);
        // Reset input so same file can be selected again
        e.target.value = '';
      }
    };
    
    return (
      <div 
        className={`relative border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-500 transition-colors cursor-pointer ${
          selectedUploadType === area.id ? 'border-blue-500 bg-blue-50' : ''
        }`}
        onClick={handleZoneClick}
      >
        <div className="text-center pointer-events-none">
          <div className={`${area.color} mx-auto h-12 w-12 rounded-lg flex items-center justify-center mb-4`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">{area.title}</h3>
          <p className="text-sm text-gray-600 mb-4">{area.description}</p>
          
          <div className="text-xs text-gray-500 mb-2">
            <strong>Accepted formats:</strong> {area.acceptedTypes.join(', ')}
          </div>
          
          <div className="text-xs text-gray-500 mb-4">
            <strong>Examples:</strong> {area.examples.join(', ')}
          </div>

          <div className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">
            <Upload className="h-4 w-4 mr-2" />
            Click to upload files
          </div>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={area.acceptedTypes.join(',')}
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
    );
  };

  return (
    <>
      <style>{styles}</style>
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden ml-64">
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
            <div className="flex h-full">
              {/* Main Content Area */}
              <div className="flex-1 overflow-y-auto">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-5xl">
              {/* Context Breadcrumbs */}
              <div className="mb-6">
                <ContextBreadcrumbs />
              </div>
              
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Intelligent Data Analysis</h1>
                <p className="mt-2 text-gray-600">
                  Upload any data file and let our AI crew intelligently determine its type, value, and processing requirements
                </p>
                <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Brain className="h-6 w-6 text-blue-600" />
                    <div>
                      <p className="text-sm text-blue-800">
                        <strong>Smart AI Analysis:</strong> Our intelligent agents analyze any uploaded data to determine actual content type, assess quality and relevance, then recommend the optimal processing workflow for your migration journey.
                      </p>
                    </div>
                  </div>
                </div>
        </div>
        
              {/* Upload Success Toast */}
              {showUploadSuccess && (
                <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in-right z-50">
                  <CheckCircle className="h-5 w-5" />
                  <span>File uploaded successfully! AI analysis starting...</span>
                </div>
              )}

              {/* Upload Areas */}
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Your Data (AI Will Determine Actual Type)</h2>
                <p className="text-sm text-gray-600 mb-6">
                  Choose the category that best represents what you <em>intended</em> to upload. Our AI crew will analyze the actual content and determine its true type and value.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {uploadAreas.map((area) => (
                    <FileUploadZone key={area.id} area={area} />
                  ))}
                </div>
              </div>

              {/* Uploaded Files */}
              {uploadedFiles.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-semibold text-gray-900">AI Crew Analysis</h2>
                    {isAnalyzing && (
                      <div className="flex items-center space-x-2 text-blue-600">
                        <Bot className="h-5 w-5 animate-pulse" />
                        <span className="text-sm font-medium">Agentic crew active</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-6">
                    {uploadedFiles.map((fileUpload, index) => {
                      const uploadArea = uploadAreas.find(area => area.id === fileUpload.type);
                      const Icon = uploadArea?.icon || FileSpreadsheet;
                      
                      return (
                        <div key={index} className="border border-gray-200 rounded-lg p-6 transition-all duration-300 hover:shadow-md">
                          {/* File Header */}
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              {getStatusIcon(fileUpload.status)}
                              <div>
                                <h3 className="font-medium text-gray-900">{fileUpload.file.name}</h3>
                                <div className="flex items-center space-x-2 text-sm text-gray-500">
                                  <Icon className="h-4 w-4" />
                                  <span>{uploadArea?.title}</span>
                                  <span>•</span>
                                  <span>{(fileUpload.file.size / 1024 / 1024).toFixed(2)} MB</span>
                                  {fileUpload.detectedFileType && (
                                    <>
                                      <span>•</span>
                                      <span className="text-blue-600 font-medium">{fileUpload.detectedFileType}</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                            {fileUpload.confidence && (
                              <div className="text-right">
                                <div className="text-lg font-semibold text-green-600">{fileUpload.confidence}%</div>
                                <div className="text-xs text-gray-500">AI Confidence</div>
                              </div>
                            )}
                          </div>

                          {/* Processing Animation */}
                          {fileUpload.status === 'analyzing' && (
                            <div className="space-y-4">
                              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                                <div className="flex items-center space-x-2 mb-3">
                                  <Bot className="h-5 w-5 text-blue-600 animate-bounce" />
                                  <h4 className="font-medium text-blue-900">AI Crew Processing</h4>
                                  <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                                </div>
                                
                                {/* Processing Steps */}
                                <div className="space-y-2 mb-4">
                                  {fileUpload.analysisSteps?.map((step, idx) => (
                                    <div key={idx} className={`flex items-center space-x-2 text-sm transition-all duration-300 ${
                                      idx <= (fileUpload.currentStep || 0) ? 'text-blue-800' : 'text-gray-500'
                                    }`}>
                                      {idx < (fileUpload.currentStep || 0) ? (
                                        <CheckCircle className="h-4 w-4 text-green-500" />
                                      ) : idx === (fileUpload.currentStep || 0) ? (
                                        <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                                      ) : (
                                        <Clock className="h-4 w-4 text-gray-400" />
                                      )}
                                      <span className={idx <= (fileUpload.currentStep || 0) ? 'font-medium' : ''}>{step}</span>
                                    </div>
                                  ))}
                                </div>
                                
                                {/* Live Processing Messages */}
                                <div className="bg-white rounded p-3 max-h-32 overflow-y-auto">
                                  <div className="text-xs text-gray-600 mb-1">Live Analysis Feed:</div>
                                  {fileUpload.processingMessages?.map((message, idx) => (
                                    <div key={idx} className="text-sm text-gray-800 animate-fade-in flex items-center space-x-1">
                                      <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                                      <span>{message}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Analysis Results */}
                          {fileUpload.status === 'processed' && fileUpload.aiSuggestions && (
                            <div className="space-y-4">
                              {/* File Type Detection */}
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center space-x-2 mb-2">
                                  <FileCheck className="h-5 w-5 text-gray-600" />
                                  <h4 className="font-medium text-gray-900">File Analysis Summary</h4>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="text-gray-600">Detected Type:</span>
                                    <span className="ml-2 font-medium text-blue-600">{fileUpload.detectedFileType}</span>
                                  </div>
                <div>
                                    <span className="text-gray-600">Confidence:</span>
                                    <span className="ml-2 font-medium text-green-600">{fileUpload.confidence}%</span>
                                  </div>
                                </div>
                              </div>

                              {/* AI Insights */}
                              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <div className="flex items-center space-x-2 mb-3">
                                  <Lightbulb className="h-5 w-5 text-blue-600" />
                                  <h4 className="font-medium text-blue-900">AI Crew Insights</h4>
                                </div>
                                <ul className="space-y-2">
                                  {fileUpload.aiSuggestions.map((suggestion, idx) => (
                                    <li key={idx} className="text-sm text-blue-800 flex items-start space-x-2">
                                      <CheckCircle className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                                      <span>{suggestion}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>

                              {/* Next Steps */}
                              {fileUpload.nextSteps && (
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                  <div className="flex items-center space-x-2 mb-3">
                                    <ArrowRight className="h-5 w-5 text-green-600" />
                                    <h4 className="font-medium text-green-900">Recommended Next Steps</h4>
                                  </div>
                                  <div className="space-y-3">
                                    {fileUpload.nextSteps.map((step, idx) => {
                                      const handleNavigation = () => {
                                        if (step.route === '/discovery/data-cleansing' && step.dataQualityIssues) {
                                          navigate(step.route, {
                                            state: {
                                              dataQualityIssues: step.dataQualityIssues,
                                              fromDataImport: true
                                            }
                                          });
                                        } else if (step.route === '/discovery/attribute-mapping' && (step.importedData || step.import_session_id)) {
                                          navigate(step.route, {
                                            state: {
                                              importedData: step.importedData,
                                              import_session_id: step.import_session_id,
                                              fromDataImport: true
                                            }
                                          });
                                        } else if (step.route) {
                                          navigate(step.route);
                                        }
                                      };

                                      return (
                                        <div key={idx}>
                                          {step.route ? (
                                            <button 
                                              onClick={handleNavigation}
                                              className="group block w-full text-left p-3 border border-green-200 rounded-lg hover:border-green-400 hover:bg-green-100 transition-all duration-200"
                                            >
                                              <div className="flex items-center justify-between">
                                                <div className="flex items-start space-x-3">
                                                  <div className="bg-green-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                                                    {idx + 1}
                                                  </div>
                                                  <div className="flex-1">
                                                    <div className="text-sm font-medium text-green-800 group-hover:text-green-900">
                                                      {step.label}
                                                    </div>
                                                    {step.description && (
                                                      <div className="text-xs text-green-600 mt-1">
                                                        {step.description}
                                                      </div>
                                                    )}
                                                  </div>
                                                </div>
                                                <ExternalLink className="h-4 w-4 text-green-500 group-hover:text-green-700 flex-shrink-0" />
                                              </div>
                                            </button>
                                          ) : (
                                            <div className="flex items-start space-x-3 p-3 bg-green-100 rounded-lg">
                                              <div className="bg-green-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                                                {idx + 1}
                                              </div>
                                              <div className="flex-1">
                                                <div className="text-sm font-medium text-green-800">
                                                  {step.label}
                                                </div>
                                                {step.description && (
                                                  <div className="text-xs text-green-600 mt-1">
                                                    {step.description}
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                  
                                  <div className="mt-4 pt-3 border-t border-green-200">
                                    <div className="flex items-center space-x-2 text-sm text-green-700">
                                      <AlertCircle className="h-4 w-4" />
                                      <span className="font-medium">Ready for next phase:</span>
                                      <span>{getUploadAreaInfo(fileUpload.type)}</span>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Error State */}
                          {fileUpload.status === 'error' && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                              <div className="flex items-center space-x-2">
                                <AlertTriangle className="h-5 w-5 text-red-600" />
                                <span className="text-red-800">
                                  {fileUpload.processingMessages?.[0] || 'Analysis failed - please try again'}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Getting Started */}
              {uploadedFiles.length === 0 && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">How Intelligent Analysis Works</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">🤖 AI-Powered Content Detection</h3>
                      <ul className="space-y-1 text-sm text-gray-600">
                        <li>• AI crew analyzes actual file content and structure</li>
                        <li>• Determines true data type regardless of upload category</li>
                        <li>• Assesses data quality and migration relevance</li>
                        <li>• Scores information value for your migration project</li>
                      </ul>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">📊 Intelligent Recommendations</h3>
                      <ul className="space-y-1 text-sm text-gray-600">
                        <li>• Tailored processing workflow based on actual content</li>
                        <li>• Context-aware next steps for optimal migration planning</li>
                        <li>• Quality-based confidence scoring and issue identification</li>
                        <li>• Application-focused insights from any data type</li>
                      </ul>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Lightbulb className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="text-sm text-blue-800">
                          <strong>Pro Tip:</strong> Don't worry about choosing the "perfect" category - our AI crew is designed to understand your data regardless of how you categorize it. Just pick the closest match and let the intelligence do the rest!
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
            )}
        </div>
    </div>

              {/* Agent Interaction Sidebar */}
              <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
                <div className="p-4 space-y-4">
                  {/* Agent Clarification Panel */}
                  <AgentClarificationPanel 
                    pageContext="data-import"
                    refreshTrigger={agentRefreshTrigger}
                    isProcessing={isAnalyzing}
                    onQuestionAnswered={(questionId, response) => {
                      console.log('Question answered:', questionId, response);
                      // Trigger agent refresh after user interaction
                      setAgentRefreshTrigger(prev => prev + 1);
                    }}
                  />

                  {/* Data Classification Display */}
                  <DataClassificationDisplay 
                    pageContext="data-import"
                    refreshTrigger={agentRefreshTrigger}
                    isProcessing={isAnalyzing}
                    onClassificationUpdate={(itemId, newClassification) => {
                      console.log('Classification updated:', itemId, newClassification);
                      // Trigger agent refresh after user interaction
                      setAgentRefreshTrigger(prev => prev + 1);
                    }}
                  />

                  {/* Agent Insights Section */}
                  <AgentInsightsSection 
                    pageContext="data-import"
                    refreshTrigger={agentRefreshTrigger}
                    isProcessing={isAnalyzing}
                    onInsightAction={(insightId, action) => {
                      console.log('Insight action:', insightId, action);
                      // Trigger agent refresh after user interaction
                      setAgentRefreshTrigger(prev => prev + 1);
                    }}
                  />
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default DataImport; 