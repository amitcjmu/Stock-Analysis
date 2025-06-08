import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Link } from 'react-router-dom';
import { API_CONFIG } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
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
  nextSteps?: Array<{ label: string; route?: string; description?: string }>;
  confidence?: number;
  detectedFileType?: string;
  analysisSteps?: string[];
  currentStep?: number;
  processingMessages?: string[];
  analysisError?: string;
}

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
];

const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = (error) => reject(error);
        reader.readAsBinaryString(file);
    });
};

const parseFileContent = (content: string, filename: string) => {
    try {
        if (filename.endsWith('.csv')) {
            const lines = content.split('\n');
            const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
            const dataLines = lines.slice(1);
            return {
                headers,
                data: dataLines.map(line => {
                    const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
                    let row: any = {};
                    headers.forEach((header, i) => {
                        row[header] = values[i];
                    });
                    return row;
                }).filter(row => Object.values(row).some(v => v))
            };
        } else if (filename.endsWith('.json')) {
            const parsed = JSON.parse(content);
            return {
                headers: Object.keys(parsed[0] || {}),
                data: parsed
            };
        }
        return { headers: [], data: [{ content }] };
    } catch (error) {
        console.error('Error parsing file content:', error);
        return { headers: [], data: [{ content: content.substring(0, 500) }] };
    }
};


export default function DataImport() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { getAuthHeaders } = useAuth();

  const analyzeFiles = async (files: UploadedFile[]) => {
    setIsAnalyzing(true);
    for (const fileUpload of files) {
      setUploadedFiles(prev => prev.map(f => f.file === fileUpload.file ? { ...f, status: 'analyzing', processingMessages: ['🤖 AI crew initializing...'] } : f));
      try {
        const fileContent = await readFileContent(fileUpload.file);
        const { headers, data } = parseFileContent(fileContent, fileUpload.file.name);
        
        setUploadedFiles(prev => prev.map(f => f.file === fileUpload.file ? { ...f, processingMessages: [...(f.processingMessages || []), '🔬 File parsed, invoking discovery flow...'] } : f));

        const requestBody = {
          headers: headers,
          sample_data: data, // Sending full data as per user request
          filename: fileUpload.file.name,
          options: { source: 'file_upload', intended_type: fileUpload.type }
        };

        const response = await fetch(`${API_CONFIG.BASE_URL}/discovery/flow/run`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Discovery flow failed: ${response.status} ${errorText}`);
        }

        const result = await response.json();
        setUploadedFiles(prev => prev.map(f => f.file === fileUpload.file ? { 
            ...f, 
            status: 'processed', 
            aiSuggestions: result.flow_result?.recommendations,
            nextSteps: result.next_steps?.recommended_actions?.map((action: string) => ({ label: action })) || [],
            confidence: result.flow_result?.confidence,
            processingMessages: [...(f.processingMessages || []), '✅ AI analysis complete.']
        } : f));

      } catch (error: any) {
        setUploadedFiles(prev => prev.map(f => f.file === fileUpload.file ? { ...f, status: 'error', analysisError: error.message } : f));
      }
    }
    setIsAnalyzing(false);
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      type: 'cmdb', // Assumption for now
      status: 'uploaded' as const,
      processingMessages: []
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
    setTimeout(() => analyzeFiles(newFiles), 500);
  }, [analyzeFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div className="p-6">
        <h1 className="text-2xl font-semibold mb-4">Upload Your Data</h1>
        <p className="text-gray-600 mb-6">Choose the category that best represents what you intend to upload. Our AI crew will analyze the actual content and determine its true type and value.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {uploadAreas.map((area) => (
                <div key={area.id} {...getRootProps()} className={`p-6 border-2 border-dashed rounded-lg text-center cursor-pointer hover:border-solid hover:bg-gray-50`}>
                    <input {...getInputProps()} />
                    <div className={`w-12 h-12 ${area.color} rounded-lg flex items-center justify-center mx-auto mb-4`}>
                        <area.icon className="text-white" size={24} />
                    </div>
                    <h3 className="font-semibold">{area.title}</h3>
                    <p className="text-sm text-gray-500">{area.description}</p>
                </div>
            ))}
        </div>
        
        <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">AI Crew Analysis</h2>
            {uploadedFiles.length === 0 && !isAnalyzing ? (
                <div className="text-center py-8 border-2 border-dashed rounded-lg">
                    <p className="text-gray-500">Upload a file to begin analysis.</p>
                </div>
            ) : (
                <div>
                    {uploadedFiles.map((upFile, index) => (
                        <div key={index} className="mb-4 p-4 border rounded-lg">
                            <p className="font-semibold">{upFile.file.name}</p>
                            <p>Status: {upFile.status}</p>
                            {upFile.processingMessages?.map((msg, i) => <p key={i}>{msg}</p>)}
                            {upFile.analysisError && <p className="text-red-500">{upFile.analysisError}</p>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    </div>
  );
} 