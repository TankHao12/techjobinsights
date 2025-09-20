/**
 * Companies Page
 * Browse companies and their hiring activity
 * US-3.1: Company Directory
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Building2, Search, Code2, TrendingUp } from 'lucide-react';
import { getCompanies, getCompaniesByTech, getPopularCompaniesAutocomplete } from '../services/companiesService';
import { LoadingSpinner } from '../components/common';
import { GlassCard } from '../components/common/GlassCard';

const Companies: React.FC = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [techSearch, setTechSearch] = useState('');
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<'all' | 'bytech'>('all');
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ['companies', search, page],
    queryFn: () => getCompanies({ search, page, limit }),
    enabled: activeTab === 'all',
  });

  const { data: techCompanies, isLoading: techLoading } = useQuery({
    queryKey: ['companiesByTech', techSearch],
    queryFn: () => getCompaniesByTech(techSearch),
    enabled: activeTab === 'bytech' && techSearch.length > 0,
  });

  const { data: topCompanies } = useQuery({
    queryKey: ['topCompanies'],
    queryFn: () => getPopularCompaniesAutocomplete(10),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Companies
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Explore companies hiring in the NZ tech market
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => {
            setActiveTab('all');
            setPage(1);
          }}
          className={`pb-2 px-1 font-medium transition-colors ${
            activeTab === 'all'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            <span>All Companies</span>
          </div>
        </button>
        <button
          onClick={() => {
            setActiveTab('bytech');
            setTechSearch('');
          }}
          className={`pb-2 px-1 font-medium transition-colors ${
            activeTab === 'bytech'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4" />
            <span>Find by Technology</span>
          </div>
        </button>
      </div>

      {/* Search Bar */}
      {activeTab === 'all' ? (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search companies by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100"
          />
        </div>
      ) : (
        <div className="relative">
          <Code2 className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Enter technology name (e.g., React, Python, AWS)..."
            value={techSearch}
            onChange={(e) => setTechSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100"
          />
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Find companies that are using a specific technology in their job postings
          </p>
        </div>
      )}

      {activeTab === 'all' ? (
        isLoading ? (
          <div className="flex items-center justify-center min-h-[40vh]">
            <LoadingSpinner size="lg" text="Loading companies..." />
          </div>
        ) : (
          <>
            {/* Companies Grid */}
            {data && data.items.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.items.map((company) => (
                  <GlassCard
                    key={company.id}
                    hover={true}
                    onClick={() => navigate(`/companies/${company.id}`)}
                    className="cursor-pointer"
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <Building2 className="w-8 h-8 text-blue-600" />
                      </div>
                      <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 mb-2">
                        {company.name}
                      </h3>
                      <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                        <p>{company.active_jobs_count || 0} active jobs</p>
                        <p>{company.total_jobs_count || 0} total jobs posted</p>
                      </div>
                    </div>
                  </GlassCard>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600 dark:text-gray-400">
                  {search ? 'No companies found matching your search.' : 'No companies available.'}
                </p>
              </div>
            )}

            {/* Pagination */}
            {data && data.pages > 1 && (
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="px-4 py-2 text-gray-700 dark:text-gray-300">
                  Page {page} of {data.pages}
                </span>
                <button
                  onClick={() => setPage(Math.min(data.pages, page + 1))}
                  disabled={page === data.pages}
                  className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )
      ) : (
        <>
          {/* Tech Search Results */}
          {techSearch.length === 0 ? (
            <GlassCard>
              <div className="p-8 text-center">
                <Code2 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Search for a Technology
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Enter a technology name to find companies using it
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {['React', 'Python', 'AWS', 'Docker', 'Kubernetes', 'TypeScript', 'PostgreSQL'].map(
                    (tech) => (
                      <button
                        key={tech}
                        onClick={() => setTechSearch(tech)}
                        className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                      >
                        {tech}
                      </button>
                    )
                  )}
                </div>
              </div>
            </GlassCard>
          ) : techLoading ? (
            <div className="flex items-center justify-center min-h-[40vh]">
              <LoadingSpinner size="lg" text={`Finding companies using ${techSearch}...`} />
            </div>
          ) : techCompanies && techCompanies.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {techCompanies.length} companies using {techSearch}
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {techCompanies.map((company) => (
                  <GlassCard
                    key={company.id}
                    hover={true}
                    onClick={() => navigate(`/companies/${company.id}`)}
                    className="cursor-pointer"
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <Building2 className="w-8 h-8 text-blue-600" />
                        <div className="flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs">
                          <TrendingUp className="w-3 h-3" />
                          {company.job_count} {company.job_count === 1 ? 'job' : 'jobs'}
                        </div>
                      </div>
                      <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 mb-2">
                        {company.name}
                      </h3>
                    </div>
                  </GlassCard>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400">
                No companies found using <strong>{techSearch}</strong>. Try a different technology.
              </p>
            </div>
          )}
        </>
      )}

      {/* Top Hiring Companies Sidebar (shown on all tab only) */}
      {activeTab === 'all' && topCompanies && topCompanies.length > 0 && (
        <GlassCard>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Top Hiring Companies
            </h3>
            <div className="space-y-2">
              {topCompanies.slice(0, 5).map((company, index) => (
                <div
                  key={company.id}
                  onClick={() => navigate(`/companies/${company.id}`)}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-gray-400 w-6">#{index + 1}</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{company.name}</span>
                  </div>
                  <span className="text-sm text-gray-500">{company.job_count || 0} jobs</span>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default Companies;
