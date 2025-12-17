import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface PriceData {
  date: string;
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface PriceChartProps {
  data: PriceData[];
  symbol: string;
  period: string;
}

export const PriceChart: React.FC<PriceChartProps> = ({ data, symbol, period }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No price data available
      </div>
    );
  }

  // Format data for chart
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    close: item.close,
    open: item.open,
    high: item.high,
    low: item.low,
    volume: item.volume,
  }));

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            angle={-45}
            textAnchor="end"
            height={80}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(value) => `$${value.toFixed(2)}`}
          />
          <Tooltip
            formatter={(value: number) => `$${value.toFixed(2)}`}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#2563eb"
            strokeWidth={2}
            name="Close Price"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="open"
            stroke="#10b981"
            strokeWidth={1}
            name="Open Price"
            dot={false}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
