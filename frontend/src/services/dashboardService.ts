/**
 * Dashboard API Service
 * Endpoints for dashboard statistics and overview data
 */

import { api } from './api';
import type {
  DashboardStats,
  TrendingSkill,
  PopularCompany,
  Job,
} from '../types';

export interface DashboardResponse {
  total_jobs: number;
  active_jobs: number;
  total_companies: number;
  hiring_companies: number;
  total_skills: number;
  new_jobs_today: number;
  avg_salary?: number;
  jobs_with_salary: number;
  last_updated: string;
}

export interface RecentJob {
  id: number;
  title: string;
  company_name: string;
  location?: string;
  posted_date: string;
  salary_min?: number;
  salary_max?: number;
}

/**
 * Get dashboard statistics
 * 
 * @param days Number of days to include (default: 90)
 * @returns Dashboard statistics
 */
export const getDashboardStats = async (days: number = 90): Promise<DashboardStats> => {
  return api.get<DashboardStats>('/analytics/dashboard', { days });
};

/**
 * Get trending skills
 * 
 * @param limit Number of skills to return (default: 8)
 * @param days Time period in days (default: 30)
 * @returns Array of trending skills
 */
export const getTrendingSkills = async (
  limit: number = 8,
  days: number = 30
): Promise<TrendingSkill[]> => {
  return api.get<TrendingSkill[]>('/analytics/trending-skills', { limit, days });
};

/**
 * Get recent jobs
 * 
 * @param limit Number of jobs to return (default: 10)
 * @returns Array of recent jobs
 */
export const getRecentJobs = async (limit: number = 10): Promise<Job[]> => {
  return api.get<Job[]>('/jobs', { limit, is_active: true, sort_by: 'posted_date', sort_order: 'desc' });
};

/**
 * Get popular companies (top hiring)
 * 
 * @param limit Number of companies to return (default: 10)
 * @returns Array of popular companies
 */
export const getPopularCompanies = async (limit: number = 10): Promise<PopularCompany[]> => {
  return api.get<PopularCompany[]>('/analytics/popular-companies', { limit });
};


