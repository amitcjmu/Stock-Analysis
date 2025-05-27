import React, { useState, useCallback } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import FileUploadArea from '../../components/discovery/FileUploadArea';
import FileList, { FileUpload, AnalysisResult } from '../../components/discovery/FileList';
import ProjectDialog, { ProjectInfo } from '../../components/discovery/ProjectDialog';
import { useCMDBAnalysis } from '../../hooks/useCMDBAnalysis';
import { apiCall, API_CONFIG } from '../../config/api';
import { 
  Download,
  AlertCircle,
  RefreshCw,
  Save,
  Plus,
  Trash2,
  Brain,
  CheckCircle,
  XCircle,
  Eye,
  Edit3
} from 'lucide-react';

const CMDBImport = () => {
  const [uploadedFiles, setUploadedFiles] = useState<FileUpload[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null);
  const [isEditing, setIsEditing] = useState(false);
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

  const { 
    isAnalyzing, 
    isProcessing, 
    analyzeFile, 
    processData, 
    submitFeedback 
  } = useCMDBAnalysis();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'uploaded' as const
    }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    // Auto-analyze the first file
    if (newFiles.length > 0) {
      handleAnalyzeFile(newFiles[0]);
    }
  }, []);



  const updateFileInList = useCallback((id: string, updates: Partial<FileUpload>) => {
    setUploadedFiles(prev => 
      prev.map(f => f.id === id ? { ...f, ...updates } : f)
    );
  }, []);

  const handleAnalyzeFile = async (fileUpload: FileUpload) => {
    try {
      await analyzeFile(fileUpload, updateFileInList);
    } catch (error) {
      console.error('Analysis failed:', error);
    }
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

  const handleProcessData = async () => {
    if (!selectedFile || !selectedFile.editableData) return;
    
    if (projectInfo.saveToDatabase && !projectInfo.name.trim()) {
      setShowProjectDialog(true);
      return;
    }
    
    try {
      const processedData = await processData(selectedFile, projectInfo.saveToDatabase ? projectInfo : null);
      
      console.log('Data processed successfully:', processedData);
      
      // Update the file status
      updateFileInList(selectedFile.id, {
        status: 'processed',
        analysis: {
          ...selectedFile.analysis!,
          status: 'completed',
          readyForImport: true
        }
      });
      
      // Close editing mode
      setIsEditing(false);
      setSelectedFile(null);
      
    } catch (error) {
      console.error('Processing failed:', error);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!selectedFile || !selectedFile.analysis) return;
    
    try {
      const result = await submitFeedback(
        selectedFile.file.name,
        selectedFile.analysis,
        feedbackData
      );
      
      console.log('Feedback submitted successfully:', result);
      setShowFeedbackDialog(false);
      setFeedbackData({
        assetTypeCorrection: '',
        analysisCorrections: '',
        additionalComments: ''
      });
      
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
      case 'analyzing':
        return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getAllFields = () => {
    if (!selectedFile || !selectedFile.editableData || selectedFile.editableData.length === 0) return [];
    return Object.keys(selectedFile.editableData[0]);
  };

  const getMissingFieldsNotInData = () => {
    if (!selectedFile || !selectedFile.analysis) return [];
    const currentFields = getAllFields();
    return selectedFile.analysis.missingFields.filter(field => 
      !currentFields.some(currentField => 
        currentField.toLowerCase().includes(field.toLowerCase()) ||
        field.toLowerCase().includes(currentField.toLowerCase())
      )
    );
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden ml-64">
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">CMDB Import & Analysis</h1>
              <p className="mt-2 text-gray-600">
                Upload your CMDB export files for AI-powered analysis and validation
              </p>
            </div>

            {/* File Upload Area */}
            <FileUploadArea 
              onFilesUploaded={(files) => onDrop(files)}
              isAnalyzing={isAnalyzing}
            />

            {/* File List */}
            <FileList 
              files={uploadedFiles}
              onAnalyzeFile={handleAnalyzeFile}
              onViewAnalysis={(file) => {
                setSelectedFile(file);
                setIsEditing(false);
              }}
              onEditData={(file) => {
                setSelectedFile(file);
                setIsEditing(true);
              }}
            />

            {/* Analysis Results */}
            {selectedFile && selectedFile.analysis && !isEditing && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Analysis Results: {selectedFile.file.name}
                  </h2>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 sm:px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm sm:text-base"
                    >
                      <Edit3 className="h-4 w-4 inline mr-1 sm:mr-2" />
                      <span className="hidden sm:inline">Edit Data</span>
                      <span className="sm:hidden">Edit</span>
                    </button>
                    <button
                      onClick={() => setShowFeedbackDialog(true)}
                      className="px-3 sm:px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm sm:text-base"
                    >
                      <Brain className="h-4 w-4 inline mr-1 sm:mr-2" />
                      <span className="hidden sm:inline">Provide Feedback</span>
                      <span className="sm:hidden">Feedback</span>
                    </button>
                  </div>
                </div>

                {/* Data Quality Score */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-6">
                  <div className="text-center">
                    <div className={`inline-flex px-3 py-2 rounded-full text-xs sm:text-sm font-medium ${getQualityColor(selectedFile.analysis.dataQuality.score)}`}>
                      Data Quality: {selectedFile.analysis.dataQuality.score}%
                    </div>
                  </div>
                  <div className="text-center">
                    <span className="text-xs sm:text-sm text-gray-600">Applications: </span>
                    <span className="text-base sm:text-lg font-semibold">{selectedFile.analysis.coverage.applications}</span>
                  </div>
                  <div className="text-center">
                    <span className="text-xs sm:text-sm text-gray-600">Servers: </span>
                    <span className="text-base sm:text-lg font-semibold">{selectedFile.analysis.coverage.servers}</span>
                  </div>
                  <div className="text-center">
                    <span className="text-xs sm:text-sm text-gray-600">Databases: </span>
                    <span className="text-base sm:text-lg font-semibold">{selectedFile.analysis.coverage.databases}</span>
                  </div>
                </div>

                {/* Issues and Recommendations */}
                {selectedFile.analysis.dataQuality.issues.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Data Quality Issues</h3>
                    <div className="bg-red-50 border border-red-200 rounded-md p-4">
                      <ul className="list-disc list-inside space-y-1">
                        {selectedFile.analysis.dataQuality.issues.map((issue, index) => (
                          <li key={index} className="text-red-700">{issue}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {selectedFile.analysis.dataQuality.recommendations.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Recommendations</h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <ul className="list-disc list-inside space-y-1">
                        {selectedFile.analysis.dataQuality.recommendations.map((rec, index) => (
                          <li key={index} className="text-blue-700">{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Missing Fields */}
                {selectedFile.analysis.missingFields.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Missing Required Fields</h3>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <div className="flex flex-wrap gap-2">
                        {selectedFile.analysis.missingFields.map((field, index) => (
                          <span key={index} className="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm">
                            {field}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Data Preview */}
                {selectedFile.preview && selectedFile.preview.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Data Preview</h3>
                    <div className="overflow-x-auto border border-gray-200 rounded-lg">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            {Object.keys(selectedFile.preview[0]).map((header) => (
                              <th key={header} className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {selectedFile.preview.slice(0, 5).map((row, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              {Object.values(row).map((value, cellIndex) => (
                                <td key={cellIndex} className="px-3 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-gray-900">
                                  {String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Data Editing Interface */}
            {selectedFile && isEditing && selectedFile.editableData && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Edit Data: {selectedFile.file.name}
                  </h2>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 sm:px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm sm:text-base"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleProcessData}
                      disabled={isProcessing}
                      className="px-3 sm:px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 text-sm sm:text-base"
                    >
                      {isProcessing ? (
                        <RefreshCw className="h-4 w-4 inline mr-1 sm:mr-2 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4 inline mr-1 sm:mr-2" />
                      )}
                      <span className="hidden sm:inline">{isProcessing ? 'Processing...' : 'Save & Process'}</span>
                      <span className="sm:hidden">{isProcessing ? 'Processing...' : 'Save'}</span>
                    </button>
                  </div>
                </div>

                {/* Missing Fields Actions */}
                {getMissingFieldsNotInData().length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Add Missing Fields</h3>
                    <div className="flex flex-wrap gap-2">
                      {getMissingFieldsNotInData().map((field) => (
                        <button
                          key={field}
                          onClick={() => addMissingField(field)}
                          className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                        >
                          <Plus className="h-4 w-4 inline mr-1" />
                          Add {field}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Project Info */}
                <div className="mb-6">
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={projectInfo.saveToDatabase}
                        onChange={(e) => setProjectInfo(prev => ({ ...prev, saveToDatabase: e.target.checked }))}
                        className="mr-2"
                      />
                      Save as project
                    </label>
                    {projectInfo.saveToDatabase && (
                      <input
                        type="text"
                        placeholder="Project name"
                        value={projectInfo.name}
                        onChange={(e) => setProjectInfo(prev => ({ ...prev, name: e.target.value }))}
                        className="px-3 py-1 border border-gray-300 rounded-md"
                      />
                    )}
                  </div>
                </div>

                {/* Editable Data Table */}
                <div className="overflow-x-auto border border-gray-200 rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {getAllFields().map((header) => (
                          <th key={header} className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {selectedFile.editableData.slice(0, 10).map((row, rowIndex) => (
                        <tr key={rowIndex} className="hover:bg-gray-50">
                          {getAllFields().map((field) => (
                            <td key={field} className="px-3 sm:px-6 py-4 whitespace-nowrap">
                              <input
                                type="text"
                                value={row[field] || ''}
                                onChange={(e) => handleCellEdit(rowIndex, field, e.target.value)}
                                className="w-full px-2 py-1 text-xs sm:text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            )}
          </div>
        </main>
      </div>

      {/* Project Dialog */}
      {showProjectDialog && (
        <ProjectDialog
          isOpen={showProjectDialog}
          projectInfo={projectInfo}
          onProjectInfoChange={setProjectInfo}
          onCancel={() => setShowProjectDialog(false)}
          onConfirm={() => {
            setShowProjectDialog(false);
            handleProcessData();
          }}
          isProcessing={isProcessing}
        />
      )}

      {/* Feedback Dialog */}
      {showFeedbackDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Provide Analysis Feedback</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Correct Asset Type
                </label>
                <select
                  value={feedbackData.assetTypeCorrection}
                  onChange={(e) => setFeedbackData(prev => ({ ...prev, assetTypeCorrection: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select correct type...</option>
                  <option value="application">Application</option>
                  <option value="server">Server</option>
                  <option value="database">Database</option>
                  <option value="network">Network Device</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Analysis Issues
                </label>
                <textarea
                  value={feedbackData.analysisCorrections}
                  onChange={(e) => setFeedbackData(prev => ({ ...prev, analysisCorrections: e.target.value }))}
                  placeholder="Describe what was incorrect about the analysis..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Comments
                </label>
                <textarea
                  value={feedbackData.additionalComments}
                  onChange={(e) => setFeedbackData(prev => ({ ...prev, additionalComments: e.target.value }))}
                  placeholder="Any additional feedback or suggestions..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowFeedbackDialog(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitFeedback}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      <FeedbackWidget />
    </div>
  );
};

export default CMDBImport; 