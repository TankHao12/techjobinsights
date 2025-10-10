/**
 * Company Detail Page
 * Displays company tech stack and hiring information
 * US-3.2: Company Tech Stack View
 */

import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
    ArrowLeft,
    Building2,
    Briefcase,
    // Globe,
    TrendingUp,
    Shield,
    CheckCircle,
    AlertCircle,
    BarChart3,
    Search,
    Filter,
} from 'lucide-react';
import { GlassCard, LoadingSpinner, SkillBadge } from '../components/common';
import { getCompanyTechStack } from '../services/companiesService';
import type { TechStackItem } from '../types';

const CompanyDetail: React.FC = () => {
    const { companyId } = useParams<{ companyId: string }>();
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [confidenceFilter, setConfidenceFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

    const {
        data: techStackData,
        isLoading,
        error,
    } = useQuery({
        queryKey: ['companyTechStack', companyId],
        queryFn: () => getCompanyTechStack(Number(companyId)),
        enabled: !!companyId,
    });

    const getConfidenceBadge = (confidence: 'high' | 'medium' | 'low') => {
        const configs = {
            high: {
                icon: CheckCircle,
                color: 'text-green-600 dark:text-green-400',
                bg: 'bg-green-100 dark:bg-green-900/30',
                label: 'High Confidence',
            },
            medium: {
                icon: Shield,
                color: 'text-yellow-600 dark:text-yellow-400',
                bg: 'bg-yellow-100 dark:bg-yellow-900/30',
                label: 'Medium Confidence',
            },
            low: {
                icon: AlertCircle,
                color: 'text-gray-500 dark:text-gray-400',
                bg: 'bg-gray-100 dark:bg-gray-700',
                label: 'Low Confidence',
            },
        };

        const config = configs[confidence];
        const Icon = config.icon;

        return (
            <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${config.bg} ${config.color}`}>
                <Icon className="w-3 h-3" />
                <span>{confidence.charAt(0).toUpperCase() + confidence.slice(1)}</span>
            </div>
        );
    };

    const getCategoryDisplayName = (category: string) => {
        return category
            .split('_')
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    const getCategoryIcon = (category: string) => {
        const icons: Record<string, string> = {
            programming_languages: '💻',
            web_frameworks: '🌐',
            databases: '🗄️',
            cloud_platforms: '☁️',
            devops: '⚙️',
            ai_ml: '🤖',
            mobile: '📱',
            other: '🔧',
        };
        return icons[category.toLowerCase()] || '🔧';
    };

    // Calculate statistics from tech stack data
    const stats = useMemo(() => {
        if (!techStackData?.tech_stack) return null;
        
        const allSkills = Object.values(techStackData.tech_stack).flat();
        const highConfidenceSkills = allSkills.filter(s => s.confidence === 'high');
        const totalMentions = allSkills.reduce((sum, s) => sum + s.count, 0);
        const avgMentionsPerSkill = allSkills.length > 0 ? totalMentions / allSkills.length : 0;
        
        return {
            totalSkills: allSkills.length,
            highConfidence: highConfidenceSkills.length,
            mediumConfidence: allSkills.filter(s => s.confidence === 'medium').length,
            lowConfidence: allSkills.filter(s => s.confidence === 'low').length,
            totalMentions,
            avgMentionsPerSkill: Math.round(avgMentionsPerSkill * 10) / 10,
            topSkill: allSkills.length > 0 ? allSkills.sort((a, b) => b.count - a.count)[0] : null,
        };
    }, [techStackData]);

    // Filter skills based on search and confidence filter
    const filteredTechStack = useMemo(() => {
        if (!techStackData?.tech_stack) return {};
        
        const filtered: Record<string, TechStackItem[]> = {};
        
        Object.entries(techStackData.tech_stack).forEach(([category, skills]) => {
            const filteredSkills = skills.filter((skill: TechStackItem) => {
                const matchesSearch = !searchQuery || 
                    skill.name.toLowerCase().includes(searchQuery.toLowerCase());
                const matchesConfidence = confidenceFilter === 'all' || 
                    skill.confidence === confidenceFilter;
                return matchesSearch && matchesConfidence;
            });
            
            if (filteredSkills.length > 0) {
                filtered[category] = filteredSkills;
            }
        });
        
        return filtered;
    }, [techStackData, searchQuery, confidenceFilter]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <LoadingSpinner size="lg" text="Loading company tech stack..." />
            </div>
        );
    }

    if (error || !techStackData) {
        return (
            <div className="space-y-6">
                <button onClick={() => navigate('/companies')} className="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Companies
                </button>
                <GlassCard>
                    <div className="p-8 text-center">
                        <Building2 className="w-12 h-12 mx-auto mb-4 text-red-600" />
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Company Not Found</h2>
                        <p className="text-gray-600 dark:text-gray-400">{error instanceof Error ? error.message : 'Unable to load company information'}</p>
                    </div>
                </GlassCard>
            </div>
        );
    }

    const categories = Object.keys(filteredTechStack).sort();

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <button onClick={() => navigate('/companies')} className="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-3">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Companies
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">{techStackData.company_name}</h1>
                    <div className="flex items-center gap-4 text-gray-600 dark:text-gray-400">
                        <div className="flex items-center gap-2">
                            <Briefcase className="w-4 h-4" />
                            <span>{techStackData.job_count} job postings analyzed</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Summary Statistics */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <GlassCard>
                        <div className="p-0">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Total Technologies</span>
                                <BarChart3 className="w-4 h-4 text-blue-600" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.totalSkills}</p>
                            <p className="text-xs text-gray-500 mt-1">Across {Object.keys(techStackData.tech_stack || {}).length} categories</p>
                        </div>
                    </GlassCard>
                    
                    <GlassCard>
                        <div className="p-0">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-600 dark:text-gray-400">High Confidence</span>
                                <CheckCircle className="w-4 h-4 text-green-600" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.highConfidence}</p>
                            <div className="flex gap-1 mt-2">
                                <span className="text-xs text-gray-500">M: {stats.mediumConfidence}</span>
                                <span className="text-xs text-gray-400">•</span>
                                <span className="text-xs text-gray-500">L: {stats.lowConfidence}</span>
                            </div>
                        </div>
                    </GlassCard>
                    
                    <GlassCard>
                        <div className="p-0">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Total Mentions</span>
                                <TrendingUp className="w-4 h-4 text-purple-600" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.totalMentions}</p>
                            <p className="text-xs text-gray-500 mt-1">Avg: {stats.avgMentionsPerSkill} per skill</p>
                        </div>
                    </GlassCard>
                    
                    <GlassCard>
                        <div className="p-0">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Most Used</span>
                                <Shield className="w-4 h-4 text-orange-600" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 truncate capitalize">
                                {stats.topSkill?.name || 'N/A'}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">{stats.topSkill?.count || 0} mentions</p>
                        </div>
                    </GlassCard>
                </div>
            )}

            {/* Search and Filters */}
                <div className="p-0">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <input
                                type="text"
                                placeholder="Search technologies..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100 text-sm"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <Filter className="w-4 h-4 text-gray-400" />
                            <select
                                value={confidenceFilter}
                                onChange={(e) => setConfidenceFilter(e.target.value as any)}
                                className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100 text-sm"
                            >
                                <option value="all">All Confidence</option>
                                <option value="high">High Only</option>
                                <option value="medium">Medium Only</option>
                                <option value="low">Low Only</option>
                            </select>
                        </div>
                    </div>
                    {(searchQuery || confidenceFilter !== 'all') && (
                        <div className="mt-3 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <span>Showing {categories.length} categories with {Object.values(filteredTechStack).flat().length} technologies</span>
                            {(searchQuery || confidenceFilter !== 'all') && (
                                <button
                                    onClick={() => {
                                        setSearchQuery('');
                                        setConfidenceFilter('all');
                                    }}
                                    className="text-blue-600 dark:text-blue-400 hover:underline"
                                >
                                    Clear filters
                                </button>
                            )}
                        </div>
                    )}
                </div>

            {/* Tech Stack by Category */}
            {categories.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {categories.map((category) => {
                        const skills = filteredTechStack[category as keyof typeof filteredTechStack];

                        if (!skills || skills.length === 0) return null;

                        const displayName = getCategoryDisplayName(category);
                        const icon = getCategoryIcon(category);
                        const maxCount = Math.max(...skills.map((s: TechStackItem) => s.count));

                        return (
                            <GlassCard key={category}>
                                <div className="p-0">
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="text-2xl">{icon}</span>
                                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{displayName}</h3>
                                        <span className="ml-auto text-sm text-gray-500">
                                            {skills.length} {skills.length === 1 ? 'skill' : 'skills'}
                                        </span>
                                    </div>

                                    <div className="space-y-4">
                                        {skills.map((skill: TechStackItem, index: number) => {
                                            const percentage = (skill.count / maxCount) * 100;
                                            const barColor = skill.confidence === 'high' 
                                                ? 'bg-green-500' 
                                                : skill.confidence === 'medium' 
                                                ? 'bg-yellow-500' 
                                                : 'bg-gray-400';
                                            
                                            return (
                                                <div 
                                                    key={index} 
                                                    className="group cursor-pointer" 
                                                    onClick={() => navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-')}`)}
                                                >
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="flex items-center gap-3">
                                                            <span className="font-medium text-gray-900 dark:text-gray-100 capitalize group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                                                {skill.name}
                                                            </span>
                                                            {getConfidenceBadge(skill.confidence)}
                                                        </div>
                                                        <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                                            {skill.count}
                                                        </span>
                                                    </div>
                                                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                                                        <div 
                                                            className={`h-full ${barColor} transition-all duration-300 group-hover:opacity-80`}
                                                            style={{ width: `${percentage}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </GlassCard>
                        );
                    })}
                </div>
            ) : (
                <GlassCard>
                    <div className="p-8 text-center">
                        <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                            {searchQuery || confidenceFilter !== 'all' 
                                ? 'No Technologies Match Your Filters' 
                                : 'No Tech Stack Data Available'
                            }
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400">
                            {searchQuery || confidenceFilter !== 'all'
                                ? 'Try adjusting your search or filters.'
                                : "This company doesn't have any analyzed tech job postings yet."
                            }
                        </p>
                    </div>
                </GlassCard>
            )}

            {/* Info banner explaining the confidence level */}
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-xs text-gray-700 dark:text-gray-300">
                    <span className="font-semibold">Understanding the confidence level:</span> Confidence level is based on the frequency and context in job postings, more than 5 is high and less than 3 is low.
                </p>
            </div>

            {/* Key Technologies Summary - Only show when no filters applied */}
            {categories.length > 0 && !searchQuery && confidenceFilter === 'all' && techStackData?.tech_stack && (
                    <div className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <TrendingUp className="w-5 h-5 text-blue-600" />
                            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">Top Technologies (High Confidence)</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {Object.values(techStackData.tech_stack)
                                .flat()
                                .filter((skill: TechStackItem) => skill.confidence === 'high')
                                .sort((a: TechStackItem, b: TechStackItem) => b.count - a.count)
                                .slice(0, 15)
                                .map((skill: TechStackItem, index: number) => (
                                    <SkillBadge 
                                        key={index} 
                                        name={skill.name} 
                                        size="md" 
                                        className="cursor-pointer" 
                                        onClick={() => navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-')}`)} 
                                    />
                                ))}
                        </div>
                        {Object.values(techStackData.tech_stack)
                            .flat()
                            .filter((skill: TechStackItem) => skill.confidence === 'high').length === 0 && (
                            <p className="text-gray-600 dark:text-gray-400 text-center py-4">
                                No high-confidence technologies yet. Check medium and low confidence skills above.
                            </p>
                        )}
                    </div>
            )}
        </div>
    );
};

export default CompanyDetail;
