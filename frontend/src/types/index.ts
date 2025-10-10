/**
 * TypeScript type definitions for NZ Tech Jobs Market Intelligence Platform
 * Aligned with backend schemas (app/schemas.py)
 */

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

export interface APIResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error_code?: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// =============================================================================
// ENUM TYPES
// =============================================================================

export const EmploymentType = {
  PERMANENT: 'permanent',
  CONTRACT: 'contract',
  CASUAL: 'casual',
  PART_TIME: 'part_time',
  INTERNSHIP: 'internship'
} as const;

export type EmploymentType = typeof EmploymentType[keyof typeof EmploymentType];

export const ExperienceLevel = {
  ENTRY: 'entry',
  JUNIOR: 'junior',
  MID: 'mid',
  SENIOR: 'senior',
  LEAD: 'lead',
  PRINCIPAL: 'principal'
} as const;

export type ExperienceLevel = typeof ExperienceLevel[keyof typeof ExperienceLevel];

export const SkillCategory = {
  PROGRAMMING_LANGUAGES: 'programming_languages',
  WEB_FRAMEWORKS: 'web_frameworks',
  DATABASES: 'databases',
  CLOUD_PLATFORMS: 'cloud_platforms',
  DEVOPS: 'devops',
  AI_ML: 'ai_ml',
  MOBILE: 'mobile',
  OTHER: 'other'
} as const;

export type SkillCategory = typeof SkillCategory[keyof typeof SkillCategory];

export const WorkArrangement = {
  ONSITE: 'onsite',
  HYBRID: 'hybrid',
  REMOTE: 'remote'
} as const;

export type WorkArrangement = typeof WorkArrangement[keyof typeof WorkArrangement];

// =============================================================================
// CORE ENTITY TYPES
// =============================================================================

export interface Company {
  id: number;
  name: string;
  normalized_name: string;
  created_at: string;
}

export interface CompanyWithStats extends Company {
  active_jobs_count: number;
  total_jobs_count: number;
  tech_stack?: TechStackItem[];
  job_count?: number;
}

export interface Location {
  id: number;
  city: string;
  region?: string;
  country: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
  created_at: string;
}

export interface LocationWithStats extends Location {
  active_jobs_count: number;
  total_jobs_count: number;
  avg_salary?: number;
  top_companies?: Array<{ id: number; name: string; job_count: number }>;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  color_code?: string;
  sort_order: number;
  created_at: string;
}

export interface Skill {
  id: number;
  name: string;
  display_name?: string;  // Properly formatted name (e.g., "R", "JavaScript", "REST API")
  category?: SkillCategory;
  aliases?: string;
  description?: string;
  skill_type: string;
  popularity_score: number;
  created_at?: string;
  updated_at?: string;
}

export interface SkillWithStats extends Skill {
  job_count: number;
  required_count: number;
  primary_count: number;
  avg_salary?: number;
  trend_percentage?: number;
  growth_rate?: number;
  percentage?: number;  // Percentage of total jobs
  category_percentage?: number;  // Percentage within category
  rank?: number;  // Ranking position
}

export interface Job {
  id: number;
  title: string;
  description?: string;
  requirements?: string;
  salary_min?: number;
  salary_max?: number;
  currency: string;
  employment_type?: EmploymentType;
  experience_level?: ExperienceLevel;
  work_arrangement?: WorkArrangement;
  source_url?: string;
  source_id?: string;
  posted_date?: string;
  closing_date?: string;
  is_active: boolean;
  company_id?: number;
  location_id?: number;
  category_id?: number;
  scraped_at: string;
  created_at?: string;
  updated_at?: string;
  is_tech_job?: boolean;
  extracted_skills?: Record<string, string[]>;
}

export interface JobDetail extends Job {
  company?: Company;
  location?: Location;
  category?: Category;
  skills?: Skill[];
}

// =============================================================================
// ANALYTICS TYPES
// =============================================================================

export interface DashboardStats {
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

export interface TrendingSkill {
  skill_id: number;
  name: string;
  display_name?: string;  // Properly formatted name
  category?: SkillCategory;
  job_count: number;
  growth_percentage?: number;
  avg_salary?: number;
  trend_direction?: 'up' | 'down' | 'stable';
  percentage?: number;  // Percentage of total jobs
}

export interface PopularCompany {
  company_id: number;
  name: string;
  active_jobs: number;
  new_jobs_this_week: number;
}

export interface SkillTrend {
  id: number;
  skill_id: number;
  date_recorded: string;
  job_count: number;
  new_jobs_count: number;
  avg_salary?: number;
  demand_score?: number;
  growth_percentage?: number;
}

export interface SalaryTrend {
  id: number;
  category_id: number;
  location_id: number;
  experience_level?: ExperienceLevel;
  date_recorded: string;
  avg_salary?: number;
  median_salary?: number;
  min_salary?: number;
  max_salary?: number;
  sample_size?: number;
}

export interface SkillCategoryStats {
  category: SkillCategory;
  total_jobs: number;
  skills: SkillWithStats[];
  growth_rate?: number;
}

export interface TechStackItem {
  name: string;
  category: SkillCategory;
  count: number;
  confidence: 'high' | 'medium' | 'low';
}

export interface CompanyTechStack {
  company_id: number;
  company_name: string;
  job_count: number;
  last_updated: string;
  tech_stack: {
    programming_languages?: TechStackItem[];
    web_frameworks?: TechStackItem[];
    databases?: TechStackItem[];
    cloud_platforms?: TechStackItem[];
    devops?: TechStackItem[];
    ai_ml?: TechStackItem[];
    mobile?: TechStackItem[];
    other?: TechStackItem[];
  };
}

export interface SkillDetail {
  id: number;
  name: string;
  category: string;
  current_demand: {
    job_count: number;
    percentage: number;
    rank: number;
  };
  growth_rate: number;
  trend_data: Array<{
    date: string;
    count: number;
  }>;
  top_companies: Array<{
    name: string;
    job_count: number;
  }>;
  related_skills: Array<{
    skill: string;
    co_occurrence_percentage: number;
    job_count: number;
  }>;
  experience_distribution?: Record<ExperienceLevel, number>;
  location_breakdown: Array<{
    city: string;
    count: number;
  }>;
}

export interface SkillComparison {
  skill: string;
  demand: number;
  growth_rate: number;
  companies_using: number;
  percentage: number;
  trend_data: Array<{
    date: string;
    count: number;
  }>;
}

export interface SkillPair {
  skill1: string;
  skill2: string;
  job_count: number;
  percentage: number;
  strength: 'high' | 'medium' | 'low';
}

// =============================================================================
// TRACKED KEYWORDS AND SKILLS TAXONOMY TYPES
// =============================================================================

export interface TrackedSkill {
  name: string;
  display_name: string;
}

export interface SkillTaxonomyCategory {
  display_name: string;
  skills: TrackedSkill[];
}

export interface TrackedKeywordsData {
  search_terms: string[];
  skills_taxonomy: Record<string, SkillTaxonomyCategory>;
  total_search_terms: number;
  total_skill_categories: number;
  total_skills: number;
}

// =============================================================================
// SEARCH AND FILTER TYPES
// =============================================================================

export interface JobSearchParams {
  query?: string;
  company_id?: number;
  location_id?: number;
  category_id?: number;
  skills?: string[];
  exclude_skills?: string[];
  companies?: string[];
  exclude_companies?: string[];
  employment_type?: EmploymentType;
  experience_level?: ExperienceLevel;
  salary_min?: number;
  salary_max?: number;
  location?: string;
  remote_type?: WorkArrangement;
  posted_after?: string;
  is_active?: boolean;
  offset?: number;
  limit?: number;
}

export interface SkillSearchParams {
  query?: string;
  category?: SkillCategory;
  skill_type?: string;
  min_job_count?: number;
  offset?: number;
  limit?: number;
}

export interface CompanySearchParams {
  search?: string;
  page?: number;
  limit?: number;
  sort_by?: 'name' | 'active_jobs' | 'total_jobs';
}

export interface RegionalSearchParams {
  search?: string;
  page?: number;
  limit?: number;
  time_period?: number;
  skills?: string[];
}

// =============================================================================
// CHART DATA TYPES
// =============================================================================

export interface ChartData {
  name: string;
  value: number;
  color?: string;
  percentage?: number;
  category?: string;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  category?: string;
}

export interface BarChartData {
  label: string;
  value: number;
  color?: string;
  metadata?: Record<string, any>;
}

// =============================================================================
// UI STATE TYPES
// =============================================================================

export interface FilterState {
  timeRange: 30 | 90 | 180 | 365 | 0; // 0 means all time
  category?: SkillCategory;
  location?: string;
  experienceLevel?: ExperienceLevel;
}

export interface SortOption {
  field: string;
  direction: 'asc' | 'desc';
  label: string;
}

// =============================================================================
// LOCATION ANALYTICS
// =============================================================================

export interface LocationStats {
  location: Location;
  job_count: number;
  company_count: number;
  avg_salary?: number;
  top_skills: string[];
  growth_rate?: number;
}
