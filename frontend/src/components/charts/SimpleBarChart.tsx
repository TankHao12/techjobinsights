/**
 * SimpleBarChart Component
 * Wrapper around Recharts for consistent bar chart styling
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import LoadingSpinner from '../common/LoadingSpinner';

export interface BarChartData {
  name: string;
  value: number;
  color?: string;
  category?: string;
}

export interface SimpleBarChartProps {
  data: BarChartData[];
  dataKey?: string;
  nameKey?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  loading?: boolean;
  onBarClick?: (data: BarChartData) => void;
  colorScheme?: 'blue' | 'purple' | 'green' | 'mixed';
}

const SimpleBarChart: React.FC<SimpleBarChartProps> = ({
  data,
  dataKey = 'value',
  nameKey = 'name',
  xAxisLabel,
  yAxisLabel,
  height = 400,
  loading = false,
  onBarClick,
  colorScheme = 'blue',
}) => {
  const colorSchemes = {
    blue: '#3B82F6',
    purple: '#A855F7',
    green: '#10B981',
    mixed: undefined, // Will use individual colors from data
  };

  const defaultColor = colorSchemes[colorScheme];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {data[nameKey]}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Count: <span className="font-medium">{data[dataKey].toLocaleString()}</span>
          </p>
          {data.category && (
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              {data.category}
            </p>
          )}
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
      <BarChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#E5E7EB"
          className="dark:stroke-gray-700"
        />
        <XAxis
          dataKey={nameKey}
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={80}
          stroke="#9CA3AF"
          label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom', offset: -10 } : undefined}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          stroke="#9CA3AF"
          label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
        <Bar
          dataKey={dataKey}
          fill={defaultColor}
          radius={[8, 8, 0, 0]}
          onClick={onBarClick ? (data: any) => onBarClick(data) : undefined}
          cursor={onBarClick ? 'pointer' : 'default'}
        >
          {colorScheme === 'mixed' &&
            data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || defaultColor} />
            ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default SimpleBarChart;


