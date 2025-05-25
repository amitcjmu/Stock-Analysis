
import React from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Calendar, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const Roadmap = () => {
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in-progress':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'planned':
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'completed': 'bg-green-500',
      'in-progress': 'bg-blue-500',
      'planned': 'bg-gray-300'
    };
    return colors[status] || 'bg-gray-300';
  };

  const getProgressWidth = (status) => {
    switch (status) {
      case 'completed':
        return 'w-full';
      case 'in-progress':
        return 'w-1/2';
      case 'planned':
        return 'w-0';
      default:
        return 'w-0';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Roadmap</h1>
              <p className="text-gray-600">View timeline and milestones for migration waves</p>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Roadmap - Live data integration expected September 2025
                </p>
              </div>
            </div>

            {/* Roadmap Timeline */}
            <div className="space-y-8">
              {roadmapData.map((wave) => (
                <div key={wave.wave} className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">{wave.wave} Migration Timeline</h2>
                  
                  <div className="space-y-6">
                    {wave.phases.map((phase, index) => (
                      <div key={phase.name} className="relative">
                        <div className="flex items-center space-x-4">
                          {getStatusIcon(phase.status)}
                          <div className="flex-1">
                            <div className="flex justify-between items-center mb-2">
                              <h3 className="text-lg font-medium text-gray-900">{phase.name}</h3>
                              <span className="text-sm text-gray-500">
                                {phase.start} - {phase.end}
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-3">
                              <div className={`h-3 rounded-full transition-all duration-300 ${getStatusColor(phase.status)} ${getProgressWidth(phase.status)}`}></div>
                            </div>
                          </div>
                        </div>
                        
                        {index < wave.phases.length - 1 && (
                          <div className="absolute left-2 top-8 w-0.5 h-8 bg-gray-200"></div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Timeline Overview */}
            <div className="mt-8 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Overall Timeline</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">Q4 2025</h3>
                    <p className="text-sm text-gray-600">Wave 1 & 2 Migration</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">20 Apps</p>
                    <p className="text-sm text-gray-600">Scheduled</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">Q1 2026</h3>
                    <p className="text-sm text-gray-600">Wave 3 Planning</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">15 Apps</p>
                    <p className="text-sm text-gray-600">In Planning</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default Roadmap;
