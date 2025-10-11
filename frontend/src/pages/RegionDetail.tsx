/**
 * Region Detail Page
 * Displays regional job market insights
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  MapPin,
  Briefcase,
  Building2,
  DollarSign,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { GlassCard, LoadingSpinner } from '../components/common';
import { SkillMultiSelect } from '../components/common/SkillMultiSelect';
import { getRegionDetails, getRegionCompanies, getRegionJobs } from '../services/regionsService';

const RegionDetail: React.FC = () => {
  const { regionId } = useParams<{ regionId: string }>();
  const navigate = useNavigate();
  const [timePeriod, setTimePeriod] = useState<number | undefined>(undefined);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [jobsPage, setJobsPage] = useState(1);
  const jobsLimit = 10;

  // Use skills array directly (or undefined if empty)
  const skills = selectedSkills.length > 0 ? selectedSkills : undefined;

  // Fetch region details
  const { data: regionData, isLoading: regionLoading } = useQuery({
    queryKey: ['regionDetails', regionId, timePeriod, skills],
    queryFn: () => getRegionDetails(Number(regionId), timePeriod, skills),
    enabled: !!regionId,
  });

  // Fetch top companies
  const { data: companiesData } = useQuery({
    queryKey: ['regionCompanies', regionId, timePeriod, skills],
    queryFn: () => getRegionCompanies(Number(regionId), 10, timePeriod, skills),
    enabled: !!regionId,
  });

  // Fetch jobs
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['regionJobs', regionId, jobsPage, timePeriod, skills],
    queryFn: () => getRegionJobs(Number(regionId), jobsPage, jobsLimit, timePeriod, skills),
    enabled: !!regionId,
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

  if (regionLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (!regionData) {
    return (
      <div className="text-center py-12">
        <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
          Region not found
        </h3>
        <button
          onClick={() => navigate('/regions')}
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          Back to Regions
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <button
            onClick={() => navigate('/regions')}
            className="mt-1 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <MapPin className="w-8 h-8 text-blue-500" />
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {regionData.city}
              </h1>
            </div>
            {regionData.region && (
              <p className="text-lg text-gray-600 dark:text-gray-400">
                {regionData.region}, {regionData.country}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-4">
        <GlassCard hover={false} className="p-0">
          <div className="relative">
            <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <select
              value={timePeriod || ''}
              onChange={(e) => {
                setTimePeriod(e.target.value ? parseInt(e.target.value) : undefined);
                setJobsPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100 appearance-none cursor-pointer"
            >
              <option value="">All Time</option>
              <option value="30">Last 30 Days</option>
              <option value="60">Last 60 Days</option>
              <option value="90">Last 90 Days</option>
            </select>
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
              setJobsPage(1);
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

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard className="p-6">
          <div className="flex items-center justify-between mb-2">
            <Briefcase className="w-8 h-8 text-green-500" />
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {regionData.active_jobs_count}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Active Jobs</div>
          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            {regionData.total_jobs_count} total jobs
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {formatSalary(regionData.avg_salary)}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Average Salary</div>
          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            Based on active jobs
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <div className="flex items-center justify-between mb-2">
            <Building2 className="w-8 h-8 text-purple-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {companiesData?.companies.length || 0}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Companies Hiring</div>
          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            Top companies in this region
          </div>
        </GlassCard>
      </div>

      {/* Top Companies */}
      {companiesData && companiesData.companies.length > 0 && (
        <GlassCard className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-purple-500" />
            Top Hiring Companies
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Company
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Active Jobs
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {companiesData.companies.map((company) => (
                  <tr
                    key={company.id}
                    onClick={() => navigate(`/companies/${company.id}`)}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {company.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Briefcase className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-gray-900 dark:text-gray-100">
                          {company.job_count}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      {/* Recent Jobs */}
      <GlassCard className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
          <Briefcase className="w-6 h-6 text-green-500" />
          Recent Jobs
        </h2>

        {jobsLoading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        )}

        {!jobsLoading && jobsData && (
          <>
            <div className="space-y-4">
              {jobsData.items.map((job: any) => (
                <div
                  key={job.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                      {job.title}
                    </h3>
                    {job.is_active && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                        Active
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
                    {job.employment_type && (
                      <span>{job.employment_type}</span>
                    )}
                    {job.salary_min && job.salary_max && (
                      <span>
                        ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                      </span>
                    )}
                    {job.posted_date && (
                      <span>
                        Posted: {new Date(job.posted_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {job.extracted_skills && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {Object.entries(job.extracted_skills).flatMap(([category, skills]: [string, any]) =>
                        skills.slice(0, 5).map((skill: string, idx: number) => (
                          <span
                            key={`${category}-${idx}`}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                          >
                            {skill}
                          </span>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Jobs Pagination */}
            {jobsData.total > 0 && (
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Showing {((jobsPage - 1) * jobsLimit) + 1} to {Math.min(jobsPage * jobsLimit, jobsData.total)} of {jobsData.total} jobs
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setJobsPage(jobsPage - 1)}
                    disabled={!jobsData.has_prev}
                    className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-gray-100 transition-colors"
                  >
                    Previous
                  </button>
                  <span className="px-4 py-2 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg text-blue-600 dark:text-blue-200 font-medium">
                    Page {jobsPage} of {jobsData.pages}
                  </span>
                  <button
                    onClick={() => setJobsPage(jobsPage + 1)}
                    disabled={!jobsData.has_next}
                    className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-gray-100 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {jobsData.items.length === 0 && (
              <div className="text-center py-8">
                <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  No jobs found
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  {selectedSkills.length > 0 
                    ? `No jobs match the selected skill${selectedSkills.length > 1 ? 's' : ''}: ${selectedSkills.join(', ')}`
                    : 'Try adjusting your filters'}
                </p>
                {selectedSkills.length > 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    Try removing some skills or changing the time period filter
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </GlassCard>
    </div>
  );
};

export default RegionDetail;

