
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { DollarSign, TrendingDown, TrendingUp, AlertTriangle, Sparkles, Download } from 'lucide-react';

const CostAnalysis = () => {
  const costComparisonData = [
    {
      app: 'ERP System',
      currentCost: 45000,
      plannedCost: 32000,
      actualCost: 29500,
      variance: -2500,
      variancePercent: -7.8,
      status: 'Under Budget'
    },
    {
      app: 'CRM Platform',
      currentCost: 28000,
      plannedCost: 18000,
      actualCost: 19200,
      variance: 1200,
      variancePercent: 6.7,
      status: 'Over Budget'
    },
    {
      app: 'Analytics Suite',
      currentCost: 35000,
      plannedCost: 25000,
      actualCost: 24800,
      variance: -200,
      variancePercent: -0.8,
      status: 'On Target'
    },
    {
      app: 'HR Management',
      currentCost: 22000,
      plannedCost: 15000,
      actualCost: 14200,
      variance: -800,
      variancePercent: -5.3,
      status: 'Under Budget'
    },
    {
      app: 'Document System',
      currentCost: 18000,
      plannedCost: 12000,
      actualCost: 13500,
      variance: 1500,
      variancePercent: 12.5,
      status: 'Over Budget'
    },
    {
      app: 'Email Platform',
      currentCost: 15000,
      plannedCost: 8000,
      actualCost: 7500,
      variance: -500,
      variancePercent: -6.3,
      status: 'Under Budget'
    },
    {
      app: 'Database Cluster',
      currentCost: 52000,
      plannedCost: 38000,
      actualCost: 41000,
      variance: 3000,
      variancePercent: 7.9,
      status: 'Over Budget'
    },
    {
      app: 'Web Portal',
      currentCost: 25000,
      plannedCost: 16000,
      actualCost: 15200,
      variance: -800,
      variancePercent: -5.0,
      status: 'Under Budget'
    }
  ];

  const totalCurrentCost = costComparisonData.reduce((sum, app) => sum + app.currentCost, 0);
  const totalPlannedCost = costComparisonData.reduce((sum, app) => sum + app.plannedCost, 0);
  const totalActualCost = costComparisonData.reduce((sum, app) => sum + app.actualCost, 0);
  const totalVariance = totalActualCost - totalPlannedCost;
  const totalVariancePercent = ((totalVariance / totalPlannedCost) * 100);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Under Budget':
        return 'bg-green-100 text-green-800';
      case 'Over Budget':
        return 'bg-red-100 text-red-800';
      case 'On Target':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getVarianceIcon = (variance) => {
    if (variance < 0) {
      return <TrendingDown className="h-4 w-4 text-green-500" />;
    } else if (variance > 0) {
      return <TrendingUp className="h-4 w-4 text-red-500" />;
    }
    return <div className="h-4 w-4"></div>;
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Cost Analysis Dashboard</h1>
                  <p className="text-gray-600">Compare current, planned, and actual migration costs by application</p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Analysis</span>
                  </button>
                  <button className="bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 flex items-center space-x-2">
                    <Download className="h-4 w-4" />
                    <span>Export Report</span>
                  </button>
                </div>
              </div>
            </div>

            {/* AI Insights Banner */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Sparkles className="h-6 w-6 text-orange-600" />
                <h3 className="text-lg font-semibold text-gray-900">AI Cost Optimization Insights</h3>
              </div>
              <p className="text-orange-800 mb-3">
                3 applications are over budget by 8.9% on average. Document System shows highest variance at +12.5%. 
                AI recommends rightsizing instances for CRM Platform and Database Cluster to reduce costs by $3,200/month.
              </p>
              <div className="text-sm text-orange-600">
                Overall performance: 1.2% over planned budget | Risk level: Medium | Optimization potential: $38,400 annually
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-gray-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalCurrentCost)}</p>
                    <p className="text-gray-600">Current Costs</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalPlannedCost)}</p>
                    <p className="text-gray-600">Planned Costs</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-green-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalActualCost)}</p>
                    <p className="text-gray-600">Actual Costs</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${totalVariance < 0 ? 'bg-green-500' : 'bg-red-500'}`}>
                    {totalVariance < 0 ? <TrendingDown className="h-6 w-6 text-white" /> : <TrendingUp className="h-6 w-6 text-white" />}
                  </div>
                  <div className="ml-4">
                    <p className={`text-2xl font-semibold ${totalVariance < 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {totalVariancePercent > 0 ? '+' : ''}{totalVariancePercent.toFixed(1)}%
                    </p>
                    <p className="text-gray-600">Budget Variance</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Cost Comparison Table */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Application Cost Comparison</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Current Cost</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Planned Cost</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Cost</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance %</th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costComparisonData.map((app, index) => (
                      <tr key={app.app} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{app.app}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{formatCurrency(app.currentCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{formatCurrency(app.plannedCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">{formatCurrency(app.actualCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                          <div className="flex items-center justify-end space-x-1">
                            {getVarianceIcon(app.variance)}
                            <span className={`font-semibold ${app.variance < 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(Math.abs(app.variance))}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                          <span className={`font-semibold ${app.variance < 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {app.variancePercent > 0 ? '+' : ''}{app.variancePercent.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(app.status)}`}>
                            {app.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">Total</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right">{formatCurrency(totalCurrentCost)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right">{formatCurrency(totalPlannedCost)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right">{formatCurrency(totalActualCost)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-right">
                        <span className={`${totalVariance < 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(Math.abs(totalVariance))}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-right">
                        <span className={`${totalVariance < 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {totalVariancePercent > 0 ? '+' : ''}{totalVariancePercent.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          Math.abs(totalVariancePercent) <= 5 ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {Math.abs(totalVariancePercent) <= 5 ? 'Within Range' : 'Needs Review'}
                        </span>
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* AI Recommendations */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">AI-Powered Cost Optimization Recommendations</h2>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div className="border-l-4 border-red-400 bg-red-50 p-4">
                    <div className="flex">
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                      <div className="ml-3">
                        <p className="text-sm text-red-700">
                          <strong>High Priority:</strong> Document System is 12.5% over budget. Consider migrating to serverless architecture to reduce costs by ~$1,800/month.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="border-l-4 border-yellow-400 bg-yellow-50 p-4">
                    <div className="flex">
                      <AlertTriangle className="h-5 w-5 text-yellow-400" />
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700">
                          <strong>Medium Priority:</strong> Database Cluster shows consistent over-utilization. Recommend instance rightsizing to save $2,400/month.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="border-l-4 border-green-400 bg-green-50 p-4">
                    <div className="flex">
                      <TrendingDown className="h-5 w-5 text-green-400" />
                      <div className="ml-3">
                        <p className="text-sm text-green-700">
                          <strong>Success Story:</strong> ERP System achieved 7.8% cost reduction through optimized resource allocation and reserved instances.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="border-l-4 border-blue-400 bg-blue-50 p-4">
                    <div className="flex">
                      <DollarSign className="h-5 w-5 text-blue-400" />
                      <div className="ml-3">
                        <p className="text-sm text-blue-700">
                          <strong>Opportunity:</strong> Implement automated scaling for Web Portal and Analytics Suite to capture additional 15% savings during off-peak hours.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default CostAnalysis;
