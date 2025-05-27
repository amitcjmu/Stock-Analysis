import { useState, useCallback } from 'react';
import { apiCall, API_CONFIG } from '../config/api';
import { FileUpload, AnalysisResult } from '../components/discovery/FileList';

export const useCMDBAnalysis = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const parseCSVData = useCallback((csvContent: string): any[] => {
    const lines = csvContent.trim().split('\n');
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const data = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
      const row: any = {};
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      return row;
    });
    
    return data;
  }, []);

  const readFileContent = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  }, []);

  const analyzeFile = useCallback(async (
    fileUpload: FileUpload,
    onFileUpdate: (id: string, updates: Partial<FileUpload>) => void
  ) => {
    setIsAnalyzing(true);
    onFileUpdate(fileUpload.id, { status: 'analyzing' });

    try {
      // Read and parse file content
      const fileContent = await readFileContent(fileUpload.file);
      console.log('File content read:', fileContent.substring(0, 200) + '...');
      
      const parsedData = parseCSVData(fileContent);
      
      // Call CrewAI analysis API
      const analysis = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ANALYZE_CMDB, {
        method: 'POST',
        body: JSON.stringify({
          filename: fileUpload.file.name,
          content: fileContent,
          fileType: fileUpload.file.type
        })
      });
      
      console.log('Analysis result:', analysis);
      
      // Add raw data to analysis
      analysis.rawData = parsedData;
      
      onFileUpdate(fileUpload.id, {
        status: 'processed',
        analysis: analysis,
        preview: analysis.preview || [],
        editableData: JSON.parse(JSON.stringify(parsedData)) // Deep copy for editing
      });
      
      return analysis;
    } catch (error) {
      console.error('Analysis failed:', error);
      
      const errorAnalysis: AnalysisResult = {
        status: 'error',
        dataQuality: {
          score: 0,
          issues: [`Analysis failed: ${error.message}`],
          recommendations: ['Please check the file format and try again']
        },
        coverage: { applications: 0, servers: 0, databases: 0, dependencies: 0 },
        missingFields: [],
        requiredProcessing: [],
        readyForImport: false
      };
      
      onFileUpdate(fileUpload.id, {
        status: 'error',
        analysis: errorAnalysis
      });
      
      throw error;
    } finally {
      setIsAnalyzing(false);
    }
  }, [readFileContent, parseCSVData]);

  const processData = useCallback(async (
    selectedFile: FileUpload,
    projectInfo: any
  ) => {
    if (!selectedFile || !selectedFile.editableData) {
      throw new Error('No file selected or no data to process');
    }

    setIsProcessing(true);

    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.PROCESS_CMDB, {
        method: 'POST',
        body: JSON.stringify({
          filename: selectedFile.file.name,
          data: selectedFile.editableData,
          projectInfo: projectInfo
        })
      });

      console.log('Processing result:', response);
      return response;
    } catch (error) {
      console.error('Processing failed:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const submitFeedback = useCallback(async (
    filename: string,
    originalAnalysis: AnalysisResult,
    feedbackData: {
      assetTypeCorrection: string;
      analysisCorrections: string;
      additionalComments: string;
    },
    onFileUpdate?: (id: string, updates: Partial<FileUpload>) => void,
    fileId?: string
  ) => {
    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CMDB_FEEDBACK, {
        method: 'POST',
        body: JSON.stringify({
          filename: filename,
          originalAnalysis: originalAnalysis,
          userCorrections: {
            assetType: feedbackData.assetTypeCorrection,
            analysisIssues: feedbackData.analysisCorrections,
            comments: feedbackData.additionalComments
          },
          assetTypeOverride: feedbackData.assetTypeCorrection
        })
      });

      console.log('Feedback submitted successfully:', response);
      
      // If we have an updated analysis and file update callback, update the file
      if (response.updated_analysis && onFileUpdate && fileId) {
        onFileUpdate(fileId, {
          analysis: response.updated_analysis
        });
      }
      
      return response;
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      throw error;
    }
  }, []);

  return {
    isAnalyzing,
    isProcessing,
    analyzeFile,
    processData,
    submitFeedback,
    parseCSVData,
    readFileContent
  };
}; 