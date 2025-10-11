/**
 * Skills Analytics Page - Enhanced UI/UX
 * Displays skill demand, categories, and trends with improved layout
 * US-2.1: Skills by Category Browser
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Target, Link2, Zap, ArrowRight, X, Lightbulb, AlertCircle } from 'lucide-react';
import { getPopularSkills, getSkillsByCategory, getSkillPairs, getSkillRecommendations } from '../services/skillsService';
import { getDashboardStats } from '../services/dashboardService';
import { LoadingSpinner, FilterDropdown } from '../components/common';
import { GlassCard } from '../components/common/GlassCard';
import { SkillMultiSelect } from '../components/common/SkillMultiSelect';
import type { SkillWithStats } from '../types';

// Add interface for category modal
interface CategoryModalData {
    category: string;
    displayName: string;
    icon: string;
    skills: SkillWithStats[];
    totalJobs: number;
}

// Category Icons Mapping
const categoryIcons: Record<string, string> = {
    programming_languages: '💻',
    web_frameworks: '🌐',
    databases: '🗄️',
    cloud_platforms: '☁️',
    devops: '🔧',
    ai_ml: '🤖',
    mobile: '📱',
    testing: '🧪',
    tools_and_methodologies: '🛠️',
    other: '🔨',
};

// Tab types
type SkillsTab = 'categories' | 'top-skills' | 'combinations';

const Skills: React.FC = () => {
    const navigate = useNavigate();
    const [timeRange, setTimeRange] = useState<number>(90);
    const [categoryModal, setCategoryModal] = useState<CategoryModalData | null>(null);
    const [activeTab, setActiveTab] = useState<SkillsTab>('categories');

    // Recommendation feature state
    const [knownSkills, setKnownSkills] = useState<string[]>([]);
    const [recommendations, setRecommendations] = useState<any>(null);
    const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);

    // Prevent body scroll when modal is open
    React.useEffect(() => {
        if (categoryModal) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [categoryModal]);

    // Handle URL query parameters for tab navigation
    React.useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const tabParam = params.get('tab') as SkillsTab;
        if (tabParam && ['categories', 'top-skills', 'combinations'].includes(tabParam)) {
            setActiveTab(tabParam);
        }
    }, []);

    // Update URL when tab changes
    const handleTabChange = (tab: SkillsTab) => {
        setActiveTab(tab);
        const params = new URLSearchParams(window.location.search);
        params.set('tab', tab);
        window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
    };

    // Fetch popular skills (no category filtering)
    const { data: skills, isLoading: skillsLoading } = useQuery({
        queryKey: ['skills', 'popular', timeRange],
        queryFn: () => getPopularSkills(20, timeRange),
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

    // Fetch dashboard stats for accurate total job count
    const { data: dashboardStats } = useQuery({
        queryKey: ['dashboard', 'stats', timeRange],
        queryFn: () => getDashboardStats(timeRange),
        staleTime: 0, // Always fetch fresh data when timeRange changes
    });

    const isLoading = skillsLoading || categoriesLoading;

    // Handle getting skill recommendations
    const handleGetRecommendations = async () => {
        if (knownSkills.length === 0) return;

        setIsLoadingRecommendations(true);
        try {
            const result = await getSkillRecommendations(knownSkills, 10);
            setRecommendations(result);
        } catch (error) {
            console.error('Failed to get recommendations:', error);
        } finally {
            setIsLoadingRecommendations(false);
        }
    };

    const timeRangeOptions = [
        { value: 30, label: '30 days' },
        { value: 90, label: '90 days' },
        { value: 180, label: '6 months' },
        { value: 365, label: '1 year' },
        { value: 0, label: 'All time' },
    ];

    // Use actual total jobs from dashboard (not sum of categories which double-counts)
    const totalJobs = dashboardStats?.total_jobs || 0;

    return (
        <>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Skills Analytics</h1>
                        <p className="text-gray-600 dark:text-gray-400">Explore in-demand skills and make informed learning decisions</p>
                    </div>
                    <div className="flex gap-3">
                        <FilterDropdown label="Time Period" value={timeRange} options={timeRangeOptions} onChange={(val) => setTimeRange(val as number)} />
                    </div>
                </div>

                {/* Tab Navigation */}
                <div className="border-b border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-1">
                        <button type="button" onClick={() => handleTabChange('categories')} className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'categories' ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400' : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600'}`}>
                            <span className="flex items-center gap-2">
                                <span>📊</span>
                                <span>Browse by Categories</span>
                            </span>
                        </button>
                        <button type="button" onClick={() => handleTabChange('top-skills')} className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'top-skills' ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400' : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600'}`}>
                            <span className="flex items-center gap-2">
                                <span>🎯</span>
                                <span>Top Skills</span>
                            </span>
                        </button>
                        <button type="button" onClick={() => handleTabChange('combinations')} className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'combinations' ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400' : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600'}`}>
                            <span className="flex items-center gap-2">
                                <span>🔗</span>
                                <span>Skill Combinations</span>
                            </span>
                        </button>
                    </div>
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center min-h-[60vh]">
                        <LoadingSpinner size="lg" text="Loading skills data..." />
                    </div>
                ) : (
                    <>
                        {/* Tab Content: Categories */}
                        {activeTab === 'categories' && categories && categories.length > 0 && (
                            <div className="animate-fadeIn">
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Browse by Category</h2>
                                    <div className="text-sm text-gray-500 dark:text-gray-400">
                                        {categories.length} categories • {totalJobs > 0 ? `${totalJobs.toLocaleString()} unique jobs` : 'Loading...'}
                                    </div>
                                </div>

                                {/* Info banner explaining the metrics */}
                                <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                    <p className="text-xs text-gray-700 dark:text-gray-300">
                                        💡 <span className="font-semibold">Understanding the numbers:</span> Click any category card to view details. Percentages show how many jobs require each skill within that category.
                                    </p>
                                </div>

                                {/* 3-column grid for better layout with 9 categories */}
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {categories.map((cat) => {
                                        const categoryKey = cat.category as string;
                                        const icon = categoryIcons[categoryKey] || '🔨';

                                        return (
                                            <GlassCard
                                                key={cat.category}
                                                hover={true}
                                                onClick={() => {
                                                    // Open modal with category details
                                                    setCategoryModal({
                                                        category: cat.category,
                                                        displayName: cat.category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
                                                        icon: icon,
                                                        skills: cat.skills,
                                                        totalJobs: cat.total_jobs,
                                                    });
                                                }}
                                                className="cursor-pointer transition-all duration-200 hover:shadow-md"
                                            >
                                                <div className="p-5">
                                                    {/* Category Icon and Name */}
                                                    <div className="flex items-center gap-3 mb-3">
                                                        <span className="text-3xl">{icon}</span>
                                                        <h3 className="font-bold text-base text-gray-900 dark:text-gray-100">{cat.category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}</h3>
                                                    </div>

                                                    {/* Total jobs in category */}
                                                    <div className="mb-4">
                                                        <div className="flex items-baseline gap-2">
                                                            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">{cat.total_jobs.toLocaleString()}</span>
                                                            <span className="text-sm text-gray-600 dark:text-gray-400">jobs</span>
                                                        </div>
                                                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                                            {cat.skills.length} {cat.skills.length === 1 ? 'skill' : 'skills'} in category
                                                        </div>
                                                    </div>

                                                    {/* Top 5 Skills - percentages relative to category */}
                                                    <div className="space-y-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                                                        {cat.skills.slice(0, 5).map((skill: any, idx) => {
                                                            // Use category_percentage from backend (percentage within category)
                                                            const skillPercentage = skill.category_percentage || skill.percentage || 0;

                                                            return (
                                                                <div key={skill.id} className="px-2 py-2 rounded">
                                                                    <div className="flex justify-between items-center">
                                                                        <span className="text-sm text-gray-700 dark:text-gray-300 truncate font-medium flex-1">
                                                                            {idx + 1}. {skill.display_name || skill.name}
                                                                        </span>
                                                                        <div className="flex items-baseline gap-1.5 ml-2 flex-shrink-0">
                                                                            <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{skillPercentage.toFixed(1)}%</span>
                                                                            <span className="text-sm text-gray-500 dark:text-gray-400">({skill.job_count.toLocaleString()})</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>

                                                    {/* View All button */}
                                                    {cat.skills.length > 5 && (
                                                        <button
                                                            type="button"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setCategoryModal({
                                                                    category: cat.category,
                                                                    displayName: cat.category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
                                                                    icon: icon,
                                                                    skills: cat.skills,
                                                                    totalJobs: cat.total_jobs,
                                                                });
                                                            }}
                                                            className="w-full text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mt-3 py-2 font-medium text-center rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                                                        >
                                                            View all {cat.skills.length} skills →
                                                        </button>
                                                    )}
                                                </div>
                                            </GlassCard>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Tab Content: Top Skills */}
                        {activeTab === 'top-skills' && skills && skills.length > 0 && (
                            <div className="animate-fadeIn">
                                <GlassCard hover={false}>
                                    <div className="p-6">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Target className="text-blue-600" />
                                            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Top Skills in Demand</h2>
                                        </div>

                                        {/* Info banner */}
                                        <div className="mb-6 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                            <p className="text-xs text-gray-700 dark:text-gray-300">
                                                💡 <span className="font-semibold">Understanding the numbers:</span> Percentages show how many jobs require each skill. For example, if Python shows 85%, it means 85% of all tech jobs require Python skills.
                                            </p>
                                        </div>

                                        {/* Single clean list view */}
                                        <div className="space-y-3">
                                            {skills.map((skill, index) => {
                                                // Use percentage from backend (percentage of total tech jobs)
                                                const percentageOfJobs = skill.percentage || 0;

                                                return (
                                                    <div key={skill.id} onClick={() => navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-')}`)} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg cursor-pointer border border-gray-200 dark:border-gray-700">
                                                        <div className="flex items-center gap-4 flex-1 min-w-0">
                                                            <span className="text-xl font-bold text-gray-400 dark:text-gray-500 w-8 flex-shrink-0">#{index + 1}</span>
                                                            <div className="flex-1 min-w-0">
                                                                <h3 className="font-semibold text-base text-gray-900 dark:text-gray-100 truncate">{skill.name}</h3>
                                                                <p className="text-sm text-gray-600 dark:text-gray-400 truncate">{skill.category?.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}</p>
                                                            </div>
                                                        </div>

                                                        <div className="flex items-center gap-4 flex-shrink-0 ml-4">
                                                            {/* Percentage badge */}
                                                            <div className="text-center px-4 py-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                                                <div className="text-xl font-bold text-blue-600 dark:text-blue-400">{percentageOfJobs.toFixed(1)}%</div>
                                                                <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">of jobs</div>
                                                            </div>

                                                            {/* Job count */}
                                                            <div className="text-right">
                                                                <div className="font-semibold text-gray-900 dark:text-gray-100">{skill.job_count.toLocaleString()}</div>
                                                                <div className="text-xs text-gray-500 dark:text-gray-400">jobs</div>
                                                            </div>

                                                            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>

                                        {/* Summary footer */}
                                        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                                            <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                                                <span>Showing top {skills.length} most in-demand skills</span>
                                                <span>Based on {totalJobs.toLocaleString()} total jobs</span>
                                            </div>
                                        </div>
                                    </div>
                                </GlassCard>
                            </div>
                        )}

                        {/* Tab Content: Skill Combinations & Recommendations */}
                        {activeTab === 'combinations' && (
                            <div className="animate-fadeIn space-y-6">
                                {/* Skill Recommender Tool */}
                                <GlassCard hover={false}>
                                    <div className="p-0">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Lightbulb className="text-yellow-600" />
                                            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">What Should I Learn Next?</h2>
                                        </div>
                                        <p className="text-gray-600 dark:text-gray-400 mb-6">Enter skills you already know, and we'll recommend what to learn next based on real job market data.</p>

                                        {/* Skill Input */}
                                        <div className="mb-6">
                                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Skills You Know:</label>
                                            <SkillMultiSelect selectedSkills={knownSkills} onChange={setKnownSkills} placeholder="Type to add skills (e.g., Python, SQL, React)" />
                                        </div>

                                        <button type="button" onClick={handleGetRecommendations} disabled={knownSkills.length === 0 || isLoadingRecommendations} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
                                            {isLoadingRecommendations ? 'Getting Recommendations...' : 'Get Recommendations'}
                                        </button>

                                        {/* Recommendations Results */}
                                        {recommendations && (
                                            <div className="mt-6">
                                                {recommendations.recommendations && recommendations.recommendations.length > 0 ? (
                                                    <div className="space-y-3">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100">Recommended Skills:</h3>
                                                            <span className="text-sm text-gray-500 dark:text-gray-400">Based on: {recommendations.known_skills.join(', ')}</span>
                                                        </div>
                                                        {recommendations.recommendations.map((rec: any) => (
                                                            <div key={rec.skill} className="border rounded-lg p-4 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer" onClick={() => navigate(`/skills/${rec.skill.toLowerCase().replace(/\s+/g, '-')}`)}>
                                                                <div className="flex justify-between items-start">
                                                                    <div className="flex-1">
                                                                        <h4 className="font-semibold text-lg text-gray-900 dark:text-gray-100 capitalize">{rec.skill}</h4>
                                                                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.reason}</p>
                                                                    </div>
                                                                    <div className="text-right ml-4">
                                                                        <div className="text-2xl font-bold text-blue-600">{rec.relevance_score}%</div>
                                                                        <div className="text-xs text-gray-500 dark:text-gray-400">relevance</div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex gap-4 mt-3 text-sm text-gray-600 dark:text-gray-400">
                                                                    <span>📊 {rec.job_count} jobs</span>
                                                                    <span>📈 {rec.market_demand}% market demand</span>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <div className="mt-6 p-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                                                        <div className="flex items-start gap-3">
                                                            <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                                                            <div>
                                                                <h4 className="font-semibold text-amber-900 dark:text-amber-100 mb-2">No Recommendations Found</h4>
                                                                <p className="text-sm text-amber-800 dark:text-amber-200 mb-3">{recommendations.message || "We couldn't find skills that commonly appear with the ones you entered."}</p>
                                                                <div className="text-sm text-amber-700 dark:text-amber-300">
                                                                    <p className="font-medium mb-1">Possible reasons:</p>
                                                                    <ul className="list-disc list-inside space-y-1 ml-2">
                                                                        <li>The skill names might not match our database exactly</li>
                                                                        <li>These skills rarely appear together in job postings</li>
                                                                        <li>Try using more common or different skill names</li>
                                                                    </ul>
                                                                </div>
                                                                <div className="mt-3 text-sm">
                                                                    <p className="font-medium text-amber-900 dark:text-amber-100 mb-1">💡 Tips:</p>
                                                                    <ul className="text-amber-700 dark:text-amber-300 space-y-1">
                                                                        <li>• Use the autocomplete suggestions when typing</li>
                                                                        <li>• Try popular skills like "Python", "JavaScript", "SQL"</li>
                                                                        <li>• Check spelling and capitalization</li>
                                                                    </ul>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </GlassCard>

                                {/* Popular Skill Combinations */}
                                {skillPairs && skillPairs.length > 0 && (
                                    <GlassCard>
                                        <div className="p-0">
                                            <div className="flex items-center gap-2 mb-4">
                                                <Link2 className="text-purple-600" />
                                                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">Popular Skill Combinations</h3>
                                            </div>
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">Skills that frequently appear together. Percentage shows how many jobs require both skills.</p>

                                            {/* 2-column grid for skill combinations */}
                                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                                                {skillPairs.slice(0, 10).map((pair, index) => {
                                                    const strengthColor = pair.strength === 'high' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : pair.strength === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';

                                                    return (
                                                        <div key={`${pair.skill1}-${pair.skill2}`} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                                                    <span className="text-sm font-medium text-gray-400 dark:text-gray-500 w-6 flex-shrink-0">{index + 1}</span>
                                                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                                                        <button type="button" onClick={() => navigate(`/skills/${pair.skill1.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`)} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors text-xs font-medium capitalize truncate">
                                                                            {pair.skill1}
                                                                        </button>
                                                                        <Zap className="w-3 h-3 text-gray-400 flex-shrink-0" />
                                                                        <button type="button" onClick={() => navigate(`/skills/${pair.skill2.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`)} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors text-xs font-medium capitalize truncate">
                                                                            {pair.skill2}
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${strengthColor}`}>{pair.strength}</span>
                                                                <div className="text-right">
                                                                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 whitespace-nowrap">{pair.job_count}</div>
                                                                    <div className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">{pair.percentage.toFixed(0)}%</div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            {/* View Comparison Link */}
                                            <div className="mt-6 text-center">
                                                <button type="button" onClick={() => navigate('/skills/compare')} className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-lg transition-all font-medium shadow-md hover:shadow-lg">
                                                    Compare Skills Side-by-Side
                                                </button>
                                            </div>
                                        </div>
                                    </GlassCard>
                                )}
                            </div>
                        )}

                        {/* No Data State */}
                        {(!skills || skills.length === 0) && !isLoading && (
                            <div className="text-center py-12">
                                <p className="text-gray-600 dark:text-gray-400">No skills data available for the selected filters.</p>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Category Detail Modal - Rendered outside main container for proper overlay */}
            {categoryModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4" onClick={() => setCategoryModal(null)} style={{ margin: 0 }}>
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden border border-gray-200 dark:border-gray-700" onClick={(e) => e.stopPropagation()}>
                        {/* Modal Header */}
                        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between z-10">
                            <div className="flex items-center gap-3">
                                <span className="text-3xl">{categoryModal.icon}</span>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{categoryModal.displayName}</h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        {categoryModal.totalJobs.toLocaleString()} jobs • {categoryModal.skills.length} skills
                                    </p>
                                </div>
                            </div>
                            <button type="button" onClick={() => setCategoryModal(null)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="Close">
                                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                            </button>
                        </div>

                        {/* Modal Body - Scrollable */}
                        <div className="overflow-y-auto max-h-[calc(85vh-80px)] px-6 py-4">
                            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                <p className="text-xs text-gray-700 dark:text-gray-300">💡 Percentages show what portion of jobs in this category require each skill. Click on any skill to view detailed analytics.</p>
                            </div>

                            {/* All Skills in Category */}
                            <div className="space-y-2">
                                {categoryModal.skills.map((skill: any, idx) => {
                                    // Use category_percentage from backend
                                    const skillPercentage = skill.category_percentage || skill.percentage || 0;

                                    return (
                                        <div
                                            key={skill.id}
                                            className="group hover:bg-gray-50 dark:hover:bg-gray-800/50 p-3 rounded-lg transition-colors cursor-pointer border border-gray-200 dark:border-gray-700"
                                            onClick={() => {
                                                setCategoryModal(null);
                                                navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`);
                                            }}
                                        >
                                            <div className="flex justify-between items-center">
                                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                                    <span className="text-sm font-bold text-gray-400 dark:text-gray-500 w-8 flex-shrink-0">#{idx + 1}</span>
                                                    <span className="text-sm text-gray-900 dark:text-gray-100 font-medium truncate flex-1">{skill.display_name || skill.name}</span>
                                                </div>
                                                <div className="flex items-center gap-3 flex-shrink-0 ml-4">
                                                    <div className="text-right">
                                                        <div className="text-sm font-bold text-blue-600 dark:text-blue-400">{skillPercentage.toFixed(1)}%</div>
                                                        <div className="text-xs text-gray-500 dark:text-gray-400">{skill.job_count.toLocaleString()} jobs</div>
                                                    </div>
                                                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Summary at bottom */}
                            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <div className="grid grid-cols-2 gap-4 text-center">
                                    <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{categoryModal.skills.length}</div>
                                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Total Skills</div>
                                    </div>
                                    <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{categoryModal.totalJobs.toLocaleString()}</div>
                                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Total Jobs</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default Skills;
