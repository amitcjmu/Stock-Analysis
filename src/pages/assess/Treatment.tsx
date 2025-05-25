
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Download, Filter } from 'lucide-react';

const Treatment = () => {
  const [filterDept, setFilterDept] = useState('All');
  const [filterTreatment, setFilterTreatment] = useState('All');

  const treatmentData = [
    {
      appId: 'APP001',
      name: 'Customer Portal',
      techStack: 'Java 8',
      criticality: 'High',
      dept: 'Finance',
      treatment: 'Rehost',
      group: 'G1'
    },
    {
      appId: 'APP002', 
      name: 'Legacy Billing',
      techStack: 'COBOL',
      criticality: 'Medium',
      dept: 'HR',
      treatment: 'Retire',
      group: 'G2'
    },
    {
      appId: 'APP003',
      name: 'Analytics Engine',
      techStack: 'Python 3.8',
      criticality: 'High',
      dept: 'IT',
      treatment: 'Refactor',
      group: 'G1'
    },
    {
      appId: 'APP004',
      name: 'Document Manager',
      techStack: '.NET 4.7',
      criticality: 'Low',
      dept: 'Finance',
      treatment: 'Replatform',
      group: 'G3'
    }
  ];

  const filteredData = treatmentData.filter(app => {
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">6R Treatment Analysis</h1>
              <p className="text-gray-600">Analyze applications and assign migration strategies</p>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Treatment Analysis - Live data integration expected September 2025
                </p>
              </div>
            </div>

            {/* 6R Treatments Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-gray-900">Application Treatment Matrix</h2>
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
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default Treatment;
