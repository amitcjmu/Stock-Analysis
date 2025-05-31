
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { Calendar, Users, Target } from 'lucide-react';

const WavePlanning = () => {
  const waves = [
    {
      wave: 'W1',
      startDate: '2025-10-01',
      targetDate: '2025-10-15',
      groups: ['G1'],
      apps: 12,
      status: 'Planning'
    },
    {
      wave: 'W2',
      startDate: '2025-11-01', 
      targetDate: '2025-11-20',
      groups: ['G2', 'G3'],
      apps: 8,
      status: 'Scheduled'
    },
    {
      wave: 'W3',
      startDate: '2025-12-01',
      targetDate: '2025-12-15',
      groups: ['G4'],
      apps: 15,
      status: 'Draft'
    }
  ];

  const getStatusColor = (status) => {
    const colors = {
      'Planning': 'bg-blue-100 text-blue-800',
      'Scheduled': 'bg-green-100 text-green-800',
      'Draft': 'bg-gray-100 text-gray-800'
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Wave Planning</h1>
              <p className="text-gray-600">Plan migration waves and group applications</p>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Wave Planning - Live data integration expected September 2025
                </p>
              </div>
            </div>

            {/* Wave Planning Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {waves.map((wave) => (
                <div key={wave.wave} className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-2xl font-bold text-gray-900">{wave.wave}</h3>
                    <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(wave.status)}`}>
                      {wave.status}
                    </span>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <Calendar className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-700">Start Date</p>
                        <p className="text-sm text-gray-600">{wave.startDate}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <Target className="h-5 w-5 text-green-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-700">Target Date</p>
                        <p className="text-sm text-gray-600">{wave.targetDate}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <Users className="h-5 w-5 text-purple-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-700">Groups</p>
                        <p className="text-sm text-gray-600">{wave.groups.join(', ')}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Applications</span>
                      <span className="text-lg font-semibold text-gray-900">{wave.apps}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary Section */}
            <div className="mt-8 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Wave Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">3</p>
                  <p className="text-gray-600">Total Waves</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">35</p>
                  <p className="text-gray-600">Total Applications</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600">4</p>
                  <p className="text-gray-600">Application Groups</p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default WavePlanning;
