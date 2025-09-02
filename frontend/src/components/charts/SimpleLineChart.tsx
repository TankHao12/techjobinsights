/**
 * SimpleLineChart Component
 * Wrapper around Recharts for consistent line chart styling
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import LoadingSpinner from '../common/LoadingSpinner';

export interface LineChartData {
  date: string;
  [key: string]: number | string;
}

export interface LineConfig {
  dataKey: string;
  name: string;
  color: string;
}

export interface SimpleLineChartProps {
  data: LineChartData[];
  lines: LineConfig[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  loading?: boolean;
  showLegend?: boolean;
  showGrid?: boolean;
}

const SimpleLineChart: React.FC<SimpleLineChartProps> = ({
  data,
  lines,
  xAxisLabel,
  yAxisLabel,
  height = 400,
  loading = false,
  showLegend = true,
  showGrid = true,
}) => {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-gray-600 dark:text-gray-400">
                {entry.name}:
              </span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {entry.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <LoadingSpinner size="lg" text="Loading chart..." />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <p className="text-gray-500 dark:text-gray-400">No data available</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#E5E7EB"
            className="dark:stroke-gray-700"
          />
        )}
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          stroke="#9CA3AF"
          label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom', offset: -10 } : undefined}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          stroke="#9CA3AF"
          label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined}
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend />}
        {lines.map((line, index) => (
          <Line
            key={index}
            type="monotone"
            dataKey={line.dataKey}
            name={line.name}
            stroke={line.color}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default SimpleLineChart;


