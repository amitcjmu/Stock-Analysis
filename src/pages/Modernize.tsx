
import React from 'react';
import Sidebar from '../components/Sidebar';
import FeedbackWidget from '../components/FeedbackWidget';
import { Sparkles, Zap, Layers } from 'lucide-react';

const Modernize = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-4xl mx-auto text-center">
            <div className="bg-white rounded-lg shadow-lg p-12">
              <div className="mb-8">
                <Sparkles className="h-24 w-24 text-gray-400 mx-auto mb-6" />
                <h1 className="text-4xl font-bold text-gray-900 mb-4">Modernize Phase</h1>
                <p className="text-xl text-gray-600 mb-8">
                  Coming Soon: Powered by CloudBridge
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div className="text-center">
                  <Zap className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Application Modernization</h3>
                  <p className="text-gray-600">Modernize applications post-migration</p>
                </div>
                <div className="text-center">
                  <Layers className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Cloud-Native Services</h3>
                  <p className="text-gray-600">Leverage cloud-native services and patterns</p>
                </div>
                <div className="text-center">
                  <Sparkles className="h-12 w-12 text-purple-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Performance Optimization</h3>
                  <p className="text-gray-600">Optimize performance and reduce technical debt</p>
                </div>
              </div>

              <div className="bg-gray-200 text-gray-500 rounded-lg p-8">
                <p className="text-lg">
                  This feature will provide comprehensive modernization tools, including containerization, 
                  microservices transformation, and cloud-native optimization capabilities.
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

export default Modernize;
