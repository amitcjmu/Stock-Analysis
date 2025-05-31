
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { Users, Brain, AlertTriangle, CheckCircle } from 'lucide-react';

const Resource = () => {
  const resourceAllocation = [
    { team: 'Cloud Architects', allocated: 3, required: 4, utilization: '75%', status: 'needs-more' },
    { team: 'DevOps Engineers', allocated: 5, required: 6, utilization: '83%', status: 'needs-more' },
    { team: 'Database Administrators', allocated: 2, required: 2, utilization: '100%', status: 'optimal' },
    { team: 'Security Specialists', allocated: 2, required: 3, utilization: '67%', status: 'needs-more' },
    { team: 'QA Engineers', allocated: 4, required: 5, utilization: '80%', status: 'needs-more' },
    { team: 'Network Engineers', allocated: 2, required: 2, utilization: '90%', status: 'optimal' }
  ];

  const getUtilizationColor = (utilization) => {
    const percent = parseInt(utilization);
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStatusIcon = (status) => {
    return status === 'optimal' ? 
      <CheckCircle className="h-5 w-5 text-green-500" /> : 
      <AlertTriangle className="h-5 w-5 text-orange-500" />;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Resource Allocation</h1>
                  <p className="text-gray-600">Team capacity management and optimization</p>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>AI Optimize</span>
                </button>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Recommendation:</strong> Reallocate 1 DevOps Engineer to Security team for optimal balance
                </p>
              </div>
            </div>

            {/* Resource Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Users className="h-8 w-8 text-blue-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Total Team</h3>
                    <p className="text-2xl font-bold text-blue-600">18</p>
                    <p className="text-sm text-gray-600">Members</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm font-bold">A</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Available</h3>
                    <p className="text-2xl font-bold text-green-600">18</p>
                    <p className="text-sm text-gray-600">Resources</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm font-bold">R</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Required</h3>
                    <p className="text-2xl font-bold text-orange-600">22</p>
                    <p className="text-sm text-gray-600">Resources</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm font-bold">U</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Utilization</h3>
                    <p className="text-2xl font-bold text-purple-600">82%</p>
                    <p className="text-sm text-gray-600">Average</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Resource Allocation */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Team Allocation Details</h2>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {resourceAllocation.map((resource, index) => (
                    <div key={index} className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(resource.status)}
                          <span className="font-medium text-gray-900">{resource.team}</span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm text-gray-600">
                            {resource.allocated}/{resource.required} allocated
                          </span>
                          <span className="text-sm font-medium text-gray-600">{resource.utilization}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="flex-1 bg-gray-200 rounded-full h-3">
                          <div 
                            className={`h-3 rounded-full transition-all ${getUtilizationColor(resource.utilization)}`}
                            style={{ width: resource.utilization }}
                          ></div>
                        </div>
                      </div>
                      {resource.status === 'needs-more' && (
                        <div className="text-sm text-orange-600 ml-8">
                          Need {resource.required - resource.allocated} more team member(s)
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Resource Planning Timeline */}
            <div className="mt-8 bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Resource Timeline</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">Wave 1 Staffing</h3>
                    <p className="text-sm text-gray-600">January - March 2025</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">12 Members</p>
                    <p className="text-sm text-gray-600">Assigned</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">Wave 2 Ramp-up</h3>
                    <p className="text-sm text-gray-600">April - June 2025</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">18 Members</p>
                    <p className="text-sm text-gray-600">Planned</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Resource;
