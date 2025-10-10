/**
 * SkillGridView Component
 * Displays skills in a modern grid layout with job counts and category badges
 */

import React from 'react';
import { TrendingUp } from 'lucide-react';

interface SkillData {
  name: string;
  value: number;
  color?: string;
  category?: string;
  percentage?: number;
}

interface SkillGridViewProps {
  data: SkillData[];
  onSkillClick?: (skill: SkillData) => void;
  loading?: boolean;
}

const SkillGridView: React.FC<SkillGridViewProps> = ({
  data,
  onSkillClick,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {[...Array(20)].map((_, index) => (
          <div
            key={index}
            className="bg-gray-100 dark:bg-gray-800 rounded-xl p-4 animate-pulse"
          >
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">
          No skills data available for the selected filters.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {data.map((skill, index) => (
        <div
          key={`${skill.name}-${index}`}
          onClick={() => onSkillClick?.(skill)}
          className="group relative bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 cursor-pointer hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-lg transition-all duration-200 hover:scale-105"
        >
          {/* Rank Badge */}
          <div className="absolute -top-2 -left-2 w-6 h-6 bg-blue-600 dark:bg-blue-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-md">
            {index + 1}
          </div>

          {/* Percentage Badge - Top Right */}
          {skill.percentage !== undefined && (
            <div className="absolute top-2 right-2 text-right">
              <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {skill.percentage.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                of jobs
              </div>
            </div>
          )}

          {/* Skill Name */}
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 capitalize break-words min-h-[2.5rem] pr-16">
            {skill.name}
          </h3>

          {/* Job Count */}
          <div className="flex items-baseline gap-1 mb-2">
            <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {skill.value.toLocaleString()}
            </span>
            <TrendingUp className="w-4 h-4 text-green-500" />
          </div>

          {/* Category Badge */}
          {skill.category && (
            <span
              className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium capitalize truncate"
              style={{
                backgroundColor: skill.color ? `${skill.color}15` : undefined,
                color: skill.color || undefined,
              }}
            >
              {skill.category}
            </span>
          )}

          {/* Hover Indicator */}
          <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="text-xs text-blue-600 dark:text-blue-400 font-medium">
              View Details →
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SkillGridView;

