/**
 * Regions API Service
 * Endpoints for regional insights and statistics
 */

import { api } from './api';
import type {
  LocationWithStats,
  PaginatedResponse,
  RegionalSearchParams,
  JobDetail,
} from '../types';

/**
 * Get regions with statistics
 * 
 * @param params Search and filter parameters
 * @returns Paginated list of regions
 */
export const getRegions = async (
  params: RegionalSearchParams = {}
): Promise<PaginatedResponse<LocationWithStats>> => {
  return api.getPaginated<LocationWithStats>('/regions/with-stats', params);
};

/**
 * Get region details by ID
 * 
 * @param regionId Region ID
 * @param timePeriod Optional time period in days
 * @param skills Optional list of skills to filter by
 * @returns Region details with statistics
 */
export const getRegionDetails = async (
  regionId: number,
  timePeriod?: number,
  skills?: string[]
): Promise<LocationWithStats> => {
  const params: Record<string, any> = {};
  if (timePeriod !== undefined) {
    params.time_period = timePeriod;
  }
  if (skills && skills.length > 0) {
    params.skills = skills;
  }
  return api.get<LocationWithStats>(`/regions/${regionId}`, params);
};

/**
 * Get top companies hiring in a region
 * 
 * @param regionId Region ID
 * @param limit Number of companies to return (default: 10)
 * @param timePeriod Optional time period in days
 * @param skills Optional list of skills to filter by
 * @returns Companies hiring in the region
 */
export const getRegionCompanies = async (
  regionId: number,
  limit: number = 10,
  timePeriod?: number,
  skills?: string[]
): Promise<{
  region_id: number;
  region_name: string;
  companies: Array<{ id: number; name: string; job_count: number }>;
}> => {
  const params: Record<string, any> = { limit };
  if (timePeriod !== undefined) {
    params.time_period = timePeriod;
  }
  if (skills && skills.length > 0) {
    params.skills = skills;
  }
  return api.get(`/regions/${regionId}/companies`, params);
};

/**
 * Get jobs in a specific region
 * 
 * @param regionId Region ID
 * @param page Page number (1-indexed)
 * @param limit Results per page
 * @param timePeriod Optional time period in days
 * @param skills Optional list of skills to filter by
 * @param isActive Only active jobs (default: true)
 * @returns Paginated list of jobs
 */
export const getRegionJobs = async (
  regionId: number,
  page: number = 1,
  limit: number = 20,
  timePeriod?: number,
  skills?: string[],
  isActive: boolean = true
): Promise<PaginatedResponse<JobDetail>> => {
  const params: Record<string, any> = { page, limit, is_active: isActive };
  if (timePeriod !== undefined) {
    params.time_period = timePeriod;
  }
  if (skills && skills.length > 0) {
    params.skills = skills;
  }
  return api.getPaginated<JobDetail>(`/regions/${regionId}/jobs`, params);
};

