
import React from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { AlertTriangle, CheckCircle, XCircle, Bell, Settings, Download } from 'lucide-react';

const BudgetAlerts = () => {
  const alerts = [
    {
      id: 1,
      type: 'critical',
      title: 'Wave 3 Budget Exceeded',
      description: 'Current costs are 12% over the allocated budget for Wave 3 migration',
      impact: 'High',
      amount: 4500,
      threshold: 90,
      current: 112,
      category: 'Migration',
      date: '2024-01-15',
      status: 'active'
    },
    {
      id: 2,
      type: 'warning',
      title: 'Compute Costs Rising',
      description: 'EC2 instances costs trending 8% above forecast in the last 30 days',
      impact: 'Medium',
      amount: 2800,
      threshold: 85,
      current: 93,
      category: 'Infrastructure',
      date: '2024-01-14',
      status: 'active'
    },
    {
      id: 3,
      type: 'info',
      title: 'Licensing Optimization Available',
      description: 'Potential savings of $3,200/month identified through license rightsizing',
      impact: 'Low',
      amount: -3200,
      threshold: 100,
      current: 78,
      category: 'Licensing',
      date: '2024-01-13',
      status: 'opportunity'
    },
    {
      id: 4,
      type: 'warning',
      title: 'Storage Growth Rate High',
      description: 'Data storage growing 15% faster than projected, budget impact expected',
      impact: 'Medium',
      amount: 1900,
      threshold: 80,
      current: 88,
      category: 'Storage',
      date: '2024-01-12',
      status: 'active'
    },
    {
      id: 5,
      type: 'resolved',
      title: 'Wave 1 Cost Overrun',
      description: 'Successfully optimized Wave 1 infrastructure, back under budget',
      impact: 'High',
      amount: -2100,
      threshold: 95,
      current: 85,
      category: 'Migration',
      date: '2024-01-10',
      status: 'resolved'
    }
  ];

  const budgetThresholds = [
    { category: 'Migration', budget: 150000, spent: 125000, threshold: 90 },
    { category: 'Infrastructure', budget: 80000, spent: 74000, threshold: 85 },
    { category: 'Licensing', budget: 45000, spent: 35000, threshold: 80 },
    { category: 'Storage', budget: 25000, spent: 22000, threshold: 75 },
    { category: 'Support', budget: 15000, spent: 12000, threshold: 85 }
  ];

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Math.abs(amount));
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Bell className="h-5 w-5 text-blue-500" />;
      case 'resolved':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      default:
        return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAlertColor = (type) => {
    switch (type) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'info':
        return 'border-blue-200 bg-blue-50';
      case 'resolved':
        return 'border-green-200 bg-green-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const activeAlerts = alerts.filter(alert => alert.status === 'active').length;
  const criticalAlerts = alerts.filter(alert => alert.type === 'critical').length;
  const totalSavingsOpportunity = alerts
    .filter(alert => alert.amount < 0)
    .reduce((sum, alert) => sum + Math.abs(alert.amount), 0);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Budget Alerts & Monitoring</h1>
                  <p className="text-gray-600">Monitor budget thresholds and receive proactive cost alerts</p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2">
                    <Settings className="h-4 w-4" />
                    <span>Alert Settings</span>
                  </button>
                  <button className="bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 flex items-center space-x-2">
                    <Download className="h-4 w-4" />
                    <span>Export Report</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Alert Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-red-500 p-3 rounded-lg">
                    <AlertTriangle className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{activeAlerts}</p>
                    <p className="text-gray-600">Active Alerts</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-orange-500 p-3 rounded-lg">
                    <XCircle className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{criticalAlerts}</p>
                    <p className="text-gray-600">Critical Alerts</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-green-500 p-3 rounded-lg">
                    <CheckCircle className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalSavingsOpportunity)}</p>
                    <p className="text-gray-600">Savings Opportunity</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <Bell className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">5</p>
                    <p className="text-gray-600">Categories Monitored</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Budget Thresholds */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Budget Threshold Monitoring</h2>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {budgetThresholds.map((item) => {
                    const percentage = (item.spent / item.budget) * 100;
                    const isOverThreshold = percentage > item.threshold;
                    
                    return (
                      <div key={item.category} className="border rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <h3 className="text-lg font-medium text-gray-900">{item.category}</h3>
                          <span className={`text-sm font-semibold ${isOverThreshold ? 'text-red-600' : 'text-green-600'}`}>
                            {percentage.toFixed(1)}% of budget
                          </span>
                        </div>
                        <div className="flex justify-between text-sm text-gray-600 mb-2">
                          <span>Spent: {formatCurrency(item.spent)}</span>
                          <span>Budget: {formatCurrency(item.budget)}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${isOverThreshold ? 'bg-red-500' : 'bg-green-500'}`}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Threshold: {item.threshold}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Alerts List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Recent Alerts</h2>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <div key={alert.id} className={`border rounded-lg p-4 ${getAlertColor(alert.type)}`}>
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-1">
                          {getAlertIcon(alert.type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-start">
                            <div>
                              <h3 className="text-lg font-medium text-gray-900">{alert.title}</h3>
                              <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                <span>Category: {alert.category}</span>
                                <span>Impact: {alert.impact}</span>
                                <span>Date: {alert.date}</span>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-lg font-semibold ${alert.amount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                {alert.amount > 0 ? '+' : ''}{formatCurrency(alert.amount)}
                              </div>
                              <div className="text-sm text-gray-600">
                                {alert.current}% of threshold
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
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

export default BudgetAlerts;
