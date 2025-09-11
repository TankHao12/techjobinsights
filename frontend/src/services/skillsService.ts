/**
 * Skills API Service
 * Endpoints for skills analytics and comparison
 */

import { api } from './api';
import type {
  SkillWithStats,
  SkillCategoryStats,
  SkillDetail,
  SkillComparison,
  SkillPair,
  SkillCategory,
} from '../types';

/**
 * Get popular skills
 * 
 * @param limit Number of skills to return (default: 20)
 * @param days Time period in days
 * @param category Optional skill category filter
 * @returns Array of popular skills with stats
 */
export const getPopularSkills = async (
  limit: number = 20,
  _days?: number,
  category?: SkillCategory
): Promise<SkillWithStats[]> => {
  const data = await api.get<any[]>('/analytics/skills/popular', {
    limit,
    category,
  });

  // Transform backend response to frontend format
  return data.map((item, index) => ({
    id: index + 1,
    name: item.display_name || item.name,  // Use display_name for display
    display_name: item.display_name,  // Add display_name field
    category: item.category || 'other',  // Use category from API
    job_count: item.job_count,
    required_count: item.job_count,
    primary_count: item.job_count,
    percentage: item.percentage,
    skill_type: 'technical',
    popularity_score: item.percentage,
    growth_rate: undefined, // TODO: Add growth rate calculation
  }));
};

/**
 * Get skills grouped by category
 * 
 * @param days Time period in days (default: 90)
 * @returns Array of skill categories with their skills
 */
export const getSkillsByCategory = async (_days: number = 90): Promise<SkillCategoryStats[]> => {
  const data = await api.get<Record<string, any[]>>('/analytics/skills/by-category');

  // Transform backend response to frontend format
  return Object.entries(data).map(([category, skills]) => ({
    category: category as SkillCategory,
    display_name: category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    total_jobs: skills.reduce((sum, skill) => sum + skill.job_count, 0),
    skill_count: skills.length,
    growth_rate: 0, // TODO: Calculate growth rate
    skills: skills.map((skill, index) => ({
      id: index + 1,
      name: skill.display_name || skill.name,  // Use display_name for display
      display_name: skill.display_name,  // Add display_name field
      category: category as SkillCategory,
      job_count: skill.job_count,
      required_count: skill.job_count,
      primary_count: skill.job_count,
      percentage: skill.percentage,
      skill_type: 'technical',
      popularity_score: skill.percentage,
    })),
  }));
};

/**
 * Get available skill categories
 * 
 * @returns Array of skill category enum values
 */
export const getSkillCategories = async (): Promise<SkillCategory[]> => {
  return api.get<SkillCategory[]>('/analytics/skills/categories');
};

/**
 * Get detailed information for a specific skill
 * 
 * @param skillName Skill name (lowercase, hyphenated for URL)
 * @returns Detailed skill information
 */
export const getSkillDetail = async (skillName: string): Promise<SkillDetail> => {
  const data = await api.get<any>(`/skills/${encodeURIComponent(skillName)}`);

  // Transform backend response to frontend format
  return {
    id: 1, // TODO: Add ID to backend response
    name: data.name,
    category: data.category,
    current_demand: {
      job_count: data.current_demand.job_count,
      percentage: data.current_demand.percentage,
      rank: data.current_demand.rank,
    },
    growth_rate: data.growth_rate,
    trend_data: data.trend_data,
    top_companies: data.top_companies,
    related_skills: data.related_skills,
    experience_distribution: data.experience_distribution,
    location_breakdown: data.location_breakdown,
  };
};

/**
 * Compare multiple skills side-by-side
 * 
 * @param skills Array of skill names to compare (2-3 skills)
 * @returns Array of skill comparison data
 */
export const compareSkills = async (skills: string[]): Promise<SkillComparison[]> => {
  const skillsParam = skills.join(',');
  return api.get<SkillComparison[]>('/skills/compare', { skills: skillsParam });
};

/**
 * Get common skill pairs
 * 
 * @param limit Number of pairs to return (default: 15)
 * @returns Array of skill pairs with co-occurrence data
 */
export const getSkillPairs = async (limit: number = 15): Promise<SkillPair[]> => {
  return api.get<SkillPair[]>('/skills/pairs', { limit });
};

/**
 * Search skills
 * 
 * @param query Search query
 * @param category Optional category filter
 * @param limit Results limit
 * @returns Array of matching skills
 */
export const searchSkills = async (
  query: string,
  category?: SkillCategory,
  limit: number = 20
): Promise<SkillWithStats[]> => {
  return api.get<SkillWithStats[]>('/skills/search', {
    query,
    category,
    limit,
  });
};


