
import React, { useState } from 'react'
import Sidebar from '../components/Sidebar';
import { Building2, Calendar, Users, Target, Clock, Layers, Download, Plus } from 'lucide-react';

const Plan = () => {
  const [selectedWave, setSelectedWave] = useState('W1');

  const migrationWaves = [
    {
      id: 'W1',
      name: 'Wave 1 - Critical Systems',
      startDate: '2025-01-15',
      endDate: '2025-03-30',
      applications: 15,
      status: 'Planning',
      progress: 85
    },
    {
      id: 'W2',
      name: 'Wave 2 - Business Applications',
      startDate: '2025-04-01',
      endDate: '2025-06-30',
      applications: 32,
      status: 'Ready',
      progress: 60
    },
    {
      id: 'W3',
      name: 'Wave 3 - Supporting Systems',
      startDate: '2025-07-01',
      endDate: '2025-09-30',
      applications: 48,
      status: 'Draft',
      progress: 25
    },
  ];

  const milestones = [
    { name: 'Architecture Review', date: '2025-01-10', status: 'Completed', wave: 'W1' },
    { name: 'Security Assessment', date: '2025-01-20', status: 'In Progress', wave: 'W1' },
    { name: 'Resource Allocation', date: '2025-02-01', status: 'Pending', wave: 'W1' },
    { name: 'Testing Environment Setup', date: '2025-02-15', status: 'Pending', wave: 'W1' },
    { name: 'Production Migration', date: '2025-03-15', status: 'Pending', wave: 'W1' },
  ];

  const resourceAllocation = [
    { team: 'Cloud Architects', allocated: 3, required: 4, utilization: '75%' },
    { team: 'DevOps Engineers', allocated: 5, required: 6, utilization: '83%' },
    { team: 'Database Administrators', allocated: 2, required: 2, utilization: '100%' },
    { team: 'Security Specialists', allocated: 2, required: 3, utilization: '67%' },
    { team: 'QA Engineers', allocated: 4, required: 5, utilization: '80%' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Planning</h1>
                  <p className="text-lg text-gray-600">
                    Comprehensive migration planning with AI-powered scheduling and resource optimization
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <Plus className="h-5 w-5" />
                    <span>New Wave</span>
                  </button>
                  <button className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2">
                    <Download className="h-5 w-5" />
                    <span>Export Plan</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Migration Waves Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {migrationWaves.map((wave) => (
                <div
                  key={wave.id}
                  className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all ${
                    selectedWave === wave.id ? 'ring-2 ring-blue-500' : 'hover:shadow-lg'
                  }`}
                  onClick={() => setSelectedWave(wave.id)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">{wave.name}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      wave.status === 'Planning' ? 'bg-blue-100 text-blue-800' :
                      wave.status === 'Ready' ? 'bg-green-100 text-green-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {wave.status}
                    </span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Applications</span>
                      <span className="font-medium">{wave.applications}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Duration</span>
                      <span className="font-medium">{wave.startDate} - {wave.endDate}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Planning Progress</span>
                        <span className="font-medium">{wave.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${wave.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Detailed Planning Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Timeline & Milestones */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Calendar className="h-6 w-6 text-purple-500" />
                    <h3 className="text-lg font-semibold text-gray-900">Migration Timeline</h3>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {milestones.map((milestone, index) => (
                      <div key={index} className="flex items-start space-x-4">
                        <div className={`w-3 h-3 rounded-full mt-2 ${
                          milestone.status === 'Completed' ? 'bg-green-500' :
                          milestone.status === 'In Progress' ? 'bg-blue-500' :
                          'bg-gray-300'
                        }`}></div>
                        <div className="flex-1">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-gray-900">{milestone.name}</p>
                              <p className="text-sm text-gray-600">{milestone.date}</p>
                            </div>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              milestone.status === 'Completed' ? 'bg-green-100 text-green-800' :
                              milestone.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {milestone.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Resource Allocation */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Users className="h-6 w-6 text-orange-500" />
                    <h3 className="text-lg font-semibold text-gray-900">Resource Allocation</h3>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {resourceAllocation.map((resource, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-gray-900">{resource.team}</span>
                          <span className="text-sm text-gray-600">{resource.allocated}/{resource.required}</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                parseInt(resource.utilization) >= 90 ? 'bg-red-500' :
                                parseInt(resource.utilization) >= 75 ? 'bg-yellow-500' :
                                'bg-green-500'
                              }`}
                              style={{ width: resource.utilization }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium text-gray-600">{resource.utilization}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Architecture Planning */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <Layers className="h-6 w-6 text-green-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Target Architecture Design</h3>
                </div>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-4 border rounded-lg">
                    <Target className="h-12 w-12 text-blue-500 mx-auto mb-3" />
                    <h4 className="font-semibold text-gray-900 mb-2">Cloud-Native Design</h4>
                    <p className="text-sm text-gray-600">Microservices architecture with containerization</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <Clock className="h-12 w-12 text-green-500 mx-auto mb-3" />
                    <h4 className="font-semibold text-gray-900 mb-2">Auto-scaling</h4>
                    <p className="text-sm text-gray-600">Dynamic resource allocation based on demand</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <Building2 className="h-12 w-12 text-purple-500 mx-auto mb-3" />
                    <h4 className="font-semibold text-gray-900 mb-2">Multi-region</h4>
                    <p className="text-sm text-gray-600">Global deployment for high availability</p>
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

export default Plan;
