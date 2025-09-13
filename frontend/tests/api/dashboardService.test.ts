/**
 * Dashboard Service Tests
 * Tests for dashboard API endpoints
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { getDashboardStats, getTrendingSkills } from '../../src/services/dashboardService';
import type { DashboardStats, TrendingSkill } from '../../src/types';

describe('Dashboard Service', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(axios);
  });

  afterEach(() => {
    mock.reset();
  });

  describe('getDashboardStats', () => {
    it('should fetch dashboard statistics', async () => {
      const mockStats: DashboardStats = {
        total_jobs: 5234,
        active_jobs: 4521,
        total_companies: 342,
        total_skills: 128,
        avg_salary: 95000,
        last_updated: '2025-01-15T10:30:00Z',
      };

      mock.onGet('/api/v1/analytics/dashboard').reply(200, mockStats);

      const result = await getDashboardStats();
      expect(result).toEqual(mockStats);
      expect(result.total_jobs).toBe(5234);
      expect(result.total_companies).toBe(342);
    });

    it('should handle missing optional fields', async () => {
      const mockStats = {
        total_jobs: 5234,
        active_jobs: 4521,
        total_companies: 342,
        total_skills: 128,
        last_updated: '2025-01-15T10:30:00Z',
        // avg_salary is optional
      };

      mock.onGet('/api/v1/analytics/dashboard').reply(200, mockStats);

      const result = await getDashboardStats();
      expect(result.avg_salary).toBeUndefined();
    });

    it('should handle errors', async () => {
      mock.onGet('/api/v1/analytics/dashboard').reply(500, {
        message: 'Database connection failed',
      });

      await expect(getDashboardStats()).rejects.toThrow();
    });
  });

  describe('getTrendingSkills', () => {
    it('should fetch trending skills with default parameters', async () => {
      const mockSkills: TrendingSkill[] = [
        {
          skill_id: 1,
          name: 'React',
          category: 'web_frameworks',
          job_count: 456,
          growth_rate: 23.5,
          avg_salary: 98000,
        },
        {
          skill_id: 2,
          name: 'Python',
          category: 'programming_languages',
          job_count: 523,
          growth_rate: 15.2,
          avg_salary: 102000,
        },
      ];

      mock.onGet('/api/v1/analytics/trending-skills').reply((config) => {
        expect(config.params).toEqual({ limit: 8, days: 30 });
        return [200, mockSkills];
      });

      const result = await getTrendingSkills();
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('React');
      expect(result[1].name).toBe('Python');
    });

    it('should fetch trending skills with custom parameters', async () => {
      mock.onGet('/api/v1/analytics/trending-skills').reply((config) => {
        expect(config.params).toEqual({ limit: 5, days: 60 });
        return [200, []];
      });

      await getTrendingSkills(5, 60);
    });

    it('should handle empty results', async () => {
      mock.onGet('/api/v1/analytics/trending-skills').reply(200, []);

      const result = await getTrendingSkills();
      expect(result).toEqual([]);
    });
  });
});

