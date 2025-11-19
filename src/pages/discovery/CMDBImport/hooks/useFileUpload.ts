import { useState } from 'react'
import { useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '@/config/api';
import { parseCsvFile, type CsvRecord } from '@/utils/csvParser';
import type { UploadFile } from '../CMDBImport.types';

export const useFileUpload = (): JSX.Element => {
  const { toast } = useToast();
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const storeImportData = useCallback(async (
    csvData: CsvRecord[],
    file: File,
    uploadId: string,
    categoryId: string
  ): Promise<{import_flow_id: string | null, flow_id: string | null}> => {
    if (!uploadId) {
      console.error('No upload ID available for storing data.');
      return { import_flow_id: null, flow_id: null };
    }

    // Use effective client and engagement (same logic as handleFileUpload)
    const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';
    const effectiveClient = client || (isAdmin ? { id: '11111111-1111-1111-1111-111111111111', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: '22222222-2222-2222-2222-222222222222', name: 'Demo Engagement' } : null);

    try {
      console.log(`Storing data for upload: ${uploadId}`);
      console.log('Using effective context:', {
        client: effectiveClient?.id,
        engagement: effectiveEngagement?.id
      });

      const response = await apiCall(`/data-import/store-import`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
          // Add effective client and engagement to headers for admin users
          ...(effectiveClient?.id && { 'X-Client-Account-ID': effectiveClient.id }),
          ...(effectiveEngagement?.id && { 'X-Engagement-ID': effectiveEngagement.id })
        },
        timeout: null, // allow long-running server-side processing without client abort
        body: JSON.stringify({
          file_data: csvData,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type,
          },
          upload_context: {
            intended_type: categoryId,
            validation_upload_id: uploadId,
            upload_timestamp: new Date().toISOString(),
          },
          client_id: effectiveClient?.id || null,
          engagement_id: effectiveEngagement?.id || null,
        }),
      });

      console.log('📡 Store import response:', JSON.stringify(response, null, 2));
      console.log('📡 Response type:', typeof response);
      console.log('📡 Response.success type:', typeof response?.success);
      console.log('📡 Response.success value:', response?.success);

      if (response && response.success === true) {
        console.log('✅ Data stored successfully, import flow ID:', response.import_flow_id);
        console.log('✅ CrewAI Flow ID:', response.flow_id);
        console.log('✅ Full response data:', response);

        // Make sure we're returning the correct flow_id
        // Backend returns flow_id (the master flow ID) and import_flow_id (should be same as flow_id)
        // Use flow_id which is the master flow ID for the discovery flow
        const flowId = response.flow_id || response.import_flow_id || response.crewai_flow_id || response.discovery_flow_id || response.crew_flow_id;
        console.log('🎯 Using flow ID (master flow):', flowId);
        console.log('📡 Full backend response for flow tracking:', {
          import_flow_id: response.import_flow_id,
          crew_flow_id: response.crew_flow_id,
          flow_id: flowId,
          all_flow_fields: {
            flow_id: response.flow_id,
            crew_flow_id: response.crew_flow_id,
            crewai_flow_id: response.crewai_flow_id,
            discovery_flow_id: response.discovery_flow_id,
            import_flow_id: response.import_flow_id
          }
        });

        return {
          import_flow_id: response.data_import_id,  // The actual import ID
          flow_id: flowId  // The master flow ID for status polling
        };
      } else {
        console.error('❌ Failed to store data - response not successful');
        console.error('❌ Response details:', {
          success: response?.success,
          error: response?.error,
          message: response?.message,
          fullResponse: response
        });
        throw new Error(response?.message || response?.error || 'Failed to store data - backend returned success: false');
      }
    } catch (error) {
      console.error('❌ Error storing data:', error);
      console.error('❌ Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
        error: error
      });
      // Re-throw the error so it can be caught by the parent handler
      throw error;
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

    // Provide demo context for admin users if needed (use proper UUIDs)
    const effectiveClient = client || (isAdmin ? { id: '11111111-1111-1111-1111-111111111111', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: '22222222-2222-2222-2222-222222222222', name: 'Demo Engagement' } : null);

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
      const parseResult = await parseCsvFile(file);
      const csvData = parseResult.records;
      const cleansing_stats = parseResult.cleansing_stats;

      if (csvData.length === 0) {
        throw new Error("No valid data found in the CSV file");
      }

      console.log(`Parsed ${csvData.length} records from CSV file`);

      // Alert user if data cleansing occurred (commas replaced with spaces)
      if (cleansing_stats?.rows_cleansed > 0) {
        toast({
          title: "Data Cleansing Applied",
          description: `Unquoted commas in text fields were replaced with spaces to ensure column alignment with imported data. ${cleansing_stats.rows_cleansed} row(s) were cleaned.`,
          variant: "default",
        });
      }

      // Generate a proper UUID for the upload
      const uploadId = uuidv4();

      // Store data and trigger UnifiedDiscoveryFlow directly
      console.log('Storing data and triggering UnifiedDiscoveryFlow with validation_upload_id:', uploadId);

      const payload = {
        file_data: csvData,
        metadata: {
          filename: file.name,
          size: file.size,
          type: file.type,
        },
        upload_context: {
          intended_type: categoryId,
          validation_upload_id: uploadId,
          upload_timestamp: new Date().toISOString(),
        },
        client_id: effectiveClient?.id || null,
        engagement_id: effectiveEngagement?.id || null,
        cleansing_stats: cleansing_stats ? {
          total_rows: cleansing_stats.total_rows,
          rows_cleansed: cleansing_stats.rows_cleansed,
          rows_skipped: cleansing_stats.rows_skipped,
        } : undefined,
      };

      // AGGRESSIVE DEBUGGING: Log payload and types
      console.log('Final Payload:', JSON.stringify(payload, null, 2));
      console.log('Payload Field Types:', {
        'metadata.filename': typeof payload.metadata.filename,
        'metadata.size': typeof payload.metadata.size,
        'metadata.type': typeof payload.metadata.type,
        'upload_context.intended_type': typeof payload.upload_context.intended_type,
        'upload_context.validation_upload_id': typeof payload.upload_context.validation_upload_id,
        'upload_context.upload_timestamp': typeof payload.upload_context.upload_timestamp,
        'client_id': typeof payload.client_id,
        'engagement_id': typeof payload.engagement_id,
        'file_data_length': payload.file_data.length,
      });


      const { import_flow_id, flow_id } = await storeImportData(csvData, file, uploadId, categoryId);

      console.log('🔍 Flow IDs returned from storeImportData:', {
        import_flow_id,
        flow_id,
        flow_id_type: typeof flow_id,
        flow_id_truthy: !!flow_id
      });

      if (flow_id) {
        const recordCount = csvData.length;

        console.log('🔧 Setting flow_id on uploaded file:', {
          fileId: newFile.id,
          fileName: newFile.name,
          flow_id: flow_id,
          import_flow_id: import_flow_id
        });

        // Success - UnifiedDiscoveryFlow was triggered - START PROCESSING TRACKING
        setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? {
          ...f,
          status: 'processing',  // Changed from 'approved' to 'processing'
          importFlowId: import_flow_id || undefined,
          flow_id: flow_id,
          discovery_progress: 0,
          current_phase: 'data_import',
          flow_status: 'running',
          // Will be populated by agent insights via flow status updates
          security_clearance: undefined,  // Will be populated by agents
          privacy_clearance: undefined,   // Will be populated by agents
          format_validation: true,
          flow_summary: {
            total_assets: recordCount,
            errors: 0,
            warnings: 0,  // Will be updated by agents
            phases_completed: ['data_import'],
            agent_insights: []  // Will be populated via flow status
          },
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
        throw new Error("Failed to trigger UnifiedDiscoveryFlow - no flow ID returned. Check backend logs for validation errors on /data-import/store-import.");
      }

    } catch (error) {
      console.error("File upload and flow trigger error:", error);
      console.error("🔥 Detailed error information:", {
        errorType: error?.constructor?.name,
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        isApiError: error?.isApiError,
        status: error?.status,
        response: error?.response,
        fullError: error
      });

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
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(Array.from(e.dataTransfer.files), categoryId);
      e.dataTransfer.clearData();
    }
  }, [handleFileUpload]);


  return {
    uploadedFiles,
    setUploadedFiles,
    selectedCategory,
    setSelectedCategory,
    isDragging,
    onFileUpload: handleFileUpload,
    onDragOver: handleDragOver,
    onDragLeave: handleDragLeave,
    onDrop: handleDrop,
  };
};
