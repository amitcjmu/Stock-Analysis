import React, { useCallback, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload,
  FileCheck, 
  AlertTriangle, 
  CheckCircle, 
  Shield,
  Brain,
  Database,
  Monitor,
  Activity,
  FileText,
  AlertCircle,
  Loader2,
  Eye,
  ArrowRight,
  FileSpreadsheet,
  Lock,
  Scan,
  UserCheck
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

// Data Import Validation Agents
interface DataImportAgent {
  id: string;
  name: string;
  role: string;
  icon: any;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  result?: {
    validation: 'passed' | 'failed' | 'warning';
    message: string;
    details: string[];
    confidence: number;
  };
}

interface UploadFile {
  id: string;
  filename: string;
  size: number;
  type: string;
  status: 'uploading' | 'validating' | 'approved' | 'rejected' | 'error';
  upload_progress: number;
  validation_progress: number;
  agents_completed: number;
  total_agents: number;
  security_clearance: boolean;
  privacy_clearance: boolean;
  format_validation: boolean;
  error_message?: string;
}

// Upload categories for proper data handling
const uploadCategories = [
  {
    id: 'cmdb',
    title: 'CMDB Export Data',
    description: 'Configuration Management Database exports with asset information',
    icon: Database,
    color: 'bg-blue-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['ServiceNow exports', 'BMC Remedy data', 'Custom CMDB files'],
    securityLevel: 'standard',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor']
  },
  {
    id: 'app-discovery',
    title: 'Application Discovery Data',
    description: 'Application portfolio and dependency scan results',
    icon: Monitor,
    color: 'bg-green-500',
    acceptedTypes: ['.csv', '.json', '.xml'],
    examples: ['Application scans', 'Dependency maps', 'Service inventories'],
    securityLevel: 'elevated',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'dependency_validator']
  },
  {
    id: 'infrastructure',
    title: 'Infrastructure Assessment',
    description: 'Server, network, and infrastructure discovery data',
    icon: Activity,
    color: 'bg-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['Network scans', 'Server inventories', 'Performance data'],
    securityLevel: 'high',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'infrastructure_validator']
  },
  {
    id: 'sensitive',
    title: 'Sensitive Data Assets',
    description: 'Data containing PII, financial, or confidential information',
    icon: Lock,
    color: 'bg-red-500',
    acceptedTypes: ['.csv', '.xlsx'],
    examples: ['Customer data', 'Financial records', 'HR systems'],
    securityLevel: 'maximum',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'pii_detector', 'compliance_checker']
  }
];

// Data Import Validation Agents
const createValidationAgents = (category: string): DataImportAgent[] => {
  const baseAgents = [
    {
      id: 'format_validator',
      name: 'Format Validation Agent',
      role: 'Validates file format, structure, and encoding',
      icon: FileCheck,
      status: 'pending' as const
    },
    {
      id: 'security_scanner',
      name: 'Security Analysis Agent',
      role: 'Scans for malicious content, suspicious patterns',
      icon: Shield,
      status: 'pending' as const
    },
    {
      id: 'privacy_analyzer', 
      name: 'Privacy Protection Agent',
      role: 'Identifies PII, GDPR compliance, data sensitivity',
      icon: UserCheck,
      status: 'pending' as const
    },
    {
      id: 'data_quality_assessor',
      name: 'Data Quality Agent',
      role: 'Assesses data completeness, accuracy, consistency',
      icon: Brain,
      status: 'pending' as const
    }
  ];

  // Add category-specific agents
  const additionalAgents = [];
  if (category === 'app-discovery') {
    additionalAgents.push({
      id: 'dependency_validator',
      name: 'Dependency Analysis Agent',
      role: 'Validates application relationships and dependencies',
      icon: Activity,
      status: 'pending' as const
    });
  }
  
  if (category === 'infrastructure') {
    additionalAgents.push({
      id: 'infrastructure_validator',
      name: 'Infrastructure Analysis Agent',
      role: 'Validates network and server configuration data',
      icon: Monitor,
      status: 'pending' as const
    });
  }
  
  if (category === 'sensitive') {
    additionalAgents.push(
      {
        id: 'pii_detector',
        name: 'PII Detection Agent',
        role: 'Identifies and flags personally identifiable information',
        icon: Eye,
        status: 'pending' as const
      },
      {
        id: 'compliance_checker',
        name: 'Compliance Validation Agent',
        role: 'Ensures regulatory compliance (GDPR, HIPAA, SOX)',
        icon: Scan,
        status: 'pending' as const
      }
    );
  }

  return [...baseAgents, ...additionalAgents];
};

const DataImport: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [validationAgents, setValidationAgents] = useState<DataImportAgent[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  // File upload handling
  const handleFileUpload = useCallback(async (files: File[], categoryId: string) => {
    if (files.length === 0) return;

    const file = files[0];
    const category = uploadCategories.find(c => c.id === categoryId);
    if (!category) return;

    // Create upload file entry
    const uploadFile: UploadFile = {
      id: `upload-${Date.now()}`,
      filename: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      upload_progress: 0,
      validation_progress: 0,
      agents_completed: 0,
      total_agents: category.agents.length,
      security_clearance: false,
      privacy_clearance: false,
      format_validation: false
    };

    setUploadedFiles(prev => [...prev, uploadFile]);

    // Initialize validation agents
    const agents = createValidationAgents(categoryId);
    setValidationAgents(agents);

    try {
      // Simulate file upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, upload_progress: progress }
            : f
        ));
      }

      // Start validation process
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'validating' }
          : f
      ));

      // Execute validation agents sequentially
      for (let i = 0; i < agents.length; i++) {
        const agent = agents[i];
        
        // Update agent status to analyzing
        setValidationAgents(prev => prev.map(a => 
          a.id === agent.id 
            ? { ...a, status: 'analyzing' }
            : a
        ));

        // Simulate agent analysis (in real implementation, this would call backend)
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Simulate agent result (in real implementation, this would be from backend)
        const isSuccess = Math.random() > 0.1; // 90% success rate
        const result = {
          validation: isSuccess ? 'passed' : (Math.random() > 0.5 ? 'warning' : 'failed'),
          message: isSuccess 
            ? `${agent.name} validation passed successfully`
            : `${agent.name} detected potential issues`,
          details: isSuccess 
            ? ['File format valid', 'No security threats detected', 'Data structure correct']
            : ['File format concerns', 'Review required', 'Manual validation needed'],
          confidence: isSuccess ? 0.95 : 0.65
        };

        // Update agent with result
        setValidationAgents(prev => prev.map(a => 
          a.id === agent.id 
            ? { ...a, status: 'completed', result }
            : a
        ));

        // Update file progress
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { 
                ...f, 
                agents_completed: i + 1,
                validation_progress: Math.round(((i + 1) / agents.length) * 100),
                security_clearance: agent.id === 'security_scanner' ? isSuccess : f.security_clearance,
                privacy_clearance: agent.id === 'privacy_analyzer' ? isSuccess : f.privacy_clearance,
                format_validation: agent.id === 'format_validator' ? isSuccess : f.format_validation
              }
            : f
        ));
      }

      // Final validation result
      const allAgentsPassed = agents.every(a => a.result?.validation === 'passed');
      const hasWarnings = agents.some(a => a.result?.validation === 'warning');
      
      const finalStatus = allAgentsPassed ? 'approved' : (hasWarnings ? 'approved' : 'rejected');
      
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: finalStatus }
          : f
      ));

      if (finalStatus === 'approved') {
        toast({
          title: "✅ Data Import Approved",
          description: `${file.name} passed all validation checks and is ready for field mapping.`
        });
      } else {
        toast({
          title: "⚠️ Data Import Issues Detected",
          description: "File validation completed with warnings. Review agent feedback.",
          variant: "destructive"
        });
      }

    } catch (error) {
      console.error('File upload failed:', error);
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'error', error_message: 'Upload failed' }
          : f
      ));
    }
  }, [toast]);

  // Navigate to next step
  const handleProceedToAttributeMapping = useCallback((fileId: string) => {
    const file = uploadedFiles.find(f => f.id === fileId);
    if (file?.status === 'approved') {
      navigate('/discovery/attribute-mapping', {
        state: {
          imported_file: file,
          validation_agents: validationAgents,
          from_data_import: true
        }
      });
    }
  }, [uploadedFiles, validationAgents, navigate]);

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent, categoryId: string) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files, categoryId);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading': return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'validating': return <Brain className="h-5 w-5 animate-pulse text-orange-500" />;
      case 'approved': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'rejected': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'error': return <AlertCircle className="h-5 w-5 text-red-500" />;
      default: return <FileCheck className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploading': return 'bg-blue-100 text-blue-800';
      case 'validating': return 'bg-orange-100 text-orange-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-6xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <Upload className="h-8 w-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Secure Data Import</h1>
            </div>
            <p className="mt-2 text-gray-600 max-w-3xl">
              Upload migration data files for AI-powered validation and security analysis. 
              Our specialized agents ensure data quality, security, and privacy compliance before processing.
            </p>
            
            {/* Security Notice */}
            <Alert className="mt-4 border-blue-200 bg-blue-50">
              <Shield className="h-5 w-5 text-blue-600" />
              <AlertDescription className="text-blue-800">
                <strong>Enterprise Security:</strong> All uploaded data is analyzed by specialized validation agents 
                for format compliance, security threats, privacy protection, and data quality before any processing begins.
              </AlertDescription>
            </Alert>
          </div>

          {/* Upload Categories */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Choose Data Category</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {uploadCategories.map((category) => (
                <Card 
                  key={category.id}
                  className={`relative cursor-pointer transition-all hover:shadow-md border-2 ${
                    selectedCategory === category.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  } ${isDragging ? 'border-dashed border-blue-400 bg-blue-50' : ''}`}
                  onClick={() => setSelectedCategory(category.id)}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, category.id)}
                >
                  <CardHeader>
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${category.color} text-white`}>
                        <category.icon className="h-6 w-6" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{category.title}</CardTitle>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {category.securityLevel} security
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {category.agents.length} validation agents
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <CardDescription className="mt-2">
                      {category.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Accepted formats:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {category.acceptedTypes.map(type => (
                            <Badge key={type} variant="secondary" className="text-xs">
                              {type}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">Examples:</p>
                        <p className="text-sm text-gray-600">{category.examples.join(', ')}</p>
                      </div>
                    </div>
                    
                    {/* File Input */}
                    <div className="mt-4">
                      <input
                        type="file"
                        id={`file-${category.id}`}
                        accept={category.acceptedTypes.join(',')}
                        onChange={(e) => {
                          const files = Array.from(e.target.files || []);
                          handleFileUpload(files, category.id);
                        }}
                        className="hidden"
                      />
                      <Button
                        onClick={() => document.getElementById(`file-${category.id}`)?.click()}
                        variant="outline"
                        className="w-full"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload {category.title}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Upload Progress & Validation */}
          {uploadedFiles.length > 0 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Upload & Validation Status</h2>
              
              {uploadedFiles.map((file) => (
                <Card key={file.id} className="border border-gray-200">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(file.status)}
                        <div>
                          <h3 className="font-medium text-gray-900">{file.filename}</h3>
                          <p className="text-sm text-gray-600">
                            {(file.size / 1024 / 1024).toFixed(2)} MB • {file.type}
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(file.status)}>
                        {file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Upload Progress */}
                    {file.status === 'uploading' && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Uploading file...</span>
                          <span>{file.upload_progress}%</span>
                        </div>
                        <Progress value={file.upload_progress} className="h-2" />
                      </div>
                    )}

                    {/* Validation Progress */}
                    {(file.status === 'validating' || file.status === 'approved' || file.status === 'rejected') && (
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span>Validation Progress</span>
                            <span>{file.agents_completed}/{file.total_agents} agents completed</span>
                          </div>
                          <Progress value={file.validation_progress} className="h-2" />
                        </div>

                        {/* Security Clearances */}
                        <div className="grid grid-cols-3 gap-4">
                          <div className={`p-3 rounded-lg border ${
                            file.format_validation ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                          }`}>
                            <div className="flex items-center space-x-2">
                              <FileCheck className={`h-4 w-4 ${file.format_validation ? 'text-green-600' : 'text-gray-400'}`} />
                              <span className="text-sm font-medium">Format Valid</span>
                            </div>
                          </div>
                          <div className={`p-3 rounded-lg border ${
                            file.security_clearance ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                          }`}>
                            <div className="flex items-center space-x-2">
                              <Shield className={`h-4 w-4 ${file.security_clearance ? 'text-green-600' : 'text-gray-400'}`} />
                              <span className="text-sm font-medium">Security Clear</span>
                            </div>
                          </div>
                          <div className={`p-3 rounded-lg border ${
                            file.privacy_clearance ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                          }`}>
                            <div className="flex items-center space-x-2">
                              <UserCheck className={`h-4 w-4 ${file.privacy_clearance ? 'text-green-600' : 'text-gray-400'}`} />
                              <span className="text-sm font-medium">Privacy Clear</span>
                            </div>
                          </div>
                        </div>

                        {/* Agent Results */}
                        {validationAgents.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-medium text-gray-900">Validation Agent Results</h4>
                            <div className="space-y-2">
                              {validationAgents.map((agent) => (
                                <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                  <div className="flex items-center space-x-3">
                                    <agent.icon className="h-5 w-5 text-gray-600" />
                                    <div>
                                      <p className="font-medium text-gray-900">{agent.name}</p>
                                      <p className="text-sm text-gray-600">{agent.role}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    {agent.status === 'analyzing' && (
                                      <Loader2 className="h-4 w-4 animate-spin text-orange-500" />
                                    )}
                                    {agent.status === 'completed' && agent.result && (
                                      <>
                                        {agent.result.validation === 'passed' && (
                                          <CheckCircle className="h-4 w-4 text-green-500" />
                                        )}
                                        {agent.result.validation === 'warning' && (
                                          <AlertTriangle className="h-4 w-4 text-orange-500" />
                                        )}
                                        {agent.result.validation === 'failed' && (
                                          <AlertCircle className="h-4 w-4 text-red-500" />
                                        )}
                                        <span className="text-sm text-gray-600">
                                          {(agent.result.confidence * 100).toFixed(0)}% confidence
                                        </span>
                                      </>
                                    )}
                                    <Badge 
                                      variant="outline"
                                      className={
                                        agent.status === 'completed' ? 'text-green-700' :
                                        agent.status === 'analyzing' ? 'text-orange-700' :
                                        'text-gray-700'
                                      }
                                    >
                                      {agent.status}
                                    </Badge>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        {file.status === 'approved' && (
                          <div className="flex justify-end space-x-3 pt-4 border-t">
                            <Button
                              onClick={() => handleProceedToAttributeMapping(file.id)}
                              className="bg-blue-600 hover:bg-blue-700"
                            >
                              Proceed to Field Mapping
                              <ArrowRight className="h-4 w-4 ml-2" />
                            </Button>
                          </div>
                        )}

                        {file.status === 'rejected' && (
                          <Alert className="border-red-200 bg-red-50">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <AlertDescription className="text-red-800">
                              File validation failed. Please review agent feedback and upload a corrected file.
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    )}

                    {/* Error State */}
                    {file.status === 'error' && (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertCircle className="h-5 w-5 text-red-600" />
                        <AlertDescription className="text-red-800">
                          {file.error_message || 'An error occurred during upload. Please try again.'}
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Getting Started Guide */}
          {uploadedFiles.length === 0 && (
            <Card className="border border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-900">Getting Started with Secure Data Import</CardTitle>
              </CardHeader>
              <CardContent className="text-blue-800">
                <ol className="list-decimal list-inside space-y-2">
                  <li><strong>Choose data category</strong> based on your file type and security requirements</li>
                  <li><strong>Upload your file</strong> - our validation agents will automatically begin analysis</li>
                  <li><strong>Review validation results</strong> from specialized security and privacy agents</li>
                  <li><strong>Proceed to field mapping</strong> once all validations pass successfully</li>
                </ol>
                <div className="mt-4 p-3 bg-blue-100 rounded-lg">
                  <p className="text-sm">
                    <strong>Security Promise:</strong> Your data never leaves our secure environment and is 
                    analyzed by AI agents that ensure compliance with enterprise security and privacy standards.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataImport;

