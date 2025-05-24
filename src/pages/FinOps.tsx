
import React from 'react';
import Sidebar from '../components/Sidebar';
import FeedbackWidget from '../components/FeedbackWidget';
import { DollarSign, TrendingUp, AlertTriangle, Download } from 'lucide-react';

const FinOps = () => {
  const costData = [
    {
      wave: 'W1',
      computeCost: 20000,
      licensingCost: 5000,
      totalCost: 25000,
      forecast: 30000,
      apps: 12,
      savings: 15
    },
    {
      wave: 'W2', 
      computeCost: 15000,
      licensingCost: 3000,
      totalCost: 18000,
      forecast: 20000,
      apps: 8,
      savings: 22
    },
    {
      wave: 'W3',
      computeCost: 25000,
      licensingCost: 8000,
      totalCost: 33000,
      forecast: 35000,
      apps: 15,
      savings: 18
    }
  ];

  const totalCost = costData.reduce((sum, wave) => sum + wave.totalCost, 0);
  const totalForecast = costData.reduce((sum, wave) => sum + wave.forecast, 0);
  const avgSavings = Math.round(costData.reduce((sum, wave) => sum + wave.savings, 0) / costData.length);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">FinOps Dashboard</h1>
              <p className="text-gray-600">Track costs and optimize financial operations across migration waves</p>
            </div>

            {/* Cost Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-green-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalCost)}</p>
                    <p className="text-gray-600">Total Migration Cost</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalForecast)}</p>
                    <p className="text-gray-600">Forecast Total</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-yellow-500 p-3 rounded-lg">
                    <AlertTriangle className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{avgSavings}%</p>
                    <p className="text-gray-600">Avg Cost Savings</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-purple-500 p-3 rounded-lg">
                    <Download className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">3</p>
                    <p className="text-gray-600">Active Waves</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Cost Breakdown Table */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-gray-900">Cost Breakdown by Wave</h2>
                  <button className="bg-yellow-500 text-white px-4 py-2 rounded-md hover:bg-yellow-600 flex items-center space-x-2">
                    <Download className="h-4 w-4" />
                    <span>Export Report</span>
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-yellow-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Wave</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applications</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Compute Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Licensing Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Forecast</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Savings %</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costData.map((wave, index) => (
                      <tr key={wave.wave} className="hover:bg-yellow-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{wave.wave}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{wave.apps}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.computeCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.licensingCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{formatCurrency(wave.totalCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.forecast)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            {wave.savings}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">Total</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        {costData.reduce((sum, wave) => sum + wave.apps, 0)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        {formatCurrency(costData.reduce((sum, wave) => sum + wave.computeCost, 0))}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        {formatCurrency(costData.reduce((sum, wave) => sum + wave.licensingCost, 0))}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{formatCurrency(totalCost)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{formatCurrency(totalForecast)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">{avgSavings}%</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Cost Analysis Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Cost Trend Analysis</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {costData.map((wave, index) => (
                      <div key={wave.wave} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                            <span className="text-sm font-semibold text-yellow-800">{wave.wave}</span>
                          </div>
                          <span className="font-medium">{wave.wave} - {wave.apps} apps</span>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold">{formatCurrency(wave.totalCost)}</div>
                          <div className="text-sm text-gray-500">vs {formatCurrency(wave.forecast)} forecast</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Budget Alerts</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="border-l-4 border-yellow-400 bg-yellow-50 p-4">
                      <div className="flex">
                        <AlertTriangle className="h-5 w-5 text-yellow-400" />
                        <div className="ml-3">
                          <p className="text-sm text-yellow-700">
                            <strong>W3 Budget Warning:</strong> Projected costs exceed budget by 5.7%
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="border-l-4 border-green-400 bg-green-50 p-4">
                      <div className="flex">
                        <TrendingUp className="h-5 w-5 text-green-400" />
                        <div className="ml-3">
                          <p className="text-sm text-green-700">
                            <strong>W1 On Track:</strong> Migration costs are 12% under budget
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="border-l-4 border-blue-400 bg-blue-50 p-4">
                      <div className="flex">
                        <DollarSign className="h-5 w-5 text-blue-400" />
                        <div className="ml-3">
                          <p className="text-sm text-blue-700">
                            <strong>Cost Optimization:</strong> Potential 8% savings identified in W2
                          </p>
                        </div>
                      </div>
                    </div>
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

export default FinOps;
