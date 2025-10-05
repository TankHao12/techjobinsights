/**
 * Tracked Keywords Service
 * API service for fetching tracked search terms and skills taxonomy
 */

import { api } from './api';
import type { TrackedKeywordsData } from '../types';

/**
 * Get all tracked keywords (search terms and skills taxonomy)
 * 
 * @returns Tracked keywords data including search terms and skills taxonomy
 */
export const getTrackedKeywords = async (): Promise<TrackedKeywordsData> => {
  return api.get<TrackedKeywordsData>('/analytics/tracked-keywords');
};
