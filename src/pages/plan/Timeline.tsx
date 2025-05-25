
import React from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Calendar, CheckCircle, Clock, AlertCircle, Brain } from 'lucide-react';

const Timeline = () => {
  const milestones = [
    { name: 'Architecture Review', date: '2025-01-10', status: 'completed', wave: 'W1', duration: '3 days' },
    { name: 'Security Assessment', date: '2025-01-20', status: 'in-progress', wave: 'W1', duration: '5 days' },
    { name: 'Resource Allocation', date: '2025-02-01', status: 'pending', wave: 'W1', duration: '2 days' },
    { name: 'Testing Environment Setup', date: '2025-02-15', status: 'pending', wave: 'W1', duration: '7 days' },
    { name: 'Production Migration', date: '2025-03-15', status: 'pending', wave: 'W1', duration: '14 days' },
    { name: 'Wave 2 Assessment', date: '2025-04-01', status: 'planned', wave: 'W2', duration: '10 days' },
    { name: 'Wave 2 Migration', date: '2025-05-01', status: 'planned', wave: 'W2', duration: '21 days' }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in-progress':
        return <Clock className="h-5 w-5 text-blue-500" />;
      case 'pending':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'planned':
        return <Calendar className="h-5 w-5 text-gray-400" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'completed': 'bg-green-100 text-green-800',
      'in-progress': 'bg-blue-100 text-blue-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'planned': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Timeline</h1>
                  <p className="text-gray-600">Comprehensive project timeline with AI-optimized milestones</p>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>AI Optimize</span>
                </button>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> Timeline optimized with 1-week buffer for Wave 1 critical applications
                </p>
              </div>
            </div>

            {/* Timeline Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Duration</h3>
                <p className="text-3xl font-bold text-blue-600">120</p>
                <p className="text-sm text-gray-600">Days</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Completed</h3>
                <p className="text-3xl font-bold text-green-600">1</p>
                <p className="text-sm text-gray-600">Milestones</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">In Progress</h3>
                <p className="text-3xl font-bold text-blue-600">1</p>
                <p className="text-sm text-gray-600">Milestones</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Upcoming</h3>
                <p className="text-3xl font-bold text-orange-600">5</p>
                <p className="text-sm text-gray-600">Milestones</p>
              </div>
            </div>

            {/* Detailed Timeline */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Project Milestones</h2>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {milestones.map((milestone, index) => (
                    <div key={index} className="relative">
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0 mt-1">
                          {getStatusIcon(milestone.status)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-lg font-medium text-gray-900">{milestone.name}</h3>
                              <div className="flex items-center space-x-4 mt-1">
                                <span className="text-sm text-gray-600">{milestone.date}</span>
                                <span className="text-sm text-gray-500">Duration: {milestone.duration}</span>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  milestone.wave === 'W1' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                                }`}>
                                  {milestone.wave}
                                </span>
                              </div>
                            </div>
                            <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(milestone.status)}`}>
                              {milestone.status.replace('-', ' ')}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {index < milestones.length - 1 && (
                        <div className="absolute left-2.5 top-8 w-0.5 h-8 bg-gray-200"></div>
                      )}
                    </div>
                  ))}
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

export default Timeline;
