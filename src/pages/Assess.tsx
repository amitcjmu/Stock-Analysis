
import React, { useState } from 'react'
import Sidebar from '../components/Sidebar';
import type { Filter } from 'lucide-react'
import { Download, Calendar, BarChart3 } from 'lucide-react'

const Assess = () => {
  const [filterDept, setFilterDept] = useState('All');
  const [filterTreatment, setFilterTreatment] = useState('All');

  const assessmentData = [
    {
      appId: 'APP001',
      name: 'Customer Portal',
      techStack: 'Java 8',
      criticality: 'High',
      dept: 'Finance',
      treatment: 'Rehost',
      group: 'G1',
      complexity: 'Medium'
    },
    {
      appId: 'APP002', 
      name: 'Legacy Billing',
      techStack: 'COBOL',
      criticality: 'Medium',
      dept: 'HR',
      treatment: 'Retire',
      group: 'G2',
      complexity: 'Low'
    },
    {
      appId: 'APP003',
      name: 'Analytics Engine',
      techStack: 'Python 3.8',
      criticality: 'High',
      dept: 'IT',
      treatment: 'Refactor',
      group: 'G1',
      complexity: 'High'
    },
    {
      appId: 'APP004',
      name: 'Document Manager',
      techStack: '.NET 4.7',
      criticality: 'Low',
      dept: 'Finance',
      treatment: 'Replatform',
      group: 'G3',
      complexity: 'Medium'
    }
  ];

  const waves = [
    {
      wave: 'W1',
      date: '2025-10-01',
      groups: ['G1'],
      targetDate: '2025-10-15',
      status: 'Planning',
      apps: 12
    },
    {
      wave: 'W2',
      date: '2025-11-01', 
      groups: ['G2', 'G3'],
      targetDate: '2025-11-20',
      status: 'Scheduled',
      apps: 8
    },
    {
      wave: 'W3',
      date: '2025-12-01',
      groups: ['G4'],
      targetDate: '2025-12-15',
      status: 'Draft',
      apps: 15
    }
  ];

  const roadmapData = [
    {
      wave: 'W1',
      phases: [
        { name: 'Assess', start: '2025-09-01', end: '2025-09-15', status: 'completed' },
        { name: 'Migrate', start: '2025-10-01', end: '2025-10-15', status: 'in-progress' },
        { name: 'Validate', start: '2025-10-16', end: '2025-10-30', status: 'planned' }
      ]
    },
    {
      wave: 'W2', 
      phases: [
        { name: 'Assess', start: '2025-10-15', end: '2025-10-30', status: 'in-progress' },
        { name: 'Migrate', start: '2025-11-01', end: '2025-11-20', status: 'planned' },
        { name: 'Decommission', start: '2025-11-21', end: '2025-12-05', status: 'planned' }
      ]
    }
  ];

  const filteredData = assessmentData.filter(app => {
    return (filterDept === 'All' || app.dept === filterDept) &&
           (filterTreatment === 'All' || app.treatment === filterTreatment);
  });

  const getTreatmentColor = (treatment) => {
    const colors = {
      'Rehost': 'bg-blue-100 text-blue-800',
      'Replatform': 'bg-green-100 text-green-800', 
      'Refactor': 'bg-yellow-100 text-yellow-800',
      'Rearchitect': 'bg-purple-100 text-purple-800',
      'Repurchase': 'bg-indigo-100 text-indigo-800',
      'Retire': 'bg-red-100 text-red-800'
    };
    return colors[treatment] || 'bg-gray-100 text-gray-800';
  };

  const getCriticalityColor = (criticality) => {
    const colors = {
      'High': 'bg-red-100 text-red-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-green-100 text-green-800'
    };
    return colors[criticality] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Assessment Phase</h1>
              <p className="text-gray-600">6R treatments, migration grouping, and wave planning</p>
            </div>

            {/* Assessment Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">247</p>
                    <p className="text-gray-600">Total Apps</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-green-500 p-3 rounded-lg">
                    <Calendar className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">89</p>
                    <p className="text-gray-600">Assessed</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-orange-500 p-3 rounded-lg">
                    <Filter className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">3</p>
                    <p className="text-gray-600">Waves</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-purple-500 p-3 rounded-lg">
                    <Download className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">4</p>
                    <p className="text-gray-600">Groups</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 6R Treatments Table */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-gray-900">6R Treatment Analysis</h2>
                  <div className="flex space-x-4">
                    <select
                      value={filterDept}
                      onChange={(e) => setFilterDept(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="All">All Departments</option>
                      <option value="Finance">Finance</option>
                      <option value="HR">HR</option>
                      <option value="IT">IT</option>
                    </select>
                    <select
                      value={filterTreatment}
                      onChange={(e) => setFilterTreatment(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="All">All Treatments</option>
                      <option value="Rehost">Rehost</option>
                      <option value="Replatform">Replatform</option>
                      <option value="Refactor">Refactor</option>
                      <option value="Retire">Retire</option>
                    </select>
                    <button className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 flex items-center space-x-2">
                      <Download className="h-4 w-4" />
                      <span>Download CSV</span>
                    </button>
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">App ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tech Stack</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Criticality</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">6R Treatment</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Group</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredData.map((app) => (
                      <tr key={app.appId} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{app.appId}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{app.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{app.techStack}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCriticalityColor(app.criticality)}`}>
                            {app.criticality}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{app.dept}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTreatmentColor(app.treatment)}`}>
                            {app.treatment}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{app.group}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Wave Planning */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Wave Planning</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {waves.map((wave) => (
                      <div key={wave.wave} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold text-lg">{wave.wave}</h3>
                            <p className="text-sm text-gray-600">Start: {wave.date}</p>
                            <p className="text-sm text-gray-600">Target: {wave.targetDate}</p>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            wave.status === 'Planning' ? 'bg-blue-100 text-blue-800' :
                            wave.status === 'Scheduled' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {wave.status}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="text-sm text-gray-500">Groups: </span>
                            <span className="text-sm font-medium">{wave.groups.join(', ')}</span>
                          </div>
                          <div className="text-sm text-gray-500">
                            {wave.apps} applications
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Roadmap Timeline */}
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Migration Roadmap</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-6">
                    {roadmapData.map((wave) => (
                      <div key={wave.wave}>
                        <h3 className="font-semibold mb-3">{wave.wave}</h3>
                        <div className="space-y-2">
                          {wave.phases.map((phase) => (
                            <div key={phase.name} className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                phase.status === 'completed' ? 'bg-green-500' :
                                phase.status === 'in-progress' ? 'bg-blue-500' :
                                'bg-gray-300'
                              }`}></div>
                              <div className="flex-1">
                                <div className="flex justify-between">
                                  <span className="text-sm font-medium">{phase.name}</span>
                                  <span className="text-xs text-gray-500">{phase.start} - {phase.end}</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                                  <div className={`h-2 rounded-full ${
                                    phase.status === 'completed' ? 'bg-green-500 w-full' :
                                    phase.status === 'in-progress' ? 'bg-blue-500 w-1/2' :
                                    'bg-gray-300 w-0'
                                  }`}></div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
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

export default Assess;
