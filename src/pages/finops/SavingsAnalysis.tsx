
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { TrendingUp, DollarSign, Sparkles, Download, Target } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area } from 'recharts';

const SavingsAnalysis = () => {
  const savingsData = [
    { wave: 'Baseline', month: 0, operational: 0, licensing: 0, infrastructure: 0, total: 0 },
    { wave: 'W1 Start', month: 3, operational: 12000, licensing: 8000, infrastructure: 15000, total: 35000 },
    { wave: 'W1 Complete', month: 6, operational: 28000, licensing: 18000, infrastructure: 32000, total: 78000 },
    { wave: 'W2 Start', month: 9, operational: 45000, licensing: 25000, infrastructure: 48000, total: 118000 },
    { wave: 'W2 Complete', month: 12, operational: 67000, licensing: 38000, infrastructure: 72000, total: 177000 },
    { wave: 'W3 Start', month: 15, operational: 82000, licensing: 45000, infrastructure: 89000, total: 216000 },
    { wave: 'W3 Complete', month: 18, operational: 125000, licensing: 68000, infrastructure: 135000, total: 328000 },
    { wave: 'Ongoing', month: 24, operational: 158000, licensing: 85000, infrastructure: 172000, total: 415000 }
  ];

  const waveMetrics = [
    {
      wave: 'Wave 1',
      apps: 12,
      currentCost: 85000,
      projectedSavings: 78000,
      actualSavings: 82000,
      roi: 245,
      status: 'Complete'
    },
    {
      wave: 'Wave 2', 
      apps: 8,
      currentCost: 62000,
      projectedSavings: 99000,
      actualSavings: 95000,
      roi: 312,
      status: 'Complete'
    },
    {
      wave: 'Wave 3',
      apps: 15,
      currentCost: 95000,
      projectedSavings: 151000,
      actualSavings: 148000,
      roi: 278,
      status: 'In Progress'
    }
  ];

  const chartConfig = {
    operational: {
      label: "Operational Savings",
      color: "#10b981",
    },
    licensing: {
      label: "Licensing Savings",
      color: "#3b82f6",
    },
    infrastructure: {
      label: "Infrastructure Savings",
      color: "#f59e0b",
    },
    total: {
      label: "Total Savings",
      color: "#8b5cf6",
    },
  };

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
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Operational Savings Analysis</h1>
                  <p className="text-gray-600">Track cost savings and ROI across migration waves</p>
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
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Sparkles className="h-6 w-6 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">AI Savings Insights</h3>
              </div>
              <p className="text-green-800 mb-3">
                Migration is exceeding projected savings by 8.2%. Wave 2 delivered highest ROI at 312%. 
                AI recommends accelerating Wave 3 completion to capture additional $47,000 in Q4 savings.
              </p>
              <div className="text-sm text-green-600">
                Projected annual savings: $415,000 | Current achievement: 96% of target | Trend: Positive
              </div>
            </div>

            {/* Savings Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-green-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(328000)}</p>
                    <p className="text-gray-600">Total Savings YTD</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">278%</p>
                    <p className="text-gray-600">Average ROI</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-purple-500 p-3 rounded-lg">
                    <Target className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">96%</p>
                    <p className="text-gray-600">Target Achievement</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-yellow-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(87000)}</p>
                    <p className="text-gray-600">Projected Q4 Savings</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Savings Timeline Chart */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Cumulative Savings Timeline</h2>
              </div>
              <div className="p-6">
                <ChartContainer config={chartConfig} className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={savingsData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Area type="monotone" dataKey="infrastructure" stackId="1" stroke="var(--color-infrastructure)" fill="var(--color-infrastructure)" />
                      <Area type="monotone" dataKey="licensing" stackId="1" stroke="var(--color-licensing)" fill="var(--color-licensing)" />
                      <Area type="monotone" dataKey="operational" stackId="1" stroke="var(--color-operational)" fill="var(--color-operational)" />
                      <Line type="monotone" dataKey="total" stroke="var(--color-total)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </div>

            {/* Wave Performance Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Savings by Wave Performance</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Wave</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applications</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Projected Savings</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Savings</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ROI %</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {waveMetrics.map((wave, index) => (
                      <tr key={wave.wave} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{wave.wave}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{wave.apps}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.currentCost)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.projectedSavings)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">{formatCurrency(wave.actualSavings)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-blue-600">{wave.roi}%</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            wave.status === 'Complete' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {wave.status}
                          </span>
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

export default SavingsAnalysis;
