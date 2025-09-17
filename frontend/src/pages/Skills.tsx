/**
 * Skills Analytics Page
 * Displays skill demand, categories, and trends
 * US-2.1: Skills by Category Browser
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Target, TrendingUp, TrendingDown, Minus, Link2, Zap } from 'lucide-react';
import { getPopularSkills, getSkillsByCategory, getSkillPairs } from '../services/skillsService';
import { LoadingSpinner, FilterDropdown } from '../components/common';
import { GlassCard } from '../components/common/GlassCard';
import { SkillCategory } from '../types';

// Category Icons Mapping
const categoryIcons: Record<string, string> = {
  programming_languages: '💻',
  web_frameworks: '🌐',
  databases: '🗄️',
  cloud_platforms: '☁️',
  devops: '🔧',
  ai_ml: '🤖',
  mobile: '📱',
  other: '🔨',
};

const Skills: React.FC = () => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<SkillCategory | 'all'>('all');
  const [timeRange, setTimeRange] = useState<number>(90);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);  // For expanding skill lists

  // Fetch popular skills
  const { data: skills, isLoading: skillsLoading } = useQuery({
    queryKey: ['skills', 'popular', timeRange, selectedCategory === 'all' ? undefined : selectedCategory],
    queryFn: () => getPopularSkills(20, timeRange, selectedCategory === 'all' ? undefined : selectedCategory),
  });

  // Fetch skills by category
  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['skills', 'by-category', timeRange],
    queryFn: () => getSkillsByCategory(timeRange),
  });

  // Fetch skill pairs
  const { data: skillPairs } = useQuery({
    queryKey: ['skills', 'pairs'],
    queryFn: () => getSkillPairs(15),
  });

  const isLoading = skillsLoading || categoriesLoading;

  const timeRangeOptions = [
    { value: 30, label: '30 days' },
    { value: 90, label: '90 days' },
    { value: 180, label: '6 months' },
    { value: 365, label: '1 year' },
    { value: 0, label: 'All time' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Skills Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Explore in-demand skills and make informed learning decisions
          </p>
        </div>
        <div className="flex gap-3">
          <FilterDropdown
            label="Time Period"
            value={timeRange}
            options={timeRangeOptions}
            onChange={(val) => setTimeRange(val as number)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" text="Loading skills data..." />
        </div>
      ) : (
        <>
          {/* US-2.1: Skills by Category Grid */}
          {categories && categories.length > 0 && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
                Browse by Category
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {categories.map((cat) => {
                  const categoryKey = cat.category as string;
                  const icon = categoryIcons[categoryKey] || '🔨';
                  const isSelected = selectedCategory === cat.category;
                  
                  return (
                    <GlassCard
                      key={cat.category}
                      hover={true}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedCategory('all');
                        } else {
                          setSelectedCategory(cat.category);
                        }
                      }}
                      className={`cursor-pointer transition-all duration-200 ${
                        isSelected 
                          ? 'ring-2 ring-blue-500 dark:ring-blue-400 shadow-lg' 
                          : 'hover:shadow-md'
                      }`}
                    >
                      <div className="p-5">
                        {/* Category Icon and Name */}
                        <div className="flex items-center gap-3 mb-3">
                          <span className="text-3xl">{icon}</span>
                          <h3 className="font-bold text-base text-gray-900 dark:text-gray-100">
                            {cat.category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </h3>
                        </div>

                        {/* Total Jobs */}
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            <span className="font-semibold text-lg text-gray-900 dark:text-gray-100">
                              {cat.total_jobs}
                            </span> jobs
                          </p>
                          {/* Growth Indicator */}
                          {cat.growth_rate !== undefined && (
                            <div className={`flex items-center gap-1 ${
                              cat.growth_rate > 0 ? 'text-green-600' : 
                              cat.growth_rate < 0 ? 'text-red-600' : 
                              'text-gray-500'
                            }`}>
                              {cat.growth_rate > 5 && <TrendingUp className="w-4 h-4" />}
                              {cat.growth_rate < -5 && <TrendingDown className="w-4 h-4" />}
                              {cat.growth_rate >= -5 && cat.growth_rate <= 5 && <Minus className="w-4 h-4" />}
                              <span className="text-xs font-semibold">
                                {cat.growth_rate > 0 ? '+' : ''}{cat.growth_rate?.toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Top 5 Skills (or all if expanded) */}
                        <div className="space-y-1.5 pt-2 border-t border-gray-200 dark:border-gray-700">
                          {(expandedCategory === cat.category ? cat.skills : cat.skills.slice(0, 5)).map((skill, idx) => (
                            <div 
                              key={skill.id} 
                              className="flex justify-between items-center text-xs hover:bg-gray-100 dark:hover:bg-gray-800 p-1 rounded transition-colors cursor-pointer"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`);
                              }}
                            >
                              <span className="text-gray-700 dark:text-gray-300 truncate mr-2">
                                {idx + 1}. {skill.display_name || skill.name}
                              </span>
                              <span className="text-gray-500 dark:text-gray-400 font-medium whitespace-nowrap">
                                {skill.job_count}
                              </span>
                            </div>
                          ))}
                        </div>

                        {/* Expand/Collapse button */}
                        {cat.skills.length > 5 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setExpandedCategory(expandedCategory === cat.category ? null : cat.category);
                            }}
                            className="w-full text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mt-2 py-1.5 font-medium text-center rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                          >
                            {expandedCategory === cat.category 
                              ? `Show less ▲` 
                              : `+${cat.skills.length - 5} more skills ▼`
                            }
                          </button>
                        )}

                        {/* Selected Indicator */}
                        {isSelected && (
                          <div className="mt-3 pt-2 border-t border-blue-200 dark:border-blue-800">
                            <p className="text-xs text-blue-600 dark:text-blue-400 font-semibold">
                              ✓ Filtering by this category
                            </p>
                          </div>
                        )}
                      </div>
                    </GlassCard>
                  );
                })}
              </div>
            </div>
          )}

          {/* Popular Skills List */}
          {skills && skills.length > 0 && (
            <GlassCard>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Target className="text-blue-600" />
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {selectedCategory === 'all' ? 'Top Skills' : `Top ${selectedCategory.replace(/_/g, ' ')} Skills`}
                  </h2>
                </div>
                <div className="space-y-3">
                  {skills.map((skill, index) => (
                    <div
                      key={skill.id}
                      onClick={() => navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-')}`)}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <span className="text-2xl font-bold text-gray-400 w-8">
                          {index + 1}
                        </span>
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                            {skill.name}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {skill.category?.replace(/_/g, ' ')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900 dark:text-gray-100">
                          {skill.job_count} jobs
                        </p>
                        {skill.growth_rate !== undefined && (
                          <p className={`text-sm ${skill.growth_rate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {skill.growth_rate > 0 ? '+' : ''}{skill.growth_rate.toFixed(1)}%
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          )}

          {/* Skill Combinations Section */}
          {skillPairs && skillPairs.length > 0 && (
            <GlassCard>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Link2 className="text-purple-600" />
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Popular Skill Combinations
                  </h2>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Skills that frequently appear together in job postings. These combinations represent valuable tech stacks in the market.
                </p>

                <div className="space-y-4">
                  {skillPairs.slice(0, 10).map((pair, index) => {
                    const strengthColor =
                      pair.strength === 'high' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' :
                      pair.strength === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' :
                      'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';

                    return (
                      <div
                        key={`${pair.skill1}-${pair.skill2}`}
                        className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <span className="text-sm font-medium text-gray-400 w-6">
                            {index + 1}
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => navigate(`/skills/${pair.skill1.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`)}
                              className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors font-medium capitalize"
                            >
                              {pair.skill1}
                            </button>
                            <Zap className="w-4 h-4 text-gray-400" />
                            <button
                              onClick={() => navigate(`/skills/${pair.skill2.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`)}
                              className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors font-medium capitalize"
                            >
                              {pair.skill2}
                            </button>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${strengthColor}`}>
                            {pair.strength}
                          </span>
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {pair.job_count} jobs
                            </div>
                            <div className="text-xs text-gray-500">
                              {pair.percentage.toFixed(1)}% of pairs
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* View Comparison Link */}
                <div className="mt-6 text-center">
                  <button
                    onClick={() => navigate('/skills/compare')}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                  >
                    Compare Skills Side-by-Side
                  </button>
                </div>
              </div>
            </GlassCard>
          )}

          {/* No Data State */}
          {(!skills || skills.length === 0) && !isLoading && (
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400">
                No skills data available for the selected filters.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Skills;
