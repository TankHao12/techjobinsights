/**
 * Skill Detail Page
 * Displays comprehensive information about a specific skill
 * US-2.2: Individual Skill Detail Page
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, TrendingUp, TrendingDown, Minus, Building2, Target, Share2, Plus } from 'lucide-react';
import { getSkillDetail } from '../services/skillsService';
import { LoadingSpinner } from '../components/common';
import { GlassCard } from '../components/common/GlassCard';
import SkillBadge from '../components/common/SkillBadge';
// import SimpleLineChart from '../components/charts/SimpleLineChart';

const SkillDetail: React.FC = () => {
    const { skillName } = useParams<{ skillName: string }>();
    const navigate = useNavigate();

    const { data, isLoading, error } = useQuery({
        queryKey: ['skill', skillName],
        queryFn: () => getSkillDetail(skillName!),
        enabled: !!skillName,
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <LoadingSpinner size="lg" text="Loading skill details..." />
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="text-center py-12">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Skill Not Found</h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">The skill you're looking for doesn't exist.</p>
                <button onClick={() => navigate('/skills')} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Back to Skills
                </button>
            </div>
        );
    }

    const handleShare = () => {
        if (navigator.share) {
            navigator.share({
                title: `${data.name} - Skill Analytics`,
                text: `Explore ${data.name} job market demand and trends in New Zealand`,
                url: window.location.href,
            });
        } else {
            navigator.clipboard.writeText(window.location.href);
            // TODO: Add toast notification
        }
    };

    const handleAddToComparison = () => {
        // TODO: Implement add to comparison functionality
        navigate('/skills/compare');
    };

    const getGrowthIndicator = (rate: number) => {
        if (rate > 5) return { icon: TrendingUp, color: 'text-green-600 dark:text-green-400' };
        if (rate < -5) return { icon: TrendingDown, color: 'text-red-600 dark:text-red-400' };
        return { icon: Minus, color: 'text-gray-500' };
    };

    const growth = getGrowthIndicator(data.growth_rate);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 capitalize">{data.name}</h1>
                            <SkillBadge name={data.category.replace(/_/g, ' ')} category={data.category} size="sm" />
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                            <span>Rank #{data.current_demand.rank} in demand</span>
                            <span>•</span>
                            <span>{data.current_demand.percentage}% of tech jobs</span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-3">
                    <button onClick={handleAddToComparison} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                        <Plus className="w-4 h-4" />
                        Compare
                    </button>
                    <button onClick={handleShare} className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
                        <Share2 className="w-4 h-4" />
                        Share
                    </button>
                </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <GlassCard>
                    <div className="p-6 text-center">
                        <Target className="w-8 h-8 mx-auto mb-3 text-blue-600" />
                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{data.current_demand.job_count}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Current Job Openings</div>
                    </div>
                </GlassCard>

                <GlassCard>
                    <div className="p-6 text-center">
                        <growth.icon className={`w-8 h-8 mx-auto mb-3 ${growth.color}`} />
                        <div className={`text-2xl font-bold mb-1 ${growth.color}`}>
                            {data.growth_rate > 0 ? '+' : ''}
                            {data.growth_rate.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">30-Day Growth</div>
                    </div>
                </GlassCard>

                <GlassCard>
                    <div className="p-6 text-center">
                        <Building2 className="w-8 h-8 mx-auto mb-3 text-green-600" />
                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{data.top_companies.length}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Companies Hiring</div>
                    </div>
                </GlassCard>
            </div>

            {/* Trend Chart */}
            {/* <GlassCard>
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            90-Day Demand Trend
          </h2>
          <div className="h-64">
            <SimpleLineChart
              data={data.trend_data.map(item => ({
                date: new Date(item.date).toLocaleDateString('en-NZ', {
                  month: 'short',
                  day: 'numeric'
                }),
                demand: item.count,
              }))}
              lines={[{
                dataKey: 'demand',
                name: 'Job Demand',
                color: '#3B82F6'
              }]}
              height={240}
              showLegend={false}
            />
          </div>
        </div>
      </GlassCard> */}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Companies  */}
                <GlassCard>
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Top Companies Using {data.name}</h2>
                        <div className="space-y-3">
                            {data.top_companies.slice(0, 8).map((company, index) => (
                                <div key={company.name} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors" onClick={() => navigate(`/companies/${encodeURIComponent(company.name.toLowerCase())}`)}>
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm font-medium text-gray-400 w-6">{index + 1}</span>
                                        <span className="font-medium text-gray-900 dark:text-gray-100">{company.name}</span>
                                    </div>
                                    <span className="text-sm text-gray-600 dark:text-gray-400">{company.job_count} jobs</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </GlassCard>

                {/* Related Skills */}
                <GlassCard>
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Skills Often Paired With {data.name}</h2>
                        <div className="space-y-3">
                            {data.related_skills.slice(0, 5).map((skill, index) => (
                                <div key={skill.skill} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors" onClick={() => navigate(`/skills/${skill.skill.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '')}`)}>
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm font-medium text-gray-400 w-6">{index + 1}</span>
                                        <span className="font-medium text-gray-900 dark:text-gray-100 capitalize">{skill.skill}</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{skill.co_occurrence_percentage.toFixed(1)}%</div>
                                        <div className="text-xs text-gray-500">{skill.job_count} jobs</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">Percentage shows how often this skill appears with {data.name}</div>
                    </div>
                </GlassCard>
            </div>

            {/* Navigation */}
            {/* <GlassCard>
                <div className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Explore More</h3>
                    <div className="flex flex-wrap gap-3">
                        <button onClick={() => navigate('/skills')} className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors">
                            Browse All Skills
                        </button>
                        <button onClick={() => navigate(`/skills?category=${data.category}`)} className="px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors">
                            More {data.category.replace(/_/g, ' ')} Skills
                        </button>
                        <button onClick={() => navigate('/skills/compare')} className="px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors">
                            Compare Skills
                        </button>
                    </div>
                </div>
            </GlassCard> */}
        </div>
    );
};

export default SkillDetail;
