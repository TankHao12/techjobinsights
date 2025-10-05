/**
 * Tracked Keywords Page
 * Displays search terms used for scraping and skills taxonomy monitored by the platform
 * Shows transparency in data collection and processing methodology
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Code, Filter, Database, TrendingUp, Info, Target, X } from 'lucide-react';
import { getTrackedKeywords } from '../services/trackedKeywordsService';
import { LoadingSpinner } from '../components/common';
import { GlassCard } from '../components/common/GlassCard';
import SkillBadge from '../components/common/SkillBadge';
import type { SkillCategory } from '../types';

// Category Icons Mapping
const categoryIcons: Record<string, React.ReactNode> = {
    programming_languages: <Code className="w-5 h-5" />,
    web_frameworks: <TrendingUp className="w-5 h-5" />,
    databases: <Database className="w-5 h-5" />,
    cloud_platforms: <Filter className="w-5 h-5" />,
    devops: <Filter className="w-5 h-5" />,
    ai_ml: <TrendingUp className="w-5 h-5" />,
    mobile: <Code className="w-5 h-5" />,
    testing: <Filter className="w-5 h-5" />,
    tools_and_methodologies: <Database className="w-5 h-5" />,
    other: <Info className="w-5 h-5" />,
};

// Category color mappings for consistent styling
const categoryColors: Record<string, string> = {
    programming_languages: 'from-blue-500 to-blue-600',
    web_frameworks: 'from-purple-500 to-purple-600',
    databases: 'from-green-500 to-green-600',
    cloud_platforms: 'from-cyan-500 to-cyan-600',
    devops: 'from-orange-500 to-orange-600',
    ai_ml: 'from-pink-500 to-pink-600',
    mobile: 'from-indigo-500 to-indigo-600',
    testing: 'from-yellow-500 to-yellow-600',
    tools_and_methodologies: 'from-gray-500 to-gray-600',
    other: 'from-gray-400 to-gray-500',
};

const TrackedKeywords: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState('');

    // Fetch tracked keywords data
    const { data, isLoading, error } = useQuery({
        queryKey: ['tracked-keywords'],
        queryFn: getTrackedKeywords,
        staleTime: 10 * 60 * 1000, // 10 minutes - this data doesn't change often
    });

    // Filter search terms based on search query
    const filteredSearchTerms = data?.search_terms.filter((term) => term.toLowerCase().includes(searchQuery.toLowerCase()));

    // Filter skills taxonomy based on search query
    const filteredTaxonomy = data?.skills_taxonomy
        ? Object.entries(data.skills_taxonomy).reduce((acc, [category, categoryData]) => {
              const filteredSkills = categoryData.skills.filter((skill) => skill.name.toLowerCase().includes(searchQuery.toLowerCase()) || skill.display_name.toLowerCase().includes(searchQuery.toLowerCase()));
              if (filteredSkills.length > 0) {
                  acc[category] = { ...categoryData, skills: filteredSkills };
              }
              return acc;
          }, {} as typeof data.skills_taxonomy)
        : {};

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <LoadingSpinner size="lg" text="Loading tracked keywords..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Tracked Keywords</h1>
                <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 border border-red-200 dark:border-red-800 rounded-xl p-8 text-center">
                    <p className="text-red-600 dark:text-red-400">Failed to load tracked keywords data</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="space-y-4">
                {/* Title - On Top */}
                <div>
                    <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">Tracked Keywords & Skills</h1>
                    <p className="text-sm md:text-base text-gray-600 dark:text-gray-400">Transparency in our data collection: Search terms we monitor and skills we track</p>
                </div>

                {/* Stats Summary - Below header, horizontal: Terms | Categories | Skills */}
                <div className="grid grid-cols-3 gap-3 md:gap-4 lg:gap-6">
                    {/* Terms - Left */}
                    <GlassCard hover={false}>
                        <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                            <div className="p-1.5 sm:p-2.5 md:p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex-shrink-0">
                                <Search className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div className="min-w-0">
                                <p className="text-[9px] sm:text-xs md:text-sm text-gray-600 dark:text-gray-400 truncate">Terms</p>
                                <p className="text-sm sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100">{data?.total_search_terms || 0}</p>
                            </div>
                        </div>
                    </GlassCard>

                    {/* Categories - Middle */}
                    <GlassCard hover={false}>
                        <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                            <div className="p-1.5 sm:p-2.5 md:p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex-shrink-0">
                                <Filter className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-purple-600 dark:text-purple-400" />
                            </div>
                            <div className="min-w-0">
                                <p className="text-[9px] sm:text-xs md:text-sm text-gray-600 dark:text-gray-400 truncate">Categories</p>
                                <p className="text-sm sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100">{data?.total_skill_categories || 0}</p>
                            </div>
                        </div>
                    </GlassCard>

                    {/* Skills - Right */}
                    <GlassCard hover={false}>
                        <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                            <div className="p-1.5 sm:p-2.5 md:p-3 bg-green-100 dark:bg-green-900/30 rounded-lg flex-shrink-0">
                                <Code className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-green-600 dark:text-green-400" />
                            </div>
                            <div className="min-w-0">
                                <p className="text-[9px] sm:text-xs md:text-sm text-gray-600 dark:text-gray-400 truncate">Skills</p>
                                <p className="text-sm sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100">{data?.total_skills || 0}</p>
                            </div>
                        </div>
                    </GlassCard>
                </div>

                {/* Search Bar - Enhanced with better spacing and properly positioned clear button */}
                <div className="relative w-full">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none z-10">
                        <Search className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search keywords or skills..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full h-10 pl-11 pr-12 rounded-xl text-sm
                     bg-white dark:bg-gray-800
                     backdrop-blur-md
                     border border-gray-200 dark:border-gray-700
                     text-gray-900 dark:text-white
                     placeholder-gray-500 dark:placeholder-gray-400
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     hover:border-gray-300 dark:hover:border-gray-600
                     transition-all duration-200
                     shadow-sm hover:shadow-md"
                    />
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2
                       flex items-center justify-center
                       w-6 h-6 rounded-full
                       bg-gray-200 dark:bg-gray-700
                       hover:bg-gray-300 dark:hover:bg-gray-600
                       text-gray-600 dark:text-gray-300
                       hover:text-gray-900 dark:hover:text-white
                       transition-all duration-200
                       focus:outline-none focus:ring-2 focus:ring-blue-500/50
                       cursor-pointer
                       flex-shrink-0
                       z-10"
                            aria-label="Clear search"
                            type="button"
                        >
                            <X className="w-3.5 h-3.5" />
                        </button>
                    )}
                </div>
            </div>

            {/* Search Terms Section */}
            <div>
                <div className="mb-4">
                    <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Job Search Terms</h2>
                    <p className="text-sm md:text-base text-gray-600 dark:text-gray-400">These are the job role keywords we use to scrape data from Seek.co.nz</p>
                </div>

                <GlassCard hover={false}>
                    {filteredSearchTerms && filteredSearchTerms.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                            {filteredSearchTerms.map((term) => (
                                <span key={term} className="px-2 md:px-1 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm md:text-base font-medium border border-blue-200 dark:border-blue-800 transition-all hover:shadow-sm hover:scale-105">
                                    {term}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <div className="inline-flex items-center justify-center w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-full mb-3">
                                <Search className="w-6 h-6 text-gray-400" />
                            </div>
                            <p className="text-gray-500 dark:text-gray-400 font-medium">No search terms match your query</p>
                        </div>
                    )}
                </GlassCard>
            </div>

            {/* Skills Taxonomy Section */}
            <div>
                <div className="mb-4 md:mb-6">
                    <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Skills Taxonomy</h2>
                    <p className="text-sm md:text-base text-gray-600 dark:text-gray-400">Technical skills we extract and monitor from job descriptions using NLP</p>
                </div>

                {/* Category Grid - Responsive 2 columns on desktop, 1 on mobile */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
                    {Object.entries(filteredTaxonomy).map(([category, categoryData]) => {
                        const icon = categoryIcons[category] || categoryIcons.other;
                        const gradient = categoryColors[category] || categoryColors.other;

                        return (
                            <GlassCard key={category} hover={false} className="overflow-hidden h-fit">
                                {/* Category Header - Improved spacing and readability */}
                                <div className={`bg-gradient-to-r ${gradient} px-4 py-3 -m-6 mb-4`}>
                                    <div className="flex items-center gap-4 md:gap-5">
                                        <div className="p-2 md:p-2.5 bg-white/20 dark:bg-white/10 rounded-lg backdrop-blur-sm flex-shrink-0">{icon}</div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="text-base md:text-lg font-bold text-gray-900 dark:text-white truncate">{categoryData.display_name}</h3>
                                            <p className="text-xs text-gray-800 dark:text-white/90 font-medium">
                                                {categoryData.skills.length} skill
                                                {categoryData.skills.length !== 1 ? 's' : ''}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Skills Grid - Better wrapping and spacing */}
                                <div className="flex flex-wrap gap-2">
                                    {categoryData.skills.map((skill) => (
                                        <SkillBadge key={skill.name} name={skill.display_name} category={category as SkillCategory} size="md" />
                                    ))}
                                </div>
                            </GlassCard>
                        );
                    })}
                </div>

                {Object.keys(filteredTaxonomy).length === 0 && (
                    <GlassCard hover={false}>
                        <div className="text-center py-12">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
                                <Target className="w-8 h-8 text-gray-400" />
                            </div>
                            <p className="text-gray-500 dark:text-gray-400 text-lg font-medium">No skills match your search query</p>
                            <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Try adjusting your search terms or filters</p>
                        </div>
                    </GlassCard>
                )}
            </div>

            {/* Info Footer */}
            <GlassCard hover={false} className="bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-900/30">
                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex items-start gap-3 sm:flex-row">
                        <div className="flex-shrink-0">
                            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                <Info className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            </div>
                        </div>
                        <div className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                            <p className="font-semibold mb-2 text-gray-900 dark:text-gray-100">About Our Data Collection</p>
                            <p className="leading-relaxed">We continuously monitor job postings from Seek.co.nz using these search terms. Our NLP engine extracts and categorizes technical skills from job descriptions to provide accurate market intelligence. This transparency helps you understand what data we track and how we process it.</p>
                        </div>
                    </div>
                </div>
            </GlassCard>
        </div>
    );
};

export default TrackedKeywords;
