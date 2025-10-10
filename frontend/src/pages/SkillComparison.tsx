/**
 * Skill Comparison Page
 * Compare multiple skills side-by-side
 * US-2.3: Multi-Skill Comparison Tool
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  X,
  Search,
  TrendingUp,
  TrendingDown,
  Building2,
  BarChart3,
  Users,
  Percent,
} from 'lucide-react';
import { GlassCard } from '../components/common/GlassCard';
import { LoadingSpinner } from '../components/common';
import { SimpleLineChart, SimpleBarChart } from '../components/charts';
import { compareSkills, searchSkills } from '../services/skillsService';
import type { SkillComparison, SkillWithStats } from '../types';

const SkillComparison: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SkillWithStats[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Initialize from URL params
  useEffect(() => {
    const skills = searchParams.get('skills');
    if (skills) {
      setSelectedSkills(skills.split(',').slice(0, 3));
    }
  }, [searchParams]);

  // Fetch comparison data
  const { data: comparisonData, isLoading, error } = useQuery({
    queryKey: ['skillComparison', selectedSkills],
    queryFn: () => compareSkills(selectedSkills),
    enabled: selectedSkills.length > 0,
  });

  // Search skills
  const handleSearch = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchSkills(query, undefined, 10);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const addSkill = (skillName: string) => {
    if (selectedSkills.length >= 3 || selectedSkills.includes(skillName)) return;

    const newSkills = [...selectedSkills, skillName];
    setSelectedSkills(newSkills);
    setSearchParams({ skills: newSkills.join(',') });
    setSearchQuery('');
    setSearchResults([]);
  };

  const removeSkill = (skillName: string) => {
    const newSkills = selectedSkills.filter(skill => skill !== skillName);
    setSelectedSkills(newSkills);
    if (newSkills.length > 0) {
      setSearchParams({ skills: newSkills.join(',') });
    } else {
      setSearchParams({});
    }
  };

  const getGrowthColor = (rate: number) => {
    if (rate > 5) return 'text-green-600 dark:text-green-400';
    if (rate < -5) return 'text-red-600 dark:text-red-400';
    return 'text-gray-500';
  };

  const getGrowthIcon = (rate: number) => {
    if (rate > 5) return TrendingUp;
    if (rate < -5) return TrendingDown;
    return BarChart3;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Compare Skills
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Compare up to 3 skills side-by-side to make informed learning decisions
        </p>
      </div>

      {/* Skill Selection */}
        <div className="p-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Select Skills to Compare ({selectedSkills.length}/3)
          </h2>

          {/* Selected Skills */}
          {selectedSkills.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedSkills.map((skill) => (
                <div
                  key={skill}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg"
                >
                  <span className="capitalize">{skill}</span>
                  <button
                    onClick={() => removeSkill(skill)}
                    className="hover:text-red-600 dark:hover:text-red-400"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Search Input */}
          {selectedSkills.length < 3 && (
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    handleSearch(e.target.value);
                  }}
                  placeholder="Search for skills to add..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Search Results */}
              {(searchResults.length > 0 || isSearching) && (
                <div className="absolute z-[9999] mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-2xl max-h-60 overflow-y-auto">
                  {isSearching ? (
                    <div className="p-4 text-center">
                      <LoadingSpinner size="sm" />
                    </div>
                  ) : (
                    searchResults.map((skill) => (
                      <button
                        key={skill.name}
                        onClick={() => addSkill(skill.name)}
                        disabled={selectedSkills.includes(skill.name)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex justify-between items-center">
                          <span className="capitalize text-gray-900 dark:text-gray-100">
                            {skill.name}
                          </span>
                          <span className="text-sm text-gray-500">
                            {skill.job_count} jobs
                          </span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>

      {/* Comparison Results */}
      {selectedSkills.length > 0 && (
        <>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" text="Loading comparison data..." />
            </div>
          ) : error ? (
              <div className="p-0 text-center">
                <p className="text-red-600 dark:text-red-400">
                  Failed to load comparison data. Please try again.
                </p>
              </div>
          ) : selectedSkills.length === 1 ? (
              <div className="p-0 text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-4 text-blue-500" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Add More Skills to Compare
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  You've selected <span className="font-semibold text-blue-600 dark:text-blue-400 capitalize">{selectedSkills[0]}</span>. 
                  Please add at least one more skill to see a side-by-side comparison of market demand, growth trends, and opportunities.
                </p>
              </div>
          ) : comparisonData && comparisonData.length > 0 ? (
            <>
              {/* Key Metrics Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Metrics Card - Only visible on desktop */}
                <div className="hidden lg:block lg:col-span-1">
                  <GlassCard hover={false}>
                    <div className="p-0">
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                        Metrics
                      </h3>
                      <div className="space-y-3">
                        <div className="flex items-center gap-3 text-lg font-medium text-gray-700 dark:text-gray-300">
                          <BarChart3 className="w-5 h-5" />
                          <span>Job Demand</span>
                        </div>
                        <div className="flex items-center gap-3 text-lg font-medium text-gray-700 dark:text-gray-300">
                          <TrendingUp className="w-5 h-5" />
                          <span>Growth Rate</span>
                        </div>
                        <div className="flex items-center gap-3 text-lg font-medium text-gray-700 dark:text-gray-300">
                          <Building2 className="w-5 h-5" />
                          <span>Companies</span>
                        </div>
                        <div className="flex items-center gap-3 text-lg font-medium text-gray-700 dark:text-gray-300">
                          <Percent className="w-5 h-5" />
                          <span>Market Share</span>
                        </div>
                      </div>
                    </div>
                  </GlassCard>
                </div>

                {comparisonData.map((skill) => {
                  const GrowthIcon = getGrowthIcon(skill.growth_rate);
                  return (
                    <GlassCard key={skill.skill} hover={false}>
                      <div className="p-0">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 capitalize">
                          {skill.skill}
                        </h3>
                        <div className="space-y-3">
                          {/* Job Demand */}
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                {skill.demand}
                              </span>
                              <span className="text-sm text-gray-500 lg:hidden">jobs</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500 lg:hidden">Job Demand</span>
                              <BarChart3 className="w-5 h-5 text-gray-400" />
                            </div>
                          </div>
                          
                          {/* Growth Rate */}
                          <div className="flex justify-between items-center">
                            <span className={`text-xl font-semibold ${getGrowthColor(skill.growth_rate)}`}>
                              {skill.growth_rate > 0 ? '+' : ''}{skill.growth_rate.toFixed(1)}%
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500 lg:hidden">Growth Rate</span>
                              <GrowthIcon className={`w-5 h-5 ${getGrowthColor(skill.growth_rate)}`} />
                            </div>
                          </div>
                          
                          {/* Companies */}
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                                {skill.companies_using}
                              </span>
                              <span className="text-sm text-gray-500 lg:hidden">companies</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500 lg:hidden">Companies</span>
                              <Building2 className="w-5 h-5 text-gray-400" />
                            </div>
                          </div>
                          
                          {/* Market Share */}
                          <div className="flex justify-between items-center">
                            <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                              {skill.percentage.toFixed(1)}%
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500 lg:hidden">Market Share</span>
                              <Percent className="w-5 h-5 text-gray-400" />
                            </div>
                          </div>
                        </div>
                      </div>
                    </GlassCard>
                  );
                })}
              </div>

              {/* Trend Chart */}
              <GlassCard>
                <div className="p-0">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    Demand Trend Comparison
                  </h2>
                  <div className="h-80">
                    <SimpleLineChart
                      data={comparisonData[0].trend_data.map(item => ({
                        date: new Date(item.date).toLocaleDateString('en-NZ', {
                          month: 'short',
                          day: 'numeric'
                        }),
                        ...comparisonData.reduce((acc, skill) => {
                          const dataPoint = skill.trend_data.find(d => d.date === item.date);
                          acc[skill.skill] = dataPoint ? dataPoint.count : 0;
                          return acc;
                        }, {} as Record<string, number>)
                      }))}
                      lines={comparisonData.map((skill, index) => ({
                        dataKey: skill.skill,
                        name: skill.skill.charAt(0).toUpperCase() + skill.skill.slice(1),
                        color: ['#3B82F6', '#10B981', '#F59E0B'][index] || '#EF4444'
                      }))}
                      height={320}
                      showLegend={true}
                      showGrid={true}
                    />
                  </div>
                </div>
              </GlassCard>

              {/* Bar Chart Comparison */}
              <GlassCard>
                <div className="p-0">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    Current Market Position
                  </h2>
                  <div className="h-64">
                    <SimpleBarChart
                      data={comparisonData.map(skill => ({
                        name: skill.skill.charAt(0).toUpperCase() + skill.skill.slice(1),
                        value: skill.demand,
                        category: `${skill.percentage.toFixed(1)}% market share`
                      }))}
                      height={240}
                      colorScheme="blue"
                    />
                  </div>
                </div>
              </GlassCard>

              {/* Summary Table */}
              <GlassCard>
                <div className="p-0">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    Detailed Comparison
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                            Skill
                          </th>
                          <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                            Job Demand
                          </th>
                          <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                            Growth Rate
                          </th>
                          <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                            Companies
                          </th>
                          <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                            Market Share
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparisonData.map((skill, index) => (
                          <tr
                            key={skill.skill}
                            className={`border-b border-gray-100 dark:border-gray-800 ${
                              index % 2 === 0 ? 'bg-gray-50/50 dark:bg-gray-800/50' : ''
                            }`}
                          >
                            <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100 capitalize">
                              {skill.skill}
                            </td>
                            <td className="py-3 px-4 text-right text-gray-900 dark:text-gray-100">
                              {skill.demand}
                            </td>
                            <td className={`py-3 px-4 text-right font-medium ${getGrowthColor(skill.growth_rate)}`}>
                              {skill.growth_rate > 0 ? '+' : ''}{skill.growth_rate.toFixed(1)}%
                            </td>
                            <td className="py-3 px-4 text-right text-gray-900 dark:text-gray-100">
                              {skill.companies_using}
                            </td>
                            <td className="py-3 px-4 text-right text-gray-900 dark:text-gray-100">
                              {skill.percentage.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </GlassCard>
            </>
          ) : null}
        </>
      )}

      {/* Empty State */}
      {selectedSkills.length === 0 && (
        <GlassCard>
          <div className="p-0 text-center">
            <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              No Skills Selected
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Search and select up to 3 skills to compare their market demand, growth trends, and opportunities.
            </p>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default SkillComparison;


