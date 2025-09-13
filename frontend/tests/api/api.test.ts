/**
 * API Service Tests
 * Tests for the core API client functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { api, buildQueryString, isApiError, getErrorMessage } from '../../src/services/api';

describe('API Service', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(axios);
  });

  afterEach(() => {
    mock.reset();
  });

  describe('GET requests', () => {
    it('should successfully fetch data', async () => {
      const testData = { message: 'success', data: [1, 2, 3] };
      mock.onGet('/api/v1/test').reply(200, testData);

      const result = await api.get('/test');
      expect(result).toEqual(testData);
    });

    it('should handle query parameters', async () => {
      mock.onGet('/api/v1/test').reply((config) => {
        expect(config.params).toEqual({ page: 1, limit: 10 });
        return [200, { success: true }];
      });

      await api.get('/test', { page: 1, limit: 10 });
    });

    it('should handle 404 errors', async () => {
      mock.onGet('/api/v1/not-found').reply(404, {
        message: 'Not found',
      });

      await expect(api.get('/not-found')).rejects.toThrow();
    });

    it('should handle 500 errors', async () => {
      mock.onGet('/api/v1/error').reply(500, {
        message: 'Internal server error',
      });

      await expect(api.get('/error')).rejects.toThrow();
    });
  });

  describe('Paginated requests', () => {
    it('should fetch paginated data', async () => {
      const testData = {
        items: [{ id: 1 }, { id: 2 }],
        total: 100,
        page: 1,
        page_size: 10,
        pages: 10,
      };

      mock.onGet('/api/v1/jobs').reply(200, testData);

      const result = await api.getPaginated('/jobs', { page: 1, limit: 10 });
      expect(result).toEqual(testData);
      expect(result.items).toHaveLength(2);
      expect(result.total).toBe(100);
    });
  });

  describe('buildQueryString', () => {
    it('should build query string from object', () => {
      const params = { page: 1, limit: 10, search: 'test' };
      const result = buildQueryString(params);
      expect(result).toBe('page=1&limit=10&search=test');
    });

    it('should skip null and undefined values', () => {
      const params = { page: 1, limit: null, search: undefined };
      const result = buildQueryString(params);
      expect(result).toBe('page=1');
    });

    it('should handle empty object', () => {
      const result = buildQueryString({});
      expect(result).toBe('');
    });

    it('should encode special characters', () => {
      const params = { query: 'React & Angular' };
      const result = buildQueryString(params);
      expect(result).toContain('React%20%26%20Angular');
    });
  });

  describe('Error handling utilities', () => {
    it('should identify API errors', () => {
      const apiError = {
        isAxiosError: true,
        response: { status: 404, data: { message: 'Not found' } },
      };
      expect(isApiError(apiError)).toBe(true);

      const regularError = new Error('Regular error');
      expect(isApiError(regularError)).toBe(false);
    });

    it('should extract error messages', () => {
      const apiError = {
        isAxiosError: true,
        response: { data: { message: 'Custom error message' } },
      };
      expect(getErrorMessage(apiError)).toBe('Custom error message');

      const regularError = new Error('Regular error');
      expect(getErrorMessage(regularError)).toBe('Regular error');

      const unknownError = { weird: 'object' };
      expect(getErrorMessage(unknownError)).toBe('An unexpected error occurred');
    });
  });
});

