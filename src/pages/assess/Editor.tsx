import type React from 'react';
import type { useParams } from 'react-router-dom';
import { Save, User, Shield, Database, Settings } from 'lucide-react';
import { toast } from 'sonner';
import Sidebar from '../../components/Sidebar';
import { useAuth } from '@/contexts/AuthContext';
import { useApplication, useUpdateApplication } from '@/hooks/useApplication';

const Editor = () => {
  const { applicationId } = useParams<{ applicationId: string }>();
  const { isAuthenticated } = useAuth();

  // Fetch application data
  const { 
    data: application,
    isLoading,
    error
  } = useApplication(applicationId || '');

  // Update application mutation
  const { mutate: updateApplication, isPending: isUpdating } = useUpdateApplication();

  // Handle input changes
  const handleInputChange = (field: keyof Application, value: Application[keyof Application]) => {
    if (!applicationId) return;
    
    updateApplication(
      {
        applicationId,
        data: { [field]: value }
      },
      {
        onSuccess: () => {
          toast.success('Application updated successfully');
        },
        onError: (error) => {
          toast.error('Failed to update application: ' + error.message);
        }
      }
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <div className="max-w-4xl mx-auto">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">Error loading application: {error.message}</p>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Application Quick Editor</h1>
              <p className="text-gray-600">Edit application details and configurations</p>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Editor - Live data integration expected September 2025
                </p>
              </div>
            </div>

            {/* Editor Form */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Application Configuration</h2>
              </div>
              
              <div className="p-6 space-y-8">
                {/* Scope Section */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <Settings className="h-5 w-5 text-blue-500" />
                    <h3 className="text-lg font-medium text-gray-900">Scope</h3>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Migration Scope</label>
                      <select
                        value={application?.scope || 'In Scope'}
                        onChange={(e) => handleInputChange('scope', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="In Scope">In Scope</option>
                        <option value="Out of Scope">Out of Scope</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Migration Planning Section */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <Shield className="h-5 w-5 text-green-500" />
                    <h3 className="text-lg font-medium text-gray-900">Migration Planning</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">App Strategy</label>
                      <select
                        value={application?.appStrategy || 'No Strategy Assigned'}
                        onChange={(e) => handleInputChange('appStrategy', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="No Strategy Assigned">No Strategy Assigned</option>
                        <option value="Lift and Shift">Lift and Shift</option>
                        <option value="Modernize">Modernize</option>
                        <option value="Retire">Retire</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">6R Treatment</label>
                      <select
                        value={application?.grTreatment || 'No Strategy Assigned'}
                        onChange={(e) => handleInputChange('grTreatment', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="No Strategy Assigned">No Strategy Assigned</option>
                        <option value="Rehost">Rehost</option>
                        <option value="Replatform">Replatform</option>
                        <option value="Refactor">Refactor</option>
                        <option value="Rearchitect">Rearchitect</option>
                        <option value="Repurchase">Repurchase</option>
                        <option value="Retire">Retire</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Migration Wave</label>
                      <select
                        value={application?.wave || 'Wave 7'}
                        onChange={(e) => handleInputChange('wave', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="Wave 7">Wave 7</option>
                        <option value="Wave 1">Wave 1</option>
                        <option value="Wave 2">Wave 2</option>
                        <option value="Wave 3">Wave 3</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* App Classification Section */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <Database className="h-5 w-5 text-purple-500" />
                    <h3 className="text-lg font-medium text-gray-900">App Classification</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Function</label>
                      <input
                        type="text"
                        value={application?.function || 'Business Application'}
                        onChange={(e) => handleInputChange('function', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                      <select
                        value={application?.type || 'Choose an App Type'}
                        onChange={(e) => handleInputChange('type', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="Choose an App Type">Choose an App Type</option>
                        <option value="Web Application">Web Application</option>
                        <option value="Database">Database</option>
                        <option value="API Service">API Service</option>
                        <option value="Batch Job">Batch Job</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Data Classification Section */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Data Classification</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">PII Data</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={application?.piiData || false}
                          onChange={(e) => handleInputChange('piiData', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Business Critical</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={application?.businessCritical || false}
                          onChange={(e) => handleInputChange('businessCritical', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Team Members Section */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <User className="h-5 w-5 text-orange-500" />
                    <h3 className="text-lg font-medium text-gray-900">Team Members</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">App Owner</label>
                      <input
                        type="text"
                        value={application?.appOwner || 'Enter App Owner'}
                        onChange={(e) => handleInputChange('appOwner', e.target.value)}
                        placeholder="Enter App Owner"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                      <input
                        type="email"
                        value={application?.email || ''}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="owner@company.com"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Save Button */}
                <div className="flex justify-end">
                  <button
                    onClick={() => {
                      if (!applicationId || !application) return;
                      updateApplication(
                        {
                          applicationId,
                          data: application
                        },
                        {
                          onSuccess: () => {
                            toast.success('All changes saved successfully');
                          },
                          onError: (error) => {
                            toast.error('Failed to save changes: ' + error.message);
                          }
                        }
                      );
                    }}
                    disabled={isUpdating}
                    className={`bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 flex items-center space-x-2 transition-colors duration-200 ${isUpdating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <Save className="h-5 w-5" />
                    <span>{isUpdating ? 'Saving...' : 'Save Configuration'}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Editor;
