import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { apiCall, API_CONFIG } from '../../config/api';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Download,
  Eye,
  Brain,
  Database,
  Loader,
  FileSpreadsheet,
  AlertCircle,
  RefreshCw,
  Edit3,
  Save,
  Plus,
  Trash2,
  FolderPlus
} from 'lucide-react';

interface AnalysisResult {
  status: 'analyzing' | 'completed' | 'error';
  dataQuality: {
    score: number;
    issues: string[];
    recommendations: string[];
  };
  coverage: {
    applications: number;
    servers: number;
    databases: number;
    dependencies: number;
  };
  missingFields: string[];
  requiredProcessing: string[];
  readyForImport: boolean;
  rawData?: any[];
}

interface FileUpload {
  file: File;
  id: string;
  status: 'uploaded' | 'analyzing' | 'processed' | 'error';
  analysis?: AnalysisResult;
  preview?: any[];
  editableData?: any[];
}

interface ProjectInfo {
  name: string;
  description: string;
  saveToDatabase: boolean;
}

const CMDBImport = () => {
  const [uploadedFiles, setUploadedFiles] = useState<FileUpload[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [projectInfo, setProjectInfo] = useState<ProjectInfo>({
    name: '',
    description: '',
    saveToDatabase: false
  });
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [feedbackData, setFeedbackData] = useState({
    assetTypeCorrection: '',
    analysisCorrections: '',
    additionalComments: ''
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'uploaded' as const
    }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    // Auto-analyze the first file
    if (newFiles.length > 0) {
      analyzeFile(newFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json']
    },
    multiple: true
  });

  const analyzeFile = async (fileUpload: FileUpload) => {
    setIsAnalyzing(true);
    setUploadedFiles(prev => 
      prev.map(f => f.id === fileUpload.id ? { ...f, status: 'analyzing' } : f)
    );

    try {
      // Simulate file reading and analysis
      const fileContent = await readFileContent(fileUpload.file);
      console.log('File content read:', fileContent.substring(0, 200) + '...');
      
      // Parse CSV data for editing
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
      
      setUploadedFiles(prev => 
        prev.map(f => f.id === fileUpload.id ? { 
          ...f, 
          status: 'processed',
          analysis: analysis,
          preview: analysis.preview || [],
          editableData: JSON.parse(JSON.stringify(parsedData)) // Deep copy for editing
        } : f)
      );
    } catch (error) {
      console.error('Analysis failed:', error);
      setUploadedFiles(prev => 
        prev.map(f => f.id === fileUpload.id ? { 
          ...f, 
          status: 'error',
          analysis: {
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
          }
        } : f)
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const parseCSVData = (csvContent: string): any[] => {
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
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const handleCellEdit = (rowIndex: number, field: string, value: string) => {
    if (!selectedFile || !selectedFile.editableData) return;
    
    const updatedData = [...selectedFile.editableData];
    updatedData[rowIndex][field] = value;
    
    setSelectedFile({
      ...selectedFile,
      editableData: updatedData
    });
  };

  const addMissingField = (fieldName: string) => {
    if (!selectedFile || !selectedFile.editableData) return;
    
    const updatedData = selectedFile.editableData.map(row => ({
      ...row,
      [fieldName]: ''
    }));
    
    setSelectedFile({
      ...selectedFile,
      editableData: updatedData
    });
  };

  const processData = async () => {
    if (!selectedFile || !selectedFile.editableData) return;
    
    if (projectInfo.saveToDatabase && !projectInfo.name.trim()) {
      setShowProjectDialog(true);
      return;
    }
    
    setIsProcessing(true);
    
    try {
      const processedData = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.PROCESS_CMDB, {
        method: 'POST',
        body: JSON.stringify({
          filename: selectedFile.file.name,
          data: selectedFile.editableData,
          projectInfo: projectInfo.saveToDatabase ? projectInfo : null
        })
      });
      
      console.log('Data processed successfully:', processedData);
      
      // Update the file status
      setUploadedFiles(prev => 
        prev.map(f => f.id === selectedFile.id ? {
          ...f,
          analysis: {
            ...f.analysis!,
            readyForImport: true,
            dataQuality: {
              ...f.analysis!.dataQuality,
              score: 95 // Improved score after processing
            }
          }
        } : f)
      );
      
      // Update selected file
      setSelectedFile(prev => prev ? {
        ...prev,
        analysis: {
          ...prev.analysis!,
          readyForImport: true,
          dataQuality: {
            ...prev.analysis!.dataQuality,
            score: 95
          }
        }
      } : null);
      
      setIsEditing(false);
      alert('Data processed successfully!');
      
    } catch (error) {
      console.error('Processing failed:', error);
      alert('Processing failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const submitFeedback = async () => {
    if (!selectedFile || !selectedFile.analysis) return;
    
    try {
      const feedbackPayload = {
        filename: selectedFile.file.name,
        originalAnalysis: selectedFile.analysis,
        userCorrections: {
          assetType: feedbackData.assetTypeCorrection,
          analysisIssues: feedbackData.analysisCorrections,
          comments: feedbackData.additionalComments
        },
        assetTypeOverride: feedbackData.assetTypeCorrection || null
      };
      
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CMDB_FEEDBACK, {
        method: 'POST',
        body: JSON.stringify(feedbackPayload)
      });
      
      console.log('Feedback submitted successfully:', result);
      alert('Thank you for your feedback! This will help improve future analysis.');
      setShowFeedbackDialog(false);
      setFeedbackData({
        assetTypeCorrection: '',
        analysisCorrections: '',
        additionalComments: ''
      });
      
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <FileText className="h-5 w-5 text-blue-500" />;
      case 'analyzing':
        return <Loader className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getAllFields = () => {
    if (!selectedFile || !selectedFile.editableData || selectedFile.editableData.length === 0) return [];
    return Object.keys(selectedFile.editableData[0]);
  };

  const getMissingFieldsNotInData = () => {
    if (!selectedFile || !selectedFile.analysis) return [];
    const currentFields = getAllFields();
    return selectedFile.analysis.missingFields.filter(field => !currentFields.includes(field));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">CMDB Data Import</h1>
              <p className="text-lg text-gray-600">
                Import and analyze your CMDB data with AI-powered validation and processing
              </p>
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>AI Analysis:</strong> Our CrewAI agents will validate data quality, identify missing information, and recommend processing steps
                </p>
              </div>
            </div>

            {/* Upload Area */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload CMDB Files</h2>
              
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                {isDragActive ? (
                  <p className="text-lg text-blue-600">Drop the files here...</p>
                ) : (
                  <div>
                    <p className="text-lg text-gray-600 mb-2">
                      Drag & drop CMDB files here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports CSV, Excel (.xlsx, .xls), and JSON formats
                    </p>
                  </div>
                )}
              </div>

              {/* Supported Formats */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <FileSpreadsheet className="h-4 w-4" />
                  <span>CSV Files</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <FileSpreadsheet className="h-4 w-4" />
                  <span>Excel Files</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <FileText className="h-4 w-4" />
                  <span>JSON Files</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Database className="h-4 w-4" />
                  <span>CMDB Exports</span>
                </div>
              </div>
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Uploaded Files</h2>
                
                <div className="space-y-4">
                  {uploadedFiles.map((fileUpload) => (
                    <div key={fileUpload.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(fileUpload.status)}
                          <div>
                            <h3 className="font-medium text-gray-900">{fileUpload.file.name}</h3>
                            <p className="text-sm text-gray-500">
                              {(fileUpload.file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {fileUpload.status === 'processed' && (
                            <>
                              <button
                                onClick={() => setSelectedFile(fileUpload)}
                                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                              >
                                <Eye className="h-4 w-4 inline mr-1" />
                                View Analysis
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedFile(fileUpload);
                                  setIsEditing(true);
                                }}
                                className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200"
                              >
                                <Edit3 className="h-4 w-4 inline mr-1" />
                                Edit Data
                              </button>
                            </>
                          )}
                          {fileUpload.status === 'uploaded' && (
                            <button
                              onClick={() => analyzeFile(fileUpload)}
                              className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200"
                            >
                              <Brain className="h-4 w-4 inline mr-1" />
                              Analyze
                            </button>
                          )}
                        </div>
                      </div>

                      {fileUpload.analysis && (
                        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                          <div className="text-center">
                            <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getQualityColor(fileUpload.analysis.dataQuality.score)}`}>
                              Data Quality: {fileUpload.analysis.dataQuality.score}%
                            </div>
                          </div>
                          <div className="text-center">
                            <span className="text-sm text-gray-600">Applications: </span>
                            <span className="font-medium">{fileUpload.analysis.coverage.applications}</span>
                          </div>
                          <div className="text-center">
                            <span className="text-sm text-gray-600">Servers: </span>
                            <span className="font-medium">{fileUpload.analysis.coverage.servers}</span>
                          </div>
                          <div className="text-center">
                            <span className="text-sm text-gray-600">Ready: </span>
                            {fileUpload.analysis.readyForImport ? (
                              <CheckCircle className="h-4 w-4 text-green-500 inline" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-yellow-500 inline" />
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Project Information Dialog */}
            {showProjectDialog && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                  <div className="p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                      <FolderPlus className="h-5 w-5 mr-2" />
                      Project Information
                    </h2>
                  </div>
                  <div className="p-6">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Project Name *
                        </label>
                        <input
                          type="text"
                          value={projectInfo.name}
                          onChange={(e) => setProjectInfo(prev => ({ ...prev, name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="Enter project name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={projectInfo.description}
                          onChange={(e) => setProjectInfo(prev => ({ ...prev, description: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={3}
                          placeholder="Enter project description"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
                    <button
                      onClick={() => setShowProjectDialog(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => {
                        setShowProjectDialog(false);
                        processData();
                      }}
                      disabled={!projectInfo.name.trim()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Continue Processing
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Feedback Dialog */}
            {showFeedbackDialog && selectedFile && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                  <div className="p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                      <Brain className="h-5 w-5 mr-2" />
                      Improve AI Analysis
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      Help us improve future analysis by providing feedback
                    </p>
                  </div>
                  <div className="p-6">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Correct Asset Type (if wrong)
                        </label>
                        <select
                          value={feedbackData.assetTypeCorrection}
                          onChange={(e) => setFeedbackData(prev => ({ ...prev, assetTypeCorrection: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select if analysis was wrong...</option>
                          <option value="application">Application</option>
                          <option value="server">Server</option>
                          <option value="database">Database</option>
                          <option value="network">Network Device</option>
                          <option value="storage">Storage</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          What was incorrect about the analysis?
                        </label>
                        <textarea
                          value={feedbackData.analysisCorrections}
                          onChange={(e) => setFeedbackData(prev => ({ ...prev, analysisCorrections: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={3}
                          placeholder="e.g., Applications don't need OS or IP address fields..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Additional Comments
                        </label>
                        <textarea
                          value={feedbackData.additionalComments}
                          onChange={(e) => setFeedbackData(prev => ({ ...prev, additionalComments: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={2}
                          placeholder="Any other feedback to improve analysis..."
                        />
                      </div>
                    </div>
                  </div>
                  <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
                    <button
                      onClick={() => setShowFeedbackDialog(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={submitFeedback}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Submit Feedback
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Analysis Details Modal */}
            {selectedFile && selectedFile.analysis && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full mx-4 max-h-[95vh] overflow-y-auto">
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h2 className="text-xl font-semibold text-gray-900">
                        {isEditing ? 'Edit Data: ' : 'Analysis Results: '}{selectedFile.file.name}
                      </h2>
                      <div className="flex items-center space-x-2">
                        {!isEditing && selectedFile.analysis && !selectedFile.analysis.readyForImport && (
                          <button
                            onClick={() => setIsEditing(true)}
                            className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200"
                          >
                            <Edit3 className="h-4 w-4 inline mr-1" />
                            Edit Data
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setSelectedFile(null);
                            setIsEditing(false);
                          }}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <XCircle className="h-6 w-6" />
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="p-6">
                    {isEditing ? (
                      /* Data Editing Interface */
                      <div className="space-y-6">
                        {/* Missing Fields Section */}
                        {getMissingFieldsNotInData().length > 0 && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                            <h3 className="text-lg font-medium text-gray-900 mb-3">Add Missing Required Fields</h3>
                            <div className="flex flex-wrap gap-2 mb-3">
                              {getMissingFieldsNotInData().map((field, index) => (
                                <button
                                  key={index}
                                  onClick={() => addMissingField(field)}
                                  className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm hover:bg-yellow-200 flex items-center"
                                >
                                  <Plus className="h-3 w-3 mr-1" />
                                  {field}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Data Table */}
                        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                          <div className="overflow-x-auto max-h-96">
                            <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50 sticky top-0">
                                <tr>
                                  {getAllFields().map((field, index) => (
                                    <th key={index} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-32">
                                      {field}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                {selectedFile.editableData?.map((row, rowIndex) => (
                                  <tr key={rowIndex} className="hover:bg-gray-50">
                                    {getAllFields().map((field, fieldIndex) => (
                                      <td key={fieldIndex} className="px-4 py-2">
                                        <input
                                          type="text"
                                          value={row[field] || ''}
                                          onChange={(e) => handleCellEdit(rowIndex, field, e.target.value)}
                                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                          placeholder={`Enter ${field}`}
                                        />
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>

                        {/* Project Options */}
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h3 className="text-lg font-medium text-gray-900 mb-3">Processing Options</h3>
                          <div className="space-y-3">
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={projectInfo.saveToDatabase}
                                onChange={(e) => setProjectInfo(prev => ({ ...prev, saveToDatabase: e.target.checked }))}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              />
                              <span className="ml-2 text-sm text-gray-700">Save to database as a project</span>
                            </label>
                            {projectInfo.saveToDatabase && (
                              <div className="ml-6 space-y-2">
                                <input
                                  type="text"
                                  value={projectInfo.name}
                                  onChange={(e) => setProjectInfo(prev => ({ ...prev, name: e.target.value }))}
                                  className="w-full max-w-md px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="Project name"
                                />
                                <textarea
                                  value={projectInfo.description}
                                  onChange={(e) => setProjectInfo(prev => ({ ...prev, description: e.target.value }))}
                                  className="w-full max-w-md px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  rows={2}
                                  placeholder="Project description (optional)"
                                />
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                          <button
                            onClick={() => setIsEditing(false)}
                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={processData}
                            disabled={isProcessing}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                          >
                            {isProcessing ? (
                              <Loader className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                              <Save className="h-4 w-4 mr-2" />
                            )}
                            {isProcessing ? 'Processing...' : 'Process Data'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* Analysis View Interface */
                      <div>
                        {/* Data Quality Score */}
                        <div className="mb-6">
                          <h3 className="text-lg font-medium text-gray-900 mb-3">Data Quality Assessment</h3>
                          <div className="flex items-center space-x-4">
                            <div className={`px-4 py-2 rounded-lg ${getQualityColor(selectedFile.analysis.dataQuality.score)}`}>
                              <span className="font-bold text-lg">{selectedFile.analysis.dataQuality.score}%</span>
                            </div>
                            <div className="flex-1">
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full" 
                                  style={{ width: `${selectedFile.analysis.dataQuality.score}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Coverage Statistics */}
                        <div className="mb-6">
                          <h3 className="text-lg font-medium text-gray-900 mb-3">Asset Coverage</h3>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-blue-50 p-4 rounded-lg text-center">
                              <div className="text-2xl font-bold text-blue-600">{selectedFile.analysis.coverage.applications}</div>
                              <div className="text-sm text-gray-600">Applications</div>
                            </div>
                            <div className="bg-green-50 p-4 rounded-lg text-center">
                              <div className="text-2xl font-bold text-green-600">{selectedFile.analysis.coverage.servers}</div>
                              <div className="text-sm text-gray-600">Servers</div>
                            </div>
                            <div className="bg-purple-50 p-4 rounded-lg text-center">
                              <div className="text-2xl font-bold text-purple-600">{selectedFile.analysis.coverage.databases}</div>
                              <div className="text-sm text-gray-600">Databases</div>
                            </div>
                            <div className="bg-orange-50 p-4 rounded-lg text-center">
                              <div className="text-2xl font-bold text-orange-600">{selectedFile.analysis.coverage.dependencies}</div>
                              <div className="text-sm text-gray-600">Dependencies</div>
                            </div>
                          </div>
                        </div>

                        {/* Issues and Recommendations */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                          <div>
                            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
                              Data Issues
                            </h3>
                            <div className="space-y-2">
                              {selectedFile.analysis.dataQuality.issues.map((issue, index) => (
                                <div key={index} className="flex items-start space-x-2">
                                  <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                                  <span className="text-sm text-gray-700">{issue}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div>
                            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                              <Brain className="h-5 w-5 text-blue-500 mr-2" />
                              AI Recommendations
                            </h3>
                            <div className="space-y-2">
                              {selectedFile.analysis.dataQuality.recommendations.map((rec, index) => (
                                <div key={index} className="flex items-start space-x-2">
                                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                  <span className="text-sm text-gray-700">{rec}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Missing Fields */}
                        {selectedFile.analysis.missingFields.length > 0 && (
                          <div className="mb-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-3">Missing Required Fields</h3>
                            <div className="flex flex-wrap gap-2">
                              {selectedFile.analysis.missingFields.map((field, index) => (
                                <span key={index} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                                  {field}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Required Processing */}
                        {selectedFile.analysis.requiredProcessing.length > 0 && (
                          <div className="mb-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-3">Required Data Processing</h3>
                            <div className="space-y-2">
                              {selectedFile.analysis.requiredProcessing.map((process, index) => (
                                <div key={index} className="flex items-center space-x-2">
                                  <RefreshCw className="h-4 w-4 text-blue-500" />
                                  <span className="text-sm text-gray-700">{process}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                          <button
                            onClick={() => setShowFeedbackDialog(true)}
                            className="px-4 py-2 text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 flex items-center"
                          >
                            <Brain className="h-4 w-4 mr-2" />
                            Improve Analysis
                          </button>
                          <div className="flex space-x-3">
                            <button
                              onClick={() => setSelectedFile(null)}
                              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                            >
                              Close
                            </button>
                          {selectedFile.analysis.readyForImport ? (
                            <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                              <Download className="h-4 w-4 inline mr-2" />
                              Import to Inventory
                            </button>
                          ) : (
                            <button 
                              onClick={() => setIsEditing(true)}
                              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                            >
                              <Edit3 className="h-4 w-4 inline mr-2" />
                              Edit & Process Data
                            </button>
                          )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default CMDBImport; 