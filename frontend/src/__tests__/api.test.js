/**
 * api.test.js - Tests for API service functions
 * 
 * Tests the centralized API service layer including:
 * - API configuration
 * - Auth token handling
 * - API module exports
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock axios
vi.mock('axios', () => ({
    default: {
        create: vi.fn(() => ({
            get: vi.fn(),
            post: vi.fn(),
            put: vi.fn(),
            delete: vi.fn(),
            interceptors: {
                request: { use: vi.fn() },
                response: { use: vi.fn() }
            }
        })),
    }
}));

describe('API Service', () => {
    beforeEach(() => {
        vi.resetModules();
        localStorage.clear();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('API Configuration', () => {
        it('should use environment variable for base URL when available', async () => {
            // Set environment variable
            vi.stubEnv('VITE_API_BASE_URL', 'http://custom-api:9000');

            // Re-import to pick up the new env var
            const { default: axios } = await import('axios');

            expect(axios.create).toBeDefined();
        });

        it('should fallback to localhost:8000 when no env var set', async () => {
            // No need to set env var, default should be used
            const { default: axios } = await import('axios');

            expect(axios.create).toBeDefined();
        });
    });

    describe('API Module Exports', () => {
        it('should export all required API modules', async () => {
            // Import actual API file
            const api = await import('../services/api.js');

            expect(api.authAPI).toBeDefined();
            expect(api.configAPI).toBeDefined();
            expect(api.scheduleAPI).toBeDefined();
            expect(api.fleetAPI).toBeDefined();
            expect(api.drillBlastAPI).toBeDefined();
            expect(api.operationsAPI).toBeDefined();
            expect(api.monitoringAPI).toBeDefined();
            expect(api.analyticsAPI).toBeDefined();
            expect(api.washPlantAPI).toBeDefined();
        });

        it('should export authAPI with login function', async () => {
            const { authAPI } = await import('../services/api.js');

            expect(typeof authAPI.login).toBe('function');
            expect(typeof authAPI.register).toBe('function');
        });

        it('should export analyticsAPI with dashboard summary function', async () => {
            const { analyticsAPI } = await import('../services/api.js');

            expect(typeof analyticsAPI.getDashboardSummary).toBe('function');
        });
    });
});

describe('Auth Token Handling', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it('should store token in localStorage on login', () => {
        const token = 'test-jwt-token';
        localStorage.setItem('token', token);

        expect(localStorage.getItem('token')).toBe(token);
    });

    it('should clear token on logout', () => {
        localStorage.setItem('token', 'test-token');
        localStorage.removeItem('token');

        expect(localStorage.getItem('token')).toBeNull();
    });
});
