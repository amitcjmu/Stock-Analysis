
import React from 'react';
import { Link } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import { BarChart3, Calendar, Filter, Download, ClipboardList, Route, Edit, ArrowRight } from 'lucide-react';

const AssessIndex = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Assessment Overview</h1>
              <p className="text-gray-600">6R treatments, migration grouping, and wave planning dashboard</p>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> Powered by CloudBridge - Live data integration expected September 2025
                </p>
              </div>
            </div>

            {/* Summary Cards */}
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

            {/* Quick Navigation Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Link to="/assess/treatment" className="group">
                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
                  <div className="flex items-center justify-between mb-4">
                    <ClipboardList className="h-8 w-8 text-blue-500" />
                    <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500 transition-colors duration-200" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">6R Treatment Analysis</h3>
                  <p className="text-gray-600 text-sm">Analyze applications and assign 6R migration strategies</p>
                </div>
              </Link>

              <Link to="/assess/waveplanning" className="group">
                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
                  <div className="flex items-center justify-between mb-4">
                    <Calendar className="h-8 w-8 text-green-500" />
                    <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-green-500 transition-colors duration-200" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Wave Planning</h3>
                  <p className="text-gray-600 text-sm">Plan migration waves and group applications</p>
                </div>
              </Link>

              <Link to="/assess/roadmap" className="group">
                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
                  <div className="flex items-center justify-between mb-4">
                    <Route className="h-8 w-8 text-purple-500" />
                    <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-purple-500 transition-colors duration-200" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Migration Roadmap</h3>
                  <p className="text-gray-600 text-sm">View timeline and milestones for migration waves</p>
                </div>
              </Link>

              <Link to="/assess/editor" className="group">
                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
                  <div className="flex items-center justify-between mb-4">
                    <Edit className="h-8 w-8 text-orange-500" />
                    <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-orange-500 transition-colors duration-200" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Application Editor</h3>
                  <p className="text-gray-600 text-sm">Quick edit application details and configurations</p>
                </div>
              </Link>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AssessIndex;
