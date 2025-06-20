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
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { DataImportValidationService, ValidationAgentResult } from '@/services/dataImportValidationService';
import { apiCall } from '@/config/api';

// Data Import Validation Agents
interface DataImportAgent {
  id: string;
  name: string;
  role: string;
  icon: any;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  result?: ValidationAgentResult;
}

interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'validating' | 'approved' | 'approved_with_warnings' | 'rejected' | 'error';
  agentResults: ValidationAgentResult[];
  validationSessionId?: string;
  importSessionId?: string;
  // Additional progress tracking properties
  upload_progress?: number;
  validation_progress?: number;
  agents_completed?: number;
  total_agents?: number;
  // Security clearance properties
  security_clearance?: boolean;
  privacy_clearance?: boolean;
  format_validation?: boolean;
  agent_results?: ValidationAgentResult[];
  // Error handling
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
  const { user, client, engagement, session, getAuthHeaders } = useAuth();
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [validationAgents, setValidationAgents] = useState<DataImportAgent[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isStartingFlow, setIsStartingFlow] = useState(false); // ✅ Added missing state

  // File upload handling with authentication context
  const handleFileUpload = useCallback(async (files: File[], categoryId: string) => {
    if (files.length === 0) return;

    // Debug authentication state
    console.log('🔍 Upload Debug - Auth State:', {
      user: user ? { id: user.id, role: user.role, name: user.full_name } : null,
      client: client ? { id: client.id, name: client.name } : null,
      engagement: engagement ? { id: engagement.id, name: engagement.name } : null,
      session: session ? { id: session.id } : null,
      categoryId,
      fileCount: files.length
    });

    // For admin users, allow upload even without client/engagement context (demo mode)
    const isAdmin = user?.role === 'admin';
    const hasContext = client && engagement;
    
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in before uploading data.",
        variant: "destructive"
      });
      return;
    }

    if (!hasContext && !isAdmin) {
      toast({
        title: "Context Required",
        description: "Please select a client and engagement before uploading data.",
        variant: "destructive"
      });
      return;
    }

    // Provide demo context for admin users if needed
    const effectiveClient = client || (isAdmin ? { id: 'demo-client', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: 'demo-engagement', name: 'Demo Engagement' } : null);

    if (!effectiveClient || !effectiveEngagement) {
      toast({
        title: "Context Error",
        description: "Unable to determine client/engagement context.",
        variant: "destructive"
      });
      return;
    }

    const file = files[0];
    const category = uploadCategories.find(c => c.id === categoryId);
    if (!category) return;

    // Create upload file entry
    const uploadFile: UploadFile = {
      id: `upload-${Date.now()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'uploading',
      agentResults: [],
      validationSessionId: undefined,
      importSessionId: undefined,
      // Additional progress tracking properties
      upload_progress: undefined,
      validation_progress: undefined,
      agents_completed: undefined,
      total_agents: undefined,
      // Security clearance properties
      security_clearance: undefined,
      privacy_clearance: undefined,
      format_validation: undefined,
      agent_results: undefined,
      // Error handling
      error_message: undefined
    };

    setUploadedFiles(prev => [...prev, uploadFile]);

    // Initialize validation agents
    const agents = createValidationAgents(categoryId);
    setValidationAgents(agents);

    try {
      // Update upload progress to show uploading
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'validating', upload_progress: 100 }
          : f
      ));

      // Start validation process - call real backend
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'validating', upload_progress: 100 }
          : f
      ));

      // Set all agents to analyzing state
      setValidationAgents(prev => prev.map(a => ({ ...a, status: 'analyzing' as const })));

      // Call backend validation service with authentication context
      console.log('🔍 About to call validation service with:', {
        filename: file.name,
        size: file.size,
        type: file.type,
        categoryId,
        effectiveClient: effectiveClient.id,
        effectiveEngagement: effectiveEngagement.id,
        userId: user.id
      });
      
      const validationResponse = await DataImportValidationService.validateFile(file, categoryId, {
        // Include authentication context for agentic flow integration
        client_account_id: effectiveClient.id,
        engagement_id: effectiveEngagement.id,
        user_id: user.id,
        session_id: session?.id || `session-${Date.now()}`,
        headers: getAuthHeaders()
      });
      
      console.log('🔍 Validation service response:', validationResponse);

      if (validationResponse.success) {
        // Update agents with real results from backend
        const backendAgentResults = validationResponse.agent_results;
        
                 // Map backend results to frontend agent format
         const updatedAgents: DataImportAgent[] = agents.map(agent => {
           const backendResult = backendAgentResults.find(r => r.agent_id === agent.id);
           if (backendResult) {
             return {
               ...agent,
               status: 'completed' as const,
               result: backendResult
             };
           }
           return { ...agent, status: 'completed' as const };
         });

        setValidationAgents(updatedAgents);

        // Update file with final results
        const finalStatus = validationResponse.file_status;
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { 
                ...f, 
                status: finalStatus,
                validation_progress: 100,
                agents_completed: backendAgentResults.length,
                security_clearance: validationResponse.security_clearances.security_clearance,
                privacy_clearance: validationResponse.security_clearances.privacy_clearance,
                format_validation: validationResponse.security_clearances.format_validation,
                validation_session_id: validationResponse.validation_session.file_id,
                agent_results: backendAgentResults
              }
            : f
        ));

        // 🔧 DATA PERSISTENCE FIX: Store validated data to database
        if (finalStatus === 'approved' || finalStatus === 'approved_with_warnings') {
          try {
            console.log('🗄️ Persisting validated data to database...');
            
            // Parse CSV data for storage
            const csvData = await parseCsvData(file);
            
            if (csvData.length > 0) {
              const importSessionId = await storeImportData(
                csvData, 
                file, 
                validationResponse.validation_session.file_id
              );
              
              if (importSessionId) {
                // Update file with import session ID
                setUploadedFiles(prev => prev.map(f => 
                  f.id === uploadFile.id 
                    ? { ...f, importSessionId: importSessionId }
                    : f
                ));
                
                console.log('✅ Data persistence completed:', {
                  importSessionId,
                  recordCount: csvData.length,
                  validationSessionId: validationResponse.validation_session.file_id
                });
                
                toast({
                  title: "✅ Data Stored Successfully", 
                  description: `${csvData.length} records stored in database and ready for field mapping.`,
                });
              } else {
                console.warn('⚠️ Data validation passed but storage failed');
                toast({
                  title: "⚠️ Storage Warning",
                  description: "Data validated but storage encountered issues. You can still proceed to field mapping.",
                  variant: "destructive"
                });
              }
            }
          } catch (storageError) {
            console.error('❌ Data storage error:', storageError);
            toast({
              title: "⚠️ Storage Error",
              description: "Data validated but storage failed. Please try uploading again or contact support.",
              variant: "destructive"
            });
          }
        }

        // Show appropriate toast message
        if (finalStatus === 'approved') {
          toast({
            title: "✅ Data Import Approved",
            description: `${file.name} passed all validation checks and is ready for field mapping.`
          });
        } else if (finalStatus === 'approved_with_warnings') {
          toast({
            title: "⚠️ Data Import Approved with Warnings",
            description: "File validation completed with warnings. Review agent feedback before proceeding.",
            variant: "default"
          });
        } else {
          toast({
            title: "❌ Data Import Rejected",
            description: "File validation failed. Review agent feedback to understand the issues.",
            variant: "destructive"
          });
        }
      } else {
        throw new Error('Validation service returned unsuccessful response');
      }

    } catch (error) {
      console.error('File validation failed:', error);
      
      // Set all agents to failed state
      setValidationAgents(prev => prev.map(a => ({ ...a, status: 'failed' as const })));
      
      // Update file with error
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'error', 
              error_message: error instanceof Error ? error.message : 'Validation failed'
            }
          : f
      ));

      toast({
        title: "🚨 Validation Failed",
        description: error instanceof Error ? error.message : "An unknown error occurred during validation.",
        variant: "destructive"
      });
    }
  }, [toast, client, engagement, user, session, getAuthHeaders]);

  // ✅ FIXED: Trigger CrewAI Discovery Flow directly with uploaded data
  const handleProceedToMapping = useCallback(async (fileId: string) => {
    const file = uploadedFiles.find(f => f.id === fileId);
    if (!file || (file.status !== 'approved' && file.status !== 'approved_with_warnings')) {
      return;
    }

    const isAdmin = user?.role === 'admin';
    const effectiveClient = client || (isAdmin ? { id: 'demo-client', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: 'demo-engagement', name: 'Demo Engagement' } : null);
    
    if (!effectiveClient || !effectiveEngagement || !user) {
      toast({
        title: "Context Required",
        description: "Please ensure client, engagement, and user context is available.",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsStartingFlow(true);
      
             // Get the stored data for CrewAI flow (already validated and stored)
       console.log('🔍 DEBUG: file.importSessionId =', file.importSessionId);
       const csvData = await getStoredImportData(file.importSessionId);
       console.log('🔍 DEBUG: csvData.length =', csvData.length);
      
      if (csvData.length === 0) {
        console.warn('❌ No data retrieved from getStoredImportData');
        toast({
          title: "No Data Found",
          description: `Import session ID: ${file.importSessionId}. The uploaded file appears to be empty or the data wasn't stored properly. Please try uploading again.`,
          variant: "destructive"
        });
        setIsStartingFlow(false);
        return;
      }

      console.log('🚀 Starting CrewAI Discovery Flow with:', {
        filename: file.name,
        records: csvData.length,
        client: effectiveClient.id,
        engagement: effectiveEngagement.id,
        user: user.id
      });

      // Call the CrewAI Discovery Flow endpoint directly
      const discoveryFlowResponse = await apiCall('/discovery/flow/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          headers: Object.keys(csvData[0] || {}),
          sample_data: csvData,
          filename: file.name,
          options: {
            enable_parallel_execution: true,
            enable_retry_logic: true,
            max_retries: 3,
            timeout_seconds: 300,
            client_account_id: effectiveClient.id,
            engagement_id: effectiveEngagement.id,
            user_id: user.id,
            validation_session_id: file.validationSessionId,
            import_session_id: file.importSessionId
          }
        })
      });

      if (discoveryFlowResponse.status === 'success') {
        console.log('✅ CrewAI Discovery Flow started:', discoveryFlowResponse);
        
        toast({
          title: "🚀 Discovery Flow Started",
          description: `Flow ${discoveryFlowResponse.session_id} initialized with ${csvData.length} records. Proceeding to field mapping...`,
        });

        // Navigate to Attribute Mapping with flow session data
        navigate('/discovery/attribute-mapping', {
          state: {
            file_id: fileId,
            filename: file.name,
            validation_session_id: file.validationSessionId,
            import_session_id: file.importSessionId,
            flow_session_id: discoveryFlowResponse.session_id, // ✅ CrewAI flow session ID
            flow_id: discoveryFlowResponse.flow_id,
            raw_data: csvData, // ✅ Include actual uploaded data
            upload_context: {
              category: selectedCategory,
              timestamp: file.uploadedAt.toISOString(),
              user_id: user.id,
              client_id: effectiveClient.id,
              engagement_id: effectiveEngagement.id,
              session_id: session?.id
            }
          }
        });
      } else {
        throw new Error(discoveryFlowResponse.message || 'Failed to start discovery flow');
      }
      
    } catch (error) {
      console.error('❌ Failed to start Discovery Flow:', error);
      toast({
        title: "Discovery Flow Failed",
        description: error instanceof Error ? error.message : 'Failed to start discovery flow',
        variant: "destructive"
      });
    } finally {
      setIsStartingFlow(false);
    }
  }, [uploadedFiles, selectedCategory, navigate, user, client, engagement, session, toast]);

  // Helper function to get stored import data
  const getStoredImportData = async (importSessionId: string | undefined): Promise<any[]> => {
    console.log('🔍 getStoredImportData called with:', importSessionId);
    
    if (!importSessionId) {
      console.warn('❌ No import session ID provided');
      return [];
    }
    
    try {
      console.log('🔍 Making API call to:', `/data-import/import/${importSessionId}`);
      
      const response = await apiCall(`/data-import/import/${importSessionId}`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      console.log('🔍 API response:', response);
      
      if (response.success && response.data) {
        console.log('✅ Retrieved data:', response.data.length, 'records');
        return response.data;
      } else {
        console.warn('❌ No stored data found for import session:', importSessionId, 'Response:', response);
        return [];
      }
    } catch (error) {
      console.error('❌ Error retrieving stored import data:', error);
      return [];
    }
  };

  // Helper function to parse CSV data
  const parseCsvData = async (file: File): Promise<any[]> => {
    const text = await file.text();
    const lines = text.split('\\n').filter(line => line.trim());
    if (lines.length <= 1) return [];
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/\"/g, ''));
    return lines.slice(1).map((line, index) => {
      const values = line.split(',').map(v => v.trim().replace(/\"/g, ''));
      const record: any = { row_index: index + 1 };
      headers.forEach((header, headerIndex) => {
        record[header] = values[headerIndex] || '';
      });
      return record;
    });
  };

  // Helper function to store import data in database
  const storeImportData = async (csvData: any[], file: File, sessionId: string): Promise<string | null> => {
    try {
      console.log('🗄️ Storing import data in database...', {
        records: csvData.length,
        filename: file.name,
        sessionId
      });
      
      const storeResult = await apiCall('/data-import/store-import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_data: csvData,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type
          },
          upload_context: {
            intended_type: selectedCategory,
            validation_session_id: sessionId,
            upload_timestamp: new Date().toISOString()
          }
        })
      });
      
      if (storeResult.success) {
        console.log('✅ Import data stored successfully:', storeResult);
        return storeResult.import_session_id;
      } else {
        console.warn('⚠️ Failed to store import data:', storeResult);
        return null;
      }
    } catch (storeError) {
      console.error('❌ Error storing import data:', storeError);
      return null;
    }
  };

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
      case 'approved_with_warnings': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
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
      case 'approved_with_warnings': return 'bg-yellow-100 text-yellow-800';
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
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Upload className="h-8 w-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Secure Data Import</h1>
              </div>
              
              {/* Authentication Context Status */}
              <div className="flex items-center space-x-3">
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                  client && engagement ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  <Activity className="h-4 w-4" />
                  <span>
                    {client && engagement 
                      ? `${client.name} • ${engagement.name}` 
                      : 'Select Client & Engagement'
                    }
                  </span>
                </div>
                {user && (
                  <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    <span>{user.full_name}</span>
                  </div>
                )}
              </div>
            </div>
            <p className="mt-2 text-gray-600 max-w-3xl">
              Upload migration data files for AI-powered validation and security analysis. 
              Our specialized agents ensure data quality, security, and privacy compliance before processing.
            </p>
            
            {/* Authentication Context Warning */}
            {(!client || !engagement) && (
              <Alert className="mt-4 border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  <strong>Context Required:</strong> Please select a client and engagement using the context selector above 
                  before uploading data. This ensures proper data isolation and agentic flow integration.
                </AlertDescription>
              </Alert>
            )}

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
                          console.log('🔍 File Input Change Event:', {
                            categoryId: category.id,
                            files: e.target.files,
                            fileCount: e.target.files?.length || 0
                          });
                          const files = Array.from(e.target.files || []);
                          if (files.length > 0) {
                            console.log('🔍 Calling handleFileUpload with:', files[0].name);
                            handleFileUpload(files, category.id);
                          } else {
                            console.log('🔍 No files selected');
                          }
                        }}
                        className="hidden"
                      />
                      <Button
                        onClick={() => {
                          console.log('🔍 Upload Button Clicked:', {
                            categoryId: category.id,
                            categoryTitle: category.title,
                            inputElement: document.getElementById(`file-${category.id}`)
                          });
                          document.getElementById(`file-${category.id}`)?.click();
                        }}
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
                          <h3 className="font-medium text-gray-900">{file.name}</h3>
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
                    {(file.status === 'validating' || file.status === 'approved' || file.status === 'approved_with_warnings' || file.status === 'rejected') && (
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
                        {(file.status === 'approved' || file.status === 'approved_with_warnings') && (
                          <div className="pt-4 border-t">
                            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
                              <div>
                                <p className="text-sm font-medium text-gray-900">Ready for Discovery Flow</p>
                                <p className="text-sm text-gray-600">
                                  Data validation complete. Proceed to field mapping and AI-powered analysis.
                                </p>
                              </div>
                              <Button
                                onClick={() => handleProceedToMapping(file.id)}
                                disabled={isStartingFlow}
                                className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
                              >
                                {isStartingFlow ? (
                                  <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span>Starting Flow...</span>
                                  </>
                                ) : (
                                  <>
                                    <Brain className="h-4 w-4" />
                                    <span>Start Discovery Flow</span>
                                    <ArrowRight className="h-4 w-4" />
                                  </>
                                )}
                              </Button>
                            </div>
                          </div>
                        )}

                        {file.status === 'approved_with_warnings' && (
                          <Alert className="border-yellow-200 bg-yellow-50">
                            <AlertTriangle className="h-5 w-5 text-yellow-600" />
                            <AlertDescription className="text-yellow-800">
                              File validation completed with warnings. Review agent feedback before proceeding to field mapping.
                            </AlertDescription>
                          </Alert>
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

