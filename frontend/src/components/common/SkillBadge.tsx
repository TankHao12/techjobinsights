/**
 * SkillBadge Component
 * Displays a skill with color-coded category
 */

import React from 'react';
import { SkillCategory } from '../../types';

export interface SkillBadgeProps {
  name: string;
  category?: SkillCategory | string;
  count?: number;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  className?: string;
}

const SkillBadge: React.FC<SkillBadgeProps> = ({
  name,
  category,
  count,
  size = 'md',
  onClick,
  className = '',
}) => {
  // Category color mappings - consistent with all skill categories
  const categoryColors = {
    programming_languages: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800',
    web_frameworks: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-200 dark:border-purple-800',
    databases: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 border-green-200 dark:border-green-800',
    cloud_platforms: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800',
    devops: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300 border-orange-200 dark:border-orange-800',
    ai_ml: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 border-pink-200 dark:border-pink-800',
    mobile: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
    testing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800',
    tools_and_methodologies: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300 border-gray-200 dark:border-gray-800',
    other: 'bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300 border-slate-200 dark:border-slate-800',
  };

  // Size classes
  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  // Get color based on category
  const colorClass = category 
    ? (categoryColors[category as keyof typeof categoryColors] || categoryColors.other)
    : categoryColors.other;

  return (
    <span
      onClick={onClick}
      className={`
        inline-flex items-center rounded-lg font-medium
        border transition-all duration-200
        ${sizeClasses[size]}
        ${colorClass}
        ${onClick ? 'cursor-pointer hover:shadow-sm hover:scale-105' : ''}
        ${className}
      `}
    >
      <span className="truncate">{name}</span>
      {count !== undefined && (
        <span className="ml-1.5 opacity-75">
          ({count})
        </span>
      )}
    </span>
  );
};

export default SkillBadge;


