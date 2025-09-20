/**
 * Company Detail Page
 * Displays company tech stack and hiring information
 * US-3.2: Company Tech Stack View
 */

import React from 'react';
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
} from 'lucide-react';
import { GlassCard, LoadingSpinner, SkillBadge } from '../components/common';
import { getCompanyTechStack } from '../services/companiesService';
import type { TechStackItem } from '../types';

const CompanyDetail: React.FC = () => {
    const { companyId } = useParams<{ companyId: string }>();
    const navigate = useNavigate();

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

    const techStack = techStackData.tech_stack || {};
    const categories = Object.keys(techStack).sort();

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

            {/* Tech Stack Overview */}
            <GlassCard>
                <div className="p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <TrendingUp className="w-6 h-6 text-blue-600" />
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Technology Stack</h2>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">Based on {techStackData.job_count} tech job postings over the last 90 days. Confidence levels indicate how frequently each technology appears in job requirements.</p>

                    {/* Confidence Legend */}
                    <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-green-500"></div>
                            <span className="text-sm text-gray-700 dark:text-gray-300">High (&gt;5 mentions)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                            <span className="text-sm text-gray-700 dark:text-gray-300">Medium (3-5 mentions)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                            <span className="text-sm text-gray-700 dark:text-gray-300">Low (1-2 mentions)</span>
                        </div>
                    </div>
                </div>
            </GlassCard>

            {/* Tech Stack by Category */}
            {categories.length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {categories.map((category) => {
                        const skills = techStack[category as keyof typeof techStack];

                        if (!skills || skills.length === 0) return null;

                        const displayName = getCategoryDisplayName(category);
                        const icon = getCategoryIcon(category);

                        return (
                            <GlassCard key={category}>
                                <div className="p-6">
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="text-2xl">{icon}</span>
                                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{displayName}</h3>
                                        <span className="ml-auto text-sm text-gray-500">
                                            {skills.length} {skills.length === 1 ? 'skill' : 'skills'}
                                        </span>
                                    </div>

                                    <div className="space-y-3">
                                        {skills.map((skill: TechStackItem, index: number) => (
                                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer" onClick={() => navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-')}`)}>
                                                <div className="flex items-center gap-3 flex-1">
                                                    <span className="font-medium text-gray-900 dark:text-gray-100 capitalize">{skill.name}</span>
                                                    <span className="text-sm text-gray-500">
                                                        ({skill.count} {skill.count === 1 ? 'mention' : 'mentions'})
                                                    </span>
                                                </div>
                                                {getConfidenceBadge(skill.confidence)}
                                            </div>
                                        ))}
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
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">No Tech Stack Data Available</h3>
                        <p className="text-gray-600 dark:text-gray-400">This company doesn't have any analyzed tech job postings yet.</p>
                    </div>
                </GlassCard>
            )}

            {/* Key Technologies Summary */}
            {categories.length > 0 && (
                <GlassCard>
                    <div className="p-6">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Most Used Technologies</h3>
                        <div className="flex flex-wrap gap-2">
                            {categories
                                .flatMap((cat) => techStack[cat as keyof typeof techStack] || [])
                                .filter((skill) => skill.confidence === 'high')
                                .sort((a, b) => b.count - a.count)
                                .slice(0, 15)
                                .map((skill, index) => (
                                    <SkillBadge key={index} name={skill.name} size="md" className="cursor-pointer" onClick={() => navigate(`/skills/${skill.name.toLowerCase().replace(/\s+/g, '-')}`)} />
                                ))}
                        </div>
                    </div>
                </GlassCard>
            )}
        </div>
    );
};

export default CompanyDetail;
