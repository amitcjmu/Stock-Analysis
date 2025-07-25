import React from 'react';
import { Legend } from 'recharts'
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { ArrowRight, Download } from 'lucide-react';

interface AssetMetrics {
  total_count: number;
  by_type: Record<string, number>;
  by_environment: Record<string, number>;
  by_criticality: Record<string, number>;
  by_status: Record<string, number>;
}

interface AssetDistributionProps {
  metrics: AssetMetrics;
  className?: string;
}

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#d946ef'
];

const RADIAN = Math.PI / 180;

const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
  name,
  value,
}: unknown) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN) * 1.2;
  const y = cy + radius * Math.sin(-midAngle * RADIAN) * 1.2;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="text-xs font-medium"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

const CustomTooltip = ({ active, payload, label }: unknown) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
        <p className="font-medium">{payload[0].name}</p>
        <p className="text-sm">
          {payload[0].value} ({((payload[0].value / payload[0].payload.total) * 100).toFixed(1)}%)
        </p>
      </div>
    );
  }
  return null;
};

const prepareChartData = (data: Record<string, number>, total: number) => {
  return Object.entries(data).map(([name, value]) => ({
    name,
    value,
    percentage: (value / total) * 100,
    total,
  }));
};

const AssetDistribution: React.FC<AssetDistributionProps> = ({
  metrics,
  className = '',
}) => {
  const totalAssets = metrics.total_count;

  const typeData = React.useMemo(
    () => prepareChartData(metrics.by_type, totalAssets),
    [metrics.by_type, totalAssets]
  );

  const envData = React.useMemo(
    () => prepareChartData(metrics.by_environment, totalAssets),
    [metrics.by_environment, totalAssets]
  );

  const criticalityData = React.useMemo(
    () => prepareChartData(metrics.by_criticality, totalAssets),
    [metrics.by_criticality, totalAssets]
  );

  const statusData = React.useMemo(
    () => prepareChartData(metrics.by_status, totalAssets),
    [metrics.by_status, totalAssets]
  );

  const renderPieChart = (data: unknown[], title: string) => (
    <div className="flex flex-col items-center">
      <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={70}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 w-full px-4">
        <div className="grid grid-cols-2 gap-2">
          {data.map((item, index) => (
            <div key={item.name} className="flex items-center text-xs">
              <div
                className="w-2 h-2 rounded-full mr-1.5 flex-shrink-0"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <span className="truncate">{item.name}</span>
              <span className="ml-auto font-medium">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderBarChart = (data: unknown[], title: string) => (
    <div className="h-64 w-full">
      <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart
          data={data}
          margin={{
            top: 5,
            right: 5,
            left: -20,
            bottom: 5,
          }}
          layout="vertical"
        >
          <XAxis type="number" />
          <YAxis
            type="category"
            dataKey="name"
            width={80}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-2 border border-gray-200 rounded shadow">
                    <p className="font-medium">{payload[0].payload.name}</p>
                    <p className="text-sm">
                      {payload[0].value} ({(payload[0].payload.percentage).toFixed(1)}%)
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Asset Distribution</CardTitle>
          <Button variant="outline" size="sm" className="h-8">
            <Download className="h-4 w-4 mr-1.5" />
            Export
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="type" className="w-full">
          <TabsList className="grid w-full grid-cols-4 h-10">
            <TabsTrigger value="type" className="text-xs">By Type</TabsTrigger>
            <TabsTrigger value="environment" className="text-xs">By Environment</TabsTrigger>
            <TabsTrigger value="criticality" className="text-xs">By Criticality</TabsTrigger>
            <TabsTrigger value="status" className="text-xs">By Status</TabsTrigger>
          </TabsList>

          <TabsContent value="type" className="mt-4">
            {renderPieChart(typeData, 'Assets by Type')}
          </TabsContent>

          <TabsContent value="environment" className="mt-4">
            {renderBarChart(envData, 'Assets by Environment')}
          </TabsContent>

          <TabsContent value="criticality" className="mt-4">
            {renderPieChart(criticalityData, 'Assets by Criticality')}
          </TabsContent>

          <TabsContent value="status" className="mt-4">
            {renderBarChart(statusData, 'Assets by Status')}
          </TabsContent>
        </Tabs>

        <div className="mt-4 pt-4 border-t border-gray-100 text-right">
          <Button variant="ghost" size="sm" className="text-blue-600">
            View detailed asset inventory
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default AssetDistribution;
