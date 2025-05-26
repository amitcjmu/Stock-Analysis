
import React from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { TrendingUp, TrendingDown, Download, Sparkles, Calendar } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area } from 'recharts';

const CostTrends = () => {
  const monthlyTrends = [
    { month: 'Jan', planned: 45000, actual: 42000, forecast: 48000 },
    { month: 'Feb', planned: 52000, actual: 49000, forecast: 55000 },
    { month: 'Mar', planned: 48000, actual: 46000, forecast: 51000 },
    { month: 'Apr', planned: 58000, actual: 55000, forecast: 62000 },
    { month: 'May', planned: 62000, actual: 58000, forecast: 65000 },
    { month: 'Jun', planned: 55000, actual: 52000, forecast: 58000 },
    { month: 'Jul', planned: 67000, actual: 63000, forecast: 70000 },
    { month: 'Aug', planned: 71000, actual: 68000, forecast: 74000 },
    { month: 'Sep', planned: 65000, actual: 62000, forecast: 68000 },
    { month: 'Oct', planned: 73000, actual: 69000, forecast: 76000 },
    { month: 'Nov', planned: 78000, actual: 74000, forecast: 81000 },
    { month: 'Dec', planned: 72000, actual: 68000, forecast: 75000 }
  ];

  const savingsData = [
    { month: 'Jan', savings: 3000, percentage: 6.7 },
    { month: 'Feb', savings: 3000, percentage: 5.8 },
    { month: 'Mar', savings: 2000, percentage: 4.2 },
    { month: 'Apr', savings: 3000, percentage: 5.2 },
    { month: 'May', savings: 4000, percentage: 6.5 },
    { month: 'Jun', savings: 3000, percentage: 5.5 },
    { month: 'Jul', savings: 4000, percentage: 6.0 },
    { month: 'Aug', savings: 3000, percentage: 4.2 },
    { month: 'Sep', savings: 3000, percentage: 4.6 },
    { month: 'Oct', savings: 4000, percentage: 5.5 },
    { month: 'Nov', savings: 4000, percentage: 5.1 },
    { month: 'Dec', savings: 4000, percentage: 5.6 }
  ];

  const chartConfig = {
    planned: { label: "Planned", color: "#3b82f6" },
    actual: { label: "Actual", color: "#10b981" },
    forecast: { label: "Forecast", color: "#f59e0b" },
    savings: { label: "Savings", color: "#8b5cf6" },
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const totalSavings = savingsData.reduce((sum, month) => sum + month.savings, 0);
  const avgSavingsPercentage = Math.round(savingsData.reduce((sum, month) => sum + month.percentage, 0) / savingsData.length * 10) / 10;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Cost Trend Analysis</h1>
                  <p className="text-gray-600">Monitor cost trends and identify optimization opportunities</p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Insights</span>
                  </button>
                  <button className="bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 flex items-center space-x-2">
                    <Download className="h-4 w-4" />
                    <span>Export Report</span>
                  </button>
                </div>
              </div>
            </div>

            {/* AI Insights Banner */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Sparkles className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">AI Cost Trend Insights</h3>
              </div>
              <p className="text-blue-800 mb-3">
                Cost trends show consistent 5.5% savings vs planned budget. Peak costs in Q4 driven by Wave 3 completion. 
                AI recommends optimizing compute instances in Dec to reduce forecast by additional 8%.
              </p>
              <div className="text-sm text-blue-600">
                Trend: Stable downward variance | Risk Level: Low | Optimization Potential: $6,200/month
              </div>
            </div>

            {/* Trend Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-green-500 p-3 rounded-lg">
                    <TrendingDown className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalSavings)}</p>
                    <p className="text-gray-600">Total YTD Savings</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{avgSavingsPercentage}%</p>
                    <p className="text-gray-600">Avg Savings Rate</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-purple-500 p-3 rounded-lg">
                    <Calendar className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">12</p>
                    <p className="text-gray-600">Months Tracked</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-orange-500 p-3 rounded-lg">
                    <TrendingDown className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">4.2%</p>
                    <p className="text-gray-600">Best Month Savings</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Cost Trends Chart */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Monthly Cost Trends</h2>
              </div>
              <div className="p-6">
                <ChartContainer config={chartConfig} className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={monthlyTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Line type="monotone" dataKey="planned" stroke="var(--color-planned)" strokeWidth={2} strokeDasharray="5 5" />
                      <Line type="monotone" dataKey="actual" stroke="var(--color-actual)" strokeWidth={3} />
                      <Line type="monotone" dataKey="forecast" stroke="var(--color-forecast)" strokeWidth={2} strokeDasharray="3 3" />
                    </LineChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </div>

            {/* Savings Trend Chart */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Monthly Savings Trend</h2>
              </div>
              <div className="p-6">
                <ChartContainer config={chartConfig} className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={savingsData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Area type="monotone" dataKey="savings" stroke="var(--color-savings)" fill="var(--color-savings)" fillOpacity={0.6} />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </div>

            {/* Trends Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Monthly Cost Details</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Month</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Planned</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actual</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Forecast</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Savings</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Variance %</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {monthlyTrends.map((month, index) => {
                      const savings = savingsData[index];
                      return (
                        <tr key={month.month} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{month.month}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(month.planned)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">{formatCurrency(month.actual)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(month.forecast)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">{formatCurrency(savings.savings)}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                              -{savings.percentage}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default CostTrends;
