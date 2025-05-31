
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { DollarSign, TrendingUp, Cloud, Sparkles, Download, CheckCircle } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';

const CloudComparison = () => {
  const providerData = [
    {
      provider: 'AWS',
      compute: 45000,
      storage: 8000,
      networking: 3500,
      licensing: 12000,
      total: 68500,
      aiScore: 94,
      features: ['Best for Enterprise', 'Mature Services', 'Global Reach'],
      recommended: true
    },
    {
      provider: 'Azure',
      compute: 42000,
      storage: 7500,
      networking: 3200,
      licensing: 10000,
      total: 62700,
      aiScore: 91,
      features: ['Microsoft Integration', 'Hybrid Cloud', 'AD Integration'],
      recommended: false
    },
    {
      provider: 'GCP',
      compute: 38000,
      storage: 6800,
      networking: 2800,
      licensing: 9500,
      total: 57100,
      aiScore: 88,
      features: ['ML/AI Services', 'Competitive Pricing', 'Innovation'],
      recommended: false
    }
  ];

  const chartData = providerData.map(provider => ({
    provider: provider.provider,
    compute: provider.compute,
    storage: provider.storage,
    networking: provider.networking,
    licensing: provider.licensing
  }));

  const chartConfig = {
    compute: {
      label: "Compute",
      color: "#3b82f6",
    },
    storage: {
      label: "Storage", 
      color: "#10b981",
    },
    networking: {
      label: "Networking",
      color: "#f59e0b",
    },
    licensing: {
      label: "Licensing",
      color: "#ef4444",
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Cloud Provider Cost Comparison</h1>
                  <p className="text-gray-600">AI-powered analysis of cloud provider costs for your migration</p>
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

            {/* AI Recommendation Banner */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Sparkles className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">AI Recommendation</h3>
              </div>
              <p className="text-blue-800 mb-3">
                Based on your application portfolio and migration requirements, AWS offers the best value proposition with 94% compatibility score. 
                Estimated 3-year TCO savings of $127,000 compared to on-premises infrastructure.
              </p>
              <div className="text-sm text-blue-600">
                Analysis factors: Application compatibility, licensing optimization, regional presence | Confidence: 96%
              </div>
            </div>

            {/* Provider Comparison Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {providerData.map((provider) => (
                <div key={provider.provider} className={`bg-white rounded-lg shadow-lg p-6 ${provider.recommended ? 'ring-2 ring-blue-500' : ''}`}>
                  {provider.recommended && (
                    <div className="flex items-center justify-center mb-4">
                      <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold flex items-center">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        AI Recommended
                      </span>
                    </div>
                  )}
                  <div className="text-center mb-6">
                    <Cloud className="h-12 w-12 mx-auto mb-3 text-blue-600" />
                    <h3 className="text-xl font-bold text-gray-900">{provider.provider}</h3>
                    <p className="text-3xl font-bold text-blue-600 mt-2">{formatCurrency(provider.total)}</p>
                    <p className="text-sm text-gray-600">Annual Cost</p>
                  </div>
                  
                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between">
                      <span className="text-gray-600">AI Compatibility Score</span>
                      <span className="font-semibold text-green-600">{provider.aiScore}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Compute</span>
                      <span className="font-semibold">{formatCurrency(provider.compute)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Storage</span>
                      <span className="font-semibold">{formatCurrency(provider.storage)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Networking</span>
                      <span className="font-semibold">{formatCurrency(provider.networking)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Licensing</span>
                      <span className="font-semibold">{formatCurrency(provider.licensing)}</span>
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Key Features</h4>
                    <ul className="space-y-1">
                      {provider.features.map((feature, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-center">
                          <CheckCircle className="h-3 w-3 text-green-500 mr-2" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            {/* Cost Breakdown Chart */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Cost Breakdown by Provider</h2>
              </div>
              <div className="p-6">
                <ChartContainer config={chartConfig} className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="provider" />
                      <YAxis />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="compute" stackId="a" fill="var(--color-compute)" />
                      <Bar dataKey="storage" stackId="a" fill="var(--color-storage)" />
                      <Bar dataKey="networking" stackId="a" fill="var(--color-networking)" />
                      <Bar dataKey="licensing" stackId="a" fill="var(--color-licensing)" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>
            </div>

            {/* Decision Matrix */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">AI Decision Matrix</h2>
              </div>
              <div className="p-6">
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-4 font-semibold">Criteria</th>
                        <th className="text-center py-3 px-4 font-semibold">AWS</th>
                        <th className="text-center py-3 px-4 font-semibold">Azure</th>
                        <th className="text-center py-3 px-4 font-semibold">GCP</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="py-3 px-4">Total Cost (Annual)</td>
                        <td className="text-center py-3 px-4 text-orange-600 font-semibold">{formatCurrency(68500)}</td>
                        <td className="text-center py-3 px-4 text-yellow-600 font-semibold">{formatCurrency(62700)}</td>
                        <td className="text-center py-3 px-4 text-green-600 font-semibold">{formatCurrency(57100)}</td>
                      </tr>
                      <tr className="border-b">
                        <td className="py-3 px-4">Application Compatibility</td>
                        <td className="text-center py-3 px-4"><span className="text-green-600 font-semibold">Excellent</span></td>
                        <td className="text-center py-3 px-4"><span className="text-blue-600 font-semibold">Good</span></td>
                        <td className="text-center py-3 px-4"><span className="text-yellow-600 font-semibold">Fair</span></td>
                      </tr>
                      <tr className="border-b">
                        <td className="py-3 px-4">Migration Complexity</td>
                        <td className="text-center py-3 px-4"><span className="text-green-600 font-semibold">Low</span></td>
                        <td className="text-center py-3 px-4"><span className="text-yellow-600 font-semibold">Medium</span></td>
                        <td className="text-center py-3 px-4"><span className="text-orange-600 font-semibold">High</span></td>
                      </tr>
                      <tr>
                        <td className="py-3 px-4">Support & SLA</td>
                        <td className="text-center py-3 px-4"><span className="text-green-600 font-semibold">Excellent</span></td>
                        <td className="text-center py-3 px-4"><span className="text-green-600 font-semibold">Excellent</span></td>
                        <td className="text-center py-3 px-4"><span className="text-blue-600 font-semibold">Good</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default CloudComparison;
