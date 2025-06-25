import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Upload, 
  Database, 
  FileText, 
  Settings, 
  BarChart3, 
  Network,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';
import UniversalProcessingStatus from '@/components/discovery/UniversalProcessingStatus';

const DataImportDemo: React.FC = () => {
  const [currentFlow, setCurrentFlow] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState<'idle' | 'processing' | 'completed'>('idle');
  const [selectedDataCategory, setSelectedDataCategory] = useState<string>('cmdb');

  // Simulate flow creation for demo
  const startDemoFlow = () => {
    const mockFlowId = `demo-flow-${Date.now()}`;
    setCurrentFlow(mockFlowId);
    setDemoMode('processing');
    
    // Simulate completion after 30 seconds
    setTimeout(() => {
      setDemoMode('completed');
    }, 30000);
  };

  const resetDemo = () => {
    setCurrentFlow(null);
    setDemoMode('idle');
  };

  const dataCategories = [
    {
      id: 'cmdb',
      title: 'CMDB Export Data',
      description: 'Configuration Management Database exports with asset information',
      icon: Database,
      formats: ['csv', 'xlsx', 'json'],
      examples: ['ServiceNow reports', 'BMC Remedy data', 'Custom CMDB files']
    },
    {
      id: 'application',
      title: 'Application Discovery Data',
      description: 'Application portfolio and dependency scan results',
      icon: Network,
      formats: ['csv', 'json', 'xml'],
      examples: ['Application scans', 'Dependency maps', 'Service inventories']
    },
    {
      id: 'infrastructure',
      title: 'Infrastructure Assessment',
      description: 'Server, network, and infrastructure discovery data',
      icon: Settings,
      formats: ['csv', 'xlsx', 'json'],
      examples: ['Network scans', 'Server inventories', 'Performance data']
    },
    {
      id: 'sensitive',
      title: 'Sensitive Data Assets',
      description: 'Data containing PII, financial, or confidential information',
      icon: FileText,
      formats: ['csv', 'xlsx'],
      examples: ['Customer data', 'Financial records', 'HR systems']
    }
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Secure Data Import</h1>
          <p className="text-gray-600 mt-2">
            Upload migration data files for AI-powered validation and security analysis. 
            Our specialized agents ensure data quality, security, and privacy compliance before any processing begins.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Badge variant="outline" className="text-green-600 border-green-200">
            Enterprise Security
          </Badge>
          <Badge variant="outline" className="text-blue-600 border-blue-200">
            AI-Powered Validation
          </Badge>
        </div>
      </div>

      {/* Demo Controls */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Demo Controls
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <Button 
              onClick={startDemoFlow}
              disabled={demoMode === 'processing'}
              className="flex items-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Start Demo Processing</span>
            </Button>
            <Button 
              variant="outline"
              onClick={resetDemo}
              className="flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset Demo</span>
            </Button>
            <Badge variant={demoMode === 'processing' ? 'default' : 'secondary'}>
              {demoMode === 'idle' ? 'Demo Ready' : 
               demoMode === 'processing' ? 'Demo Running' : 'Demo Completed'}
            </Badge>
          </div>
          <p className="text-sm text-blue-700 mt-2">
            This demonstrates how the Universal Processing Status component provides real-time updates 
            during data import, validation, and processing phases.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Data Categories */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Choose Data Category</CardTitle>
              <p className="text-sm text-gray-600">
                Upload migration data files for AI-powered validation and security analysis. Our specialized agents ensure 
                data quality, security, and privacy compliance before any processing begins.
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dataCategories.map((category) => {
                  const IconComponent = category.icon;
                  const isSelected = selectedDataCategory === category.id;
                  
                  return (
                    <div
                      key={category.id}
                      className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                        isSelected 
                          ? 'bg-blue-50 border-blue-200 ring-2 ring-blue-500' 
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedDataCategory(category.id)}
                    >
                      <div className="flex items-center space-x-3 mb-3">
                        <IconComponent className={`w-6 h-6 ${isSelected ? 'text-blue-600' : 'text-gray-500'}`} />
                        <h3 className={`font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                          {category.title}
                        </h3>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-3">
                        {category.description}
                      </p>
                      
                      <div className="space-y-2">
                        <div>
                          <span className="text-xs font-medium text-gray-500">Accepted formats:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {category.formats.map((format) => (
                              <Badge key={format} variant="secondary" className="text-xs">
                                {format}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-xs font-medium text-gray-500">Examples:</span>
                          <div className="text-xs text-gray-600 mt-1">
                            {category.examples.join(', ')}
                          </div>
                        </div>
                      </div>
                      
                      {isSelected && (
                        <div className="mt-4 pt-3 border-t border-blue-200">
                          <Button 
                            className="w-full"
                            disabled={demoMode === 'processing'}
                          >
                            <Upload className="w-4 h-4 mr-2" />
                            Upload {category.title}
                          </Button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Sample Files Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Sample Files & Templates
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Sample CMDB Export</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Example ServiceNow CMDB export with 1,000 sample records
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Download Sample (CSV)
                  </Button>
                </div>
                
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Template Mapping</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Field mapping template for custom data sources
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Download Template (XLSX)
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Universal Processing Status */}
        <div className="space-y-6">
          {/* This is the key integration - Universal Processing Status replaces static status sections */}
          <UniversalProcessingStatus
            flow_id={currentFlow}
            page_context="data_import"
            title="Upload & Validation Status"
            showAgentInsights={true}
            showValidationDetails={true}
            onProcessingComplete={() => {
              console.log('Processing completed!');
              setDemoMode('completed');
            }}
            onValidationFailed={(issues) => {
              console.log('Validation failed:', issues);
            }}
          />

          {/* Additional Status Cards - these would also use Universal Processing Status */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Other Processing Areas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-gray-600">
                <p className="mb-2">The Universal Processing Status component can be integrated into any page:</p>
                <ul className="space-y-1 text-xs">
                  <li>• <strong>Attribute Mapping:</strong> Real-time field mapping progress</li>
                  <li>• <strong>Data Cleansing:</strong> Live data quality improvements</li>
                  <li>• <strong>Asset Inventory:</strong> Asset discovery and classification</li>
                  <li>• <strong>Dependency Analysis:</strong> Relationship mapping progress</li>
                  <li>• <strong>6R Analysis:</strong> Migration strategy recommendations</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Integration Example */}
          <Card className="bg-green-50 border-green-200">
            <CardHeader>
              <CardTitle className="text-green-900 text-base">Integration Example</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-green-800">
                <pre className="bg-green-100 p-2 rounded text-xs overflow-x-auto">
{`<UniversalProcessingStatus
  flow_id={currentFlowId}
  page_context="data_import"
  title="Upload & Validation Status"
  showAgentInsights={true}
  showValidationDetails={true}
  onProcessingComplete={() => {
    // Handle completion
  }}
  onValidationFailed={(issues) => {
    // Handle validation issues
  }}
/>`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DataImportDemo; 