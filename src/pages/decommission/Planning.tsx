
import React, { useState } from 'react'
import Sidebar from '../../components/Sidebar';
import { Filter, AlertTriangle, Users } from 'lucide-react'
import { FileText, Search, Download, CheckCircle, Clock } from 'lucide-react'

const DecommissionPlanning = () => {
  const [selectedFilter, setSelectedFilter] = useState('all');

  const planningMetrics = [
    { label: 'Systems Identified', value: '120', color: 'text-blue-600' },
    { label: 'Dependencies Mapped', value: '89', color: 'text-purple-600' },
    { label: 'Risk Assessments', value: '67', color: 'text-orange-600' },
    { label: 'Approval Pending', value: '23', color: 'text-red-600' },
  ];

  const systemsForDecommission = [
    {
      id: 'SYS001',
      name: 'Legacy Billing System',
      type: 'Application',
      department: 'Finance',
      criticality: 'Low',
      dependencies: 3,
      riskLevel: 'Medium',
      businessImpact: 'Low',
      status: 'Assessment Complete',
      estimatedSavings: '$85,000/year',
      lastUsed: '2024-06-15'
    },
    {
      id: 'SYS002',
      name: 'Old Email Server',
      type: 'Infrastructure',
      department: 'IT',
      criticality: 'Medium',
      dependencies: 8,
      riskLevel: 'High',
      businessImpact: 'Medium',
      status: 'Under Review',
      estimatedSavings: '$45,000/year',
      lastUsed: '2024-12-01'
    },
    {
      id: 'SYS003',
      name: 'Mainframe Database',
      type: 'Database',
      department: 'Operations',
      criticality: 'High',
      dependencies: 15,
      riskLevel: 'Very High',
      businessImpact: 'High',
      status: 'Planning',
      estimatedSavings: '$200,000/year',
      lastUsed: '2024-11-20'
    },
    {
      id: 'SYS004',
      name: 'Legacy CRM',
      type: 'Application',
      department: 'Sales',
      criticality: 'Medium',
      dependencies: 5,
      riskLevel: 'Low',
      businessImpact: 'Medium',
      status: 'Approved',
      estimatedSavings: '$65,000/year',
      lastUsed: '2024-08-30'
    },
  ];

  const decommissionSteps = [
    {
      step: 1,
      title: 'System Identification',
      description: 'Identify legacy systems, applications, and infrastructure components',
      status: 'completed',
      tasks: [
        'Inventory all IT assets',
        'Identify redundant systems',
        'Document system specifications'
      ]
    },
    {
      step: 2,
      title: 'Dependency Analysis',
      description: 'Map system dependencies and interconnections',
      status: 'in-progress',
      tasks: [
        'Document data flows',
        'Identify integration points',
        'Map user dependencies'
      ]
    },
    {
      step: 3,
      title: 'Risk Assessment',
      description: 'Evaluate risks associated with system decommission',
      status: 'in-progress',
      tasks: [
        'Assess business impact',
        'Identify technical risks',
        'Document mitigation strategies'
      ]
    },
    {
      step: 4,
      title: 'Stakeholder Approval',
      description: 'Obtain necessary approvals from business stakeholders',
      status: 'pending',
      tasks: [
        'Present decommission plan',
        'Gather stakeholder feedback',
        'Obtain formal approval'
      ]
    }
  ];

  const filteredSystems = selectedFilter === 'all' ? systemsForDecommission :
                         systemsForDecommission.filter(system => system.status.toLowerCase().includes(selectedFilter));

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Decommission Planning</h1>
                  <p className="text-lg text-gray-600">
                    Plan and assess systems for safe decommissioning
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Coming Soon: CloudBridge automated dependency mapping
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Download className="h-5 w-5" />
                    <span>Export Plan</span>
                  </button>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>Create Assessment</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Planning Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {planningMetrics.map((metric, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color}`}>
                        {metric.value}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Planning Steps */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Planning Process</h3>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {decommissionSteps.map((step) => (
                    <div key={step.step} className="flex space-x-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          step.status === 'completed' ? 'bg-green-500 text-white' :
                          step.status === 'in-progress' ? 'bg-blue-500 text-white' :
                          'bg-gray-300 text-gray-600'
                        }`}>
                          {step.status === 'completed' ? (
                            <CheckCircle className="h-5 w-5" />
                          ) : step.status === 'in-progress' ? (
                            <Clock className="h-5 w-5" />
                          ) : (
                            <span className="text-sm font-bold">{step.step}</span>
                          )}
                        </div>
                        {step.step < decommissionSteps.length && (
                          <div className="w-px h-16 bg-gray-300 mt-2"></div>
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h4>
                        <p className="text-gray-600 mb-3">{step.description}</p>
                        <ul className="space-y-1">
                          {step.tasks.map((task, index) => (
                            <li key={index} className="text-sm text-gray-500 flex items-center space-x-2">
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                              <span>{task}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Systems Assessment Table */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Systems Assessment</h3>
                  <div className="flex space-x-3">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <input
                        type="text"
                        placeholder="Search systems..."
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <select
                      value={selectedFilter}
                      onChange={(e) => setSelectedFilter(e.target.value)}
                      className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Status</option>
                      <option value="assessment">Assessment Complete</option>
                      <option value="review">Under Review</option>
                      <option value="planning">Planning</option>
                      <option value="approved">Approved</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">System</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Level</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dependencies</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Savings</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredSystems.map((system) => (
                      <tr key={system.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{system.name}</div>
                            <div className="text-sm text-gray-500">{system.id}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{system.type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{system.department}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            system.riskLevel === 'Very High' ? 'bg-red-100 text-red-800' :
                            system.riskLevel === 'High' ? 'bg-orange-100 text-orange-800' :
                            system.riskLevel === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {system.riskLevel}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{system.dependencies}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            system.status === 'Approved' ? 'bg-green-100 text-green-800' :
                            system.status === 'Assessment Complete' ? 'bg-blue-100 text-blue-800' :
                            system.status === 'Under Review' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {system.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                          {system.estimatedSavings}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DecommissionPlanning;
