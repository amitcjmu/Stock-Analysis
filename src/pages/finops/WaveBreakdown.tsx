
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { BarChart3, Download, Sparkles, TrendingUp, DollarSign } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const WaveBreakdown = () => {
  const waveData = [
    {
      wave: 'Wave 1',
      compute: 18000,
      storage: 3500,
      networking: 1200,
      licensing: 5000,
      support: 2300,
      total: 30000,
      apps: 12,
      status: 'Complete'
    },
    {
      wave: 'Wave 2',
      compute: 14000,
      storage: 2800,
      networking: 1000,
      licensing: 3000,
      support: 1700,
      total: 22500,
      apps: 8,
      status: 'Complete'
    },
    {
      wave: 'Wave 3',
      compute: 22000,
      storage: 4200,
      networking: 1500,
      licensing: 8000,
      support: 2800,
      total: 38500,
      apps: 15,
      status: 'In Progress'
    },
    {
      wave: 'Wave 4',
      compute: 16000,
      storage: 3000,
      networking: 1100,
      licensing: 4500,
      support: 2000,
      total: 26600,
      apps: 10,
      status: 'Planned'
    }
  ];

  const categoryData = [
    { name: 'Compute', value: 70000, color: '#3b82f6' },
    { name: 'Storage', value: 13500, color: '#10b981' },
    { name: 'Networking', value: 4800, color: '#f59e0b' },
    { name: 'Licensing', value: 20500, color: '#8b5cf6' },
    { name: 'Support', value: 8800, color: '#ef4444' }
  ];

  const chartConfig = {
    compute: { label: "Compute", color: "#3b82f6" },
    storage: { label: "Storage", color: "#10b981" },
    networking: { label: "Networking", color: "#f59e0b" },
    licensing: { label: "Licensing", color: "#8b5cf6" },
    support: { label: "Support", color: "#ef4444" },
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const totalCost = waveData.reduce((sum, wave) => sum + wave.total, 0);
  const totalApps = waveData.reduce((sum, wave) => sum + wave.apps, 0);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Cost Breakdown by Wave</h1>
                  <p className="text-gray-600">Detailed cost analysis across migration waves and categories</p>
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

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
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
                  <div className="bg-green-500 p-3 rounded-lg">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{totalApps}</p>
                    <p className="text-gray-600">Total Applications</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-purple-500 p-3 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">4</p>
                    <p className="text-gray-600">Migration Waves</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-orange-500 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(Math.round(totalCost / totalApps))}</p>
                    <p className="text-gray-600">Avg Cost per App</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Wave Cost Breakdown Chart */}
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Cost Breakdown by Wave</h2>
                </div>
                <div className="p-6">
                  <ChartContainer config={chartConfig} className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={waveData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="wave" />
                        <YAxis />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Bar dataKey="compute" stackId="a" fill="var(--color-compute)" />
                        <Bar dataKey="storage" stackId="a" fill="var(--color-storage)" />
                        <Bar dataKey="networking" stackId="a" fill="var(--color-networking)" />
                        <Bar dataKey="licensing" stackId="a" fill="var(--color-licensing)" />
                        <Bar dataKey="support" stackId="a" fill="var(--color-support)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </div>
              </div>

              {/* Cost Categories Pie Chart */}
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Cost Distribution by Category</h2>
                </div>
                <div className="p-6">
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Detailed Wave Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Detailed Wave Cost Breakdown</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Wave</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Apps</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Compute</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Storage</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Networking</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Licensing</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Support</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {waveData.map((wave) => (
                      <tr key={wave.wave} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{wave.wave}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{wave.apps}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.compute)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.storage)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.networking)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.licensing)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(wave.support)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{formatCurrency(wave.total)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            wave.status === 'Complete' ? 'bg-green-100 text-green-800' :
                            wave.status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
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

export default WaveBreakdown;
