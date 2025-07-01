import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '@/config/api';
import { UploadFile } from '../CMDBImport.types';

export const useFileUpload = () => {
  const { toast } = useToast();
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const parseCsvData = useCallback(async (file: File): Promise<any[]> => {
    const text = await file.text();
    const lines = text.split('\n').filter(line => line.trim());
    console.log(`🔍 DEBUG: Parsed ${lines.length} lines from CSV file`);
    if (lines.length <= 1) {
      console.warn('🚨 DEBUG: CSV file has no data rows or only header');
      return [];
    }
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/\"/g, ''));
    const records = lines.slice(1).map((line, index) => {
      const values = line.split(',').map(v => v.trim().replace(/\"/g, ''));
      const record: any = { row_index: index + 1 };
      headers.forEach((header, headerIndex) => {
        record[header] = values[headerIndex] || '';
      });
      return record;
    });
    
    console.log(`🔍 DEBUG: Parsed ${records.length} data records from CSV`);
    console.log(`🔍 DEBUG: Headers: ${headers.join(', ')}`);
    if (records.length > 0) {
      console.log(`🔍 DEBUG: First record sample:`, records[0]);
    }
    
    return records;
  }, []);

  const storeImportData = useCallback(async (
    csvData: any[], 
    file: File, 
    sessionId: string, 
    categoryId: string
  ): Promise<{import_session_id: string | null, flow_id: string | null}> => {
    if (!sessionId) {
      console.error('No session ID available for storing data.');
      return { import_session_id: null, flow_id: null };
    }

    // Use effective client and engagement (same logic as handleFileUpload)
    const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';
    const effectiveClient = client || (isAdmin ? { id: 'demo-client', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: 'demo-engagement', name: 'Demo Engagement' } : null);

    try {
      console.log(`Storing data for session: ${sessionId}`);
      console.log('Using effective context:', { 
        client: effectiveClient?.id, 
        engagement: effectiveEngagement?.id 
      });
      
      const response = await apiCall(`/data-import/store-import`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_data: csvData,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type,
          },
          upload_context: {
            intended_type: categoryId,
            validation_session_id: sessionId,
            upload_timestamp: new Date().toISOString(),
          },
          client_id: effectiveClient?.id || null,
          engagement_id: effectiveEngagement?.id || null,
        }),
      });

      console.log('📡 Store import response:', JSON.stringify(response, null, 2));
      
      if (response.success) {
        console.log('✅ Data stored successfully, import session ID:', response.import_session_id);
        console.log('✅ CrewAI Flow ID:', response.flow_id);
        console.log('✅ Full response data:', response);
        
        // Make sure we're returning the correct flow_id
        const flowId = response.flow_id || response.crewai_flow_id || response.discovery_flow_id;
        console.log('🎯 Using flow ID:', flowId);
        
        return { 
          import_session_id: response.import_session_id,
          flow_id: flowId
        };
      } else {
        console.error('❌ Failed to store data:', response.error);
        return { import_session_id: null, flow_id: null };
      }
    } catch (error: any) {
      console.error('❌ Error storing data:', error);
      return { import_session_id: null, flow_id: null };
    }
  }, [user, client, engagement, getAuthHeaders]);

  const handleFileUpload = useCallback(async (files: File[], categoryId: string) => {
    if (files.length === 0) return;

    // Debug authentication state
    console.log('🔍 Upload Debug - Auth State:', {
      user: user ? { id: user.id, role: user.role, name: user.full_name } : null,
      client: client ? { id: client.id, name: client.name } : null,
      engagement: engagement ? { id: engagement.id, name: engagement.name } : null,
      categoryId,
      fileCount: files.length
    });

    // For admin users, allow upload even without client/engagement context (demo mode)
    const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';
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
    const newFile: UploadFile = {
      id: `${file.name}-${new Date().toISOString()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'uploading',
      agentResults: [],
      upload_progress: 0,
    };

    setUploadedFiles([newFile]);
    setSelectedCategory(categoryId);

    try {
      // Update to processing status
      setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? { 
        ...f, 
        status: 'validating', 
        upload_progress: 100 
      } : f));
      
      // Parse CSV data
      const csvData = await parseCsvData(file);
      
      if (csvData.length === 0) {
        throw new Error("No valid data found in the CSV file");
      }

      console.log(`Parsed ${csvData.length} records from CSV file`);
      
      // Generate a proper UUID for the upload session
      const tempSessionId = crypto.randomUUID();
      
      // Store data and trigger UnifiedDiscoveryFlow directly
      console.log('Storing data and triggering UnifiedDiscoveryFlow...');
      const { import_session_id, flow_id } = await storeImportData(csvData, file, tempSessionId, categoryId);
      
      if (flow_id) {
        // Success - UnifiedDiscoveryFlow was triggered - START PROCESSING TRACKING
        setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? { 
          ...f, 
          status: 'processing',  // Changed from 'approved' to 'processing'
          importSessionId: import_session_id || undefined,
          flow_id: flow_id,
          discovery_progress: 0,
          current_phase: 'data_import',
          flow_status: 'running',
          agentResults: [{
            agent_id: 'unified_flow',
            agent_name: 'UnifiedDiscoveryFlow',
            validation: 'passed',
            confidence: 1.0,
            message: 'CrewAI Discovery Flow initiated - processing in progress',
            timestamp: new Date().toISOString(),
            details: [
              `Successfully uploaded ${csvData.length} records`,
              'UnifiedDiscoveryFlow started with CrewAI agents',
              'Real-time progress tracking enabled'
            ]
          }]
        } : f));
        
        toast({
          title: "Discovery Flow Started",
          description: `File uploaded successfully. CrewAI agents are now processing ${csvData.length} records.`,
        });
        
      } else {
        throw new Error("Failed to trigger UnifiedDiscoveryFlow - no flow ID returned");
      }
      
    } catch (error) {
      console.error("File upload and flow trigger error:", error);
      const errorMessage = (error instanceof Error) ? error.message : "An unknown error occurred.";
      setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? { 
        ...f, 
        status: 'error', 
        error_message: errorMessage 
      } : f));
      toast({
        title: "Upload Failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  }, [user, client, engagement, toast, parseCsvData, storeImportData]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, categoryId: string) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files, categoryId);
  }, [handleFileUpload]);

  return {
    uploadedFiles,
    setUploadedFiles,
    selectedCategory,
    setSelectedCategory,
    isDragging,
    handleFileUpload,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    parseCsvData,
    storeImportData
  };
};