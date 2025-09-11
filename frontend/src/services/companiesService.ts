/**
 * Companies API Service
 * Endpoints for company information and tech stacks
 */

import { api } from './api';
import type {
  CompanyWithStats,
  CompanyTechStack,
  PaginatedResponse,
  CompanySearchParams,
} from '../types';

/**
 * Get companies with statistics
 * 
 * @param params Search and pagination parameters
 * @returns Paginated list of companies
 */
export const getCompanies = async (
  params: CompanySearchParams = {}
): Promise<PaginatedResponse<CompanyWithStats>> => {
  return api.getPaginated<CompanyWithStats>('/companies/with-stats', params);
};

/**
 * Get popular companies (autocomplete/suggestions)
 * 
 * @param limit Number of companies to return (default: 10)
 * @returns Array of popular companies
 */
export const getPopularCompaniesAutocomplete = async (limit: number = 10): Promise<CompanyWithStats[]> => {
  return api.get<CompanyWithStats[]>('/companies/popular', { limit });
};

/**
 * Get company tech stack
 * 
 * @param companyId Company ID
 * @returns Company tech stack details
 */
export const getCompanyTechStack = async (companyId: number): Promise<CompanyTechStack> => {
  return api.get<CompanyTechStack>(`/companies/${companyId}/tech-stack`);
};

/**
 * Find companies using a specific technology
 * 
 * @param tech Technology name
 * @param limit Results limit (default: 20)
 * @returns Array of companies using the technology
 */
export const getCompaniesByTech = async (
  tech: string,
  limit: number = 20
): Promise<Array<{ id: number; name: string; job_count: number }>> => {
  return api.get(`/companies/by-tech`, { tech, limit });
};

/**
 * Search companies by name
 * 
 * @param search Search query
 * @param limit Results limit (default: 10)
 * @returns Array of matching companies
 */
export const searchCompanies = async (
  search: string,
  limit: number = 10
): Promise<CompanyWithStats[]> => {
  return api.get<CompanyWithStats[]>('/companies', { search, limit });
};


