
import React from 'react';
import Sidebar from '../components/Sidebar';
import FeedbackWidget from '../components/FeedbackWidget';
import { Archive, Shield, Trash2 } from 'lucide-react';

const Decommission = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-4xl mx-auto text-center">
            <div className="bg-white rounded-lg shadow-lg p-12">
              <div className="mb-8">
                <Archive className="h-24 w-24 text-gray-400 mx-auto mb-6" />
                <h1 className="text-4xl font-bold text-gray-900 mb-4">Decommission Phase</h1>
                <p className="text-xl text-gray-600 mb-8">
                  Coming Soon: Powered by CloudBridge
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div className="text-center">
                  <Shield className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Safe Decommissioning</h3>
                  <p className="text-gray-600">Safely decommission legacy systems</p>
                </div>
                <div className="text-center">
                  <Archive className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Data Archival</h3>
                  <p className="text-gray-600">Archive important data and maintain compliance</p>
                </div>
                <div className="text-center">
                  <Trash2 className="h-12 w-12 text-red-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Resource Cleanup</h3>
                  <p className="text-gray-600">Clean up resources and optimize costs</p>
                </div>
              </div>

              <div className="bg-gray-200 text-gray-500 rounded-lg p-8">
                <p className="text-lg">
                  This feature will provide controlled decommissioning processes, including 
                  data retention strategies, compliance management, and resource optimization.
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

export default Decommission;
