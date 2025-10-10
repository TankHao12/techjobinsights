/**
 * Dashboard Page
 * Main landing page showing market overview statistics
 * US-1.1: Market Overview Statistics
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Building2, DollarSign } from 'lucide-react';
import { getDashboardStats } from '../services/dashboardService';
import { getPopularSkills } from '../services/skillsService';
import StatCard from '../components/common/StatCard';
import { LoadingSpinner, FilterDropdown } from '../components/common';
import { SkillGridView } from '../components/charts';
import { SkillCategory } from '../types';

// Helper function to get color by category
const getCategoryColor = (category?: SkillCategory | string): string => {
    const colors: Record<string, string> = {
        programming_languages: '#3B82F6', // blue
        web_frameworks: '#A855F7', // purple
        databases: '#10B981', // green
        cloud_platforms: '#06B6D4', // cyan
        devops: '#F59E0B', // amber
        ai_ml: '#EC4899', // pink
        mobile: '#6366F1', // indigo
        other: '#6B7280', // gray
    };
    return colors[category as string] || colors.other;
};

const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const [timeRange, setTimeRange] = useState<number>(90);
    const [selectedCategory, setSelectedCategory] = useState<SkillCategory | 'all'>('all');

    // Fetch dashboard stats
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['dashboard', timeRange],
        queryFn: () => getDashboardStats(timeRange),
    });

    // Fetch popular skills for bar chart (US-1.2)
    const { data: popularSkills, isLoading: popularSkillsLoading } = useQuery({
        queryKey: ['skills', 'popular', timeRange, selectedCategory],
        queryFn: () => getPopularSkills(20, timeRange, selectedCategory === 'all' ? undefined : selectedCategory),
    });

    const isLoading = statsLoading;

    const timeRangeOptions = [
        { value: 30, label: '30 days' },
        { value: 90, label: '90 days' },
        { value: 180, label: '6 months' },
        { value: 365, label: '1 year' },
    ];

    // Loading state with skeleton
    if (isLoading) {
        return (
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Market Intelligence Dashboard</h1>
                    <p className="text-gray-600 dark:text-gray-400">New Zealand Tech Job Market Overview</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <StatCard key={i} title="" value="" icon={<Briefcase className="w-6 h-6" />} loading={true} />
                    ))}
                </div>
                <div className="flex items-center justify-center min-h-[40vh]">
                    <LoadingSpinner size="lg" text="Loading dashboard data..." />
                </div>
            </div>
        );
    }

    // Error state
    if (!stats && !statsLoading) {
        return (
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Market Intelligence Dashboard</h1>
                    <p className="text-gray-600 dark:text-gray-400">New Zealand Tech Job Market Overview</p>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 border border-red-200 dark:border-red-800 rounded-xl p-8 text-center shadow-lg">
                    <div className="max-w-md mx-auto">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/40 rounded-full mb-4">
                            <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Unable to Load Dashboard Data</h3>
                        <p className="text-gray-700 dark:text-gray-300 mb-6">There was an error fetching the market statistics. Please try again.</p>
                        <button onClick={() => window.location.reload()} className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                <div className="flex-1">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Market Intelligence Dashboard</h1>
                    <p className="text-gray-600 dark:text-gray-400">New Zealand Tech Job Market Overview</p>
                </div>
                <div className="flex items-center gap-3 md:mt-2">
                    <FilterDropdown label="Time Period" value={timeRange} options={timeRangeOptions} onChange={(val) => setTimeRange(val as number)} />
                </div>
            </div>

            {/* Stats Grid */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <StatCard title="Total Jobs" value={stats.total_jobs} icon={<Briefcase className="w-6 h-6" />} color="blue" subtitle={`${stats.active_jobs} active`} />
                    <StatCard title="Companies Hiring" value={stats.total_companies} icon={<Building2 className="w-6 h-6" />} color="purple" subtitle={`${stats.hiring_companies} actively hiring`} />
                    <StatCard title="Average Salary" value={stats.avg_salary ? `$${Math.round(stats.avg_salary / 1000)}k` : 'N/A'} icon={<DollarSign className="w-6 h-6" />} color="cyan" subtitle={stats.jobs_with_salary > 0 ? `Based on ${stats.jobs_with_salary} jobs with salary data` : 'Per annum (NZD)'} />
                </div>
            )}

            {/* US-1.2: Top Skills Demand Chart */}
                <div className="p-0">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
                        <div className="flex-1">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Top Skills in Demand</h2>
                            <p className="text-gray-600 dark:text-gray-400">Most sought-after technologies in the NZ tech market</p>
                        </div>
                        <div className="flex items-center gap-3 md:mt-1">
                            <FilterDropdown
                                label="Category"
                                value={selectedCategory}
                                options={[
                                    { value: 'all', label: 'All Categories' },
                                    { value: SkillCategory.PROGRAMMING_LANGUAGES, label: 'Programming Languages' },
                                    { value: SkillCategory.WEB_FRAMEWORKS, label: 'Web Frameworks' },
                                    { value: SkillCategory.DATABASES, label: 'Databases' },
                                    { value: SkillCategory.CLOUD_PLATFORMS, label: 'Cloud Platforms' },
                                    { value: SkillCategory.DEVOPS, label: 'DevOps' },
                                    { value: SkillCategory.AI_ML, label: 'AI/ML' },
                                    { value: SkillCategory.MOBILE, label: 'Mobile' },
                                    { value: SkillCategory.OTHER, label: 'Other' },
                                ]}
                                onChange={(val) => setSelectedCategory(val as SkillCategory | 'all')}
                            />
                        </div>
                    </div>

                    {/* Info banner explaining the percentages */}
                    <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <p className="text-xs text-gray-700 dark:text-gray-300">
                            <span className="font-semibold">Understanding the numbers:</span> Percentages show how many jobs require each skill. For example, if Python shows 85%, it means 85% of all tech jobs require Python skills.
                        </p>
                    </div>

                    <SkillGridView
                        data={
                            popularSkills?.map((skill, index) => ({
                                name: skill.display_name || skill.name, // Use display_name for visual display
                                value: skill.job_count,
                                color: getCategoryColor(skill.category),
                                category: skill.category?.replace(/_/g, ' '),
                                rank: index + 1, // Add rank based on position
                                percentage: skill.percentage, // Add percentage if available
                            })) || []
                        }
                        loading={popularSkillsLoading}
                        onSkillClick={(data) => {
                            // Use the original name (not display_name) for URL routing
                            const skill = popularSkills?.find((s) => (s.display_name || s.name) === data.name);
                            const skillSlug = (skill?.name || data.name).toLowerCase().replace(/\s+/g, '-').replace(/\./g, '');
                            navigate(`/skills/${skillSlug}`);
                        }}
                    />

                    <div className="mt-6 text-sm text-gray-500 dark:text-gray-400 text-center">Click on any skill card to see detailed analytics</div>
                </div>


            {/* Quick Links */}
            {/*
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <GlassCard hover={true} onClick={() => (window.location.href = '/skills')}>
                    <div className="p-6 text-center">
                        <Target className="w-12 h-12 mx-auto mb-3 text-blue-600" />
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Skills Analytics</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Explore in-demand skills and trends</p>
                    </div>
                </GlassCard>
                <GlassCard hover={true} onClick={() => (window.location.href = '/skills/compare')}>
                    <div className="p-6 text-center">
                        <TrendingUp className="w-12 h-12 mx-auto mb-3 text-purple-600" />
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Compare Skills</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Compare skills to make learning decisions</p>
                    </div>
                </GlassCard>
                <GlassCard hover={true} onClick={() => (window.location.href = '/companies')}>
                    <div className="p-6 text-center">
                        <Building2 className="w-12 h-12 mx-auto mb-3 text-green-600" />
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Company Tech Stacks</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Discover what technologies companies use</p>
                    </div>
                </GlassCard>
            </div>
            */}
            {/* Data Freshness */}
            {stats && (
                <div className="text-center text-sm text-gray-500 dark:text-gray-400">
                    Data last updated: {new Date(stats.last_updated).toLocaleString('en-NZ', { 
                        timeZone: 'Pacific/Auckland',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                    })} NZST
                </div>
            )}
        </div>
    );
};

export default Dashboard;
