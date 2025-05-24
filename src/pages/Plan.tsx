
import React from 'react';
import Sidebar from '../components/Sidebar';
import FeedbackWidget from '../components/FeedbackWidget';
import { Building2, Calendar, Users } from 'lucide-react';

const Plan = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-4xl mx-auto text-center">
            <div className="bg-white rounded-lg shadow-lg p-12">
              <div className="mb-8">
                <Building2 className="h-24 w-24 text-gray-400 mx-auto mb-6" />
                <h1 className="text-4xl font-bold text-gray-900 mb-4">Plan Phase</h1>
                <p className="text-xl text-gray-600 mb-8">
                  Coming Soon: Powered by CloudBridge
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div className="text-center">
                  <Calendar className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Migration Planning</h3>
                  <p className="text-gray-600">Create detailed migration plans and timelines</p>
                </div>
                <div className="text-center">
                  <Users className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Resource Allocation</h3>
                  <p className="text-gray-600">Assign teams and resources to migration tasks</p>
                </div>
                <div className="text-center">
                  <Building2 className="h-12 w-12 text-purple-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Architecture Design</h3>
                  <p className="text-gray-600">Design target cloud architecture and patterns</p>
                </div>
              </div>

              <div className="bg-gray-200 text-gray-500 rounded-lg p-8">
                <p className="text-lg">
                  This feature will provide comprehensive migration planning tools, including 
                  detailed project timelines, resource management, and architecture design capabilities.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default Plan;
