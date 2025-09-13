/**
 * Test setup file for Vitest
 * Configures testing environment and global test utilities
 */

import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Cleanup after each test case
afterEach(() => {
  cleanup();
});

// Extend Vitest matchers
expect.extend({});

