/**
 * Regional Insights Page
 * Explore tech job opportunities across New Zealand regions
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { MapPin, Search, Briefcase, Building2, DollarSign, Clock } from 'lucide-react';
import { getRegions } from '../services/regionsService';
import { LoadingSpinner } from '../components/common';
import { GlassCard } from '../components/common/GlassCard';
import { SkillMultiSelect } from '../components/common/SkillMultiSelect';

const Regions: React.FC = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [timePeriod, setTimePeriod] = useState<number | undefined>(undefined);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const limit = 20;

  // Use skills array directly (or undefined if empty)
  const skills = selectedSkills.length > 0 ? selectedSkills : undefined;

  const { data, isLoading } = useQuery({
    queryKey: ['regions', search, page, timePeriod, skills],
    queryFn: () => getRegions({ search, page, limit, time_period: timePeriod, skills }),
  });

  const formatSalary = (salary?: number | null) => {
    if (!salary) return 'N/A';
    return `$${Math.round(salary).toLocaleString()}`;
  };

  const getTimePeriodLabel = (days?: number) => {
    if (!days) return 'All Time';
    if (days === 30) return 'Last 30 Days';
    if (days === 60) return 'Last 60 Days';
    if (days === 90) return 'Last 90 Days';
    return `Last ${days} Days`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Regional Insights
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Explore tech job opportunities across New Zealand regions
        </p>
      </div>

      {/* Filters */}
      <div className="space-y-4">
        <GlassCard hover={false} className="p-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search regions..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100"
              />
            </div>

            {/* Time Period Filter */}
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={timePeriod || ""}
                onChange={(e) => {
                  setTimePeriod(
                    e.target.value ? parseInt(e.target.value) : undefined
                  );
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100 appearance-none cursor-pointer"
              >
                <option value="">All Time</option>
                <option value="30">Last 30 Days</option>
                <option value="60">Last 60 Days</option>
                <option value="90">Last 90 Days</option>
              </select>
            </div>
          </div>
        </GlassCard>

        {/* Skills Filter with Autocomplete - Outside GlassCard for proper z-index */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-lg border border-gray-200/50 dark:border-gray-700/50 p-4 shadow-sm">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Filter by Skills
          </label>
          <SkillMultiSelect
            selectedSkills={selectedSkills}
            onChange={(newSkills) => {
              setSelectedSkills(newSkills);
              setPage(1);
            }}
            placeholder="Type to search and select skills..."
            showAddButton={false}
          />
        </div>

        {/* Active Filters Display */}
        {timePeriod && (
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
              <Clock className="w-3 h-3 mr-1" />
              {getTimePeriodLabel(timePeriod)}
            </span>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center items-center py-12 z-[9999]">
          <LoadingSpinner />
        </div>
      )}

      {/* Regions Table */}
      {!isLoading && data && (
        <>
          <GlassCard hover={false} className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Region
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Active Jobs
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Total Jobs
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Avg Salary
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Top Companies
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {data.items.map((region) => (
                    <tr
                      key={region.id}
                      onClick={() => navigate(`/regions/${region.id}`)}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <MapPin className="w-5 h-5 text-blue-500 mr-2 flex-shrink-0" />
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {region.city}
                            </div>
                            {region.region && (
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {region.region}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center text-sm text-gray-900 dark:text-gray-100">
                          <Briefcase className="w-4 h-4 text-green-500 mr-2" />
                          {region.active_jobs_count}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {region.total_jobs_count}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center text-sm text-gray-900 dark:text-gray-100">
                          <DollarSign className="w-4 h-4 text-blue-500 mr-1" />
                          {formatSalary(region.avg_salary)}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {region.top_companies &&
                          region.top_companies.length > 0 ? (
                            region.top_companies
                              .slice(0, 3)
                              .map((company, idx) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                                >
                                  <Building2 className="w-3 h-3 mr-1" />
                                  {company.name} ({company.job_count})
                                </span>
                              ))
                          ) : (
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              N/A
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Empty State */}
            {data.items.length === 0 && (
              <div className="text-center py-12">
                <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  No regions found
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  {selectedSkills.length > 0
                    ? `No regions have jobs matching the selected skill${
                        selectedSkills.length > 1 ? "s" : ""
                      }: ${selectedSkills.join(", ")}`
                    : "Try adjusting your filters or search query"}
                </p>
                {selectedSkills.length > 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    Try removing some skills or changing the time period filter
                  </p>
                )}
              </div>
            )}
          </GlassCard>

          {/* Pagination */}
          {data.total > 0 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Showing {(page - 1) * limit + 1} to{" "}
                {Math.min(page * limit, data.total)} of {data.total} regions
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={!data.has_prev}
                  className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-gray-100 transition-colors"
                >
                  Previous
                </button>
                <span className="px-4 py-2 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg text-blue-600 dark:text-blue-200 font-medium">
                  Page {page} of {data.pages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={!data.has_next}
                  className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-gray-100 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Regions;

