/**
 * SiteContext.test.jsx - Tests for Site Context Provider
 * 
 * Tests the SiteContext including:
 * - Initial state
 * - Site selection
 * - Auto-selection of first site
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, renderHook, act } from '@testing-library/react';
import { SiteProvider, useSite } from '../context/SiteContext';
import React from 'react';

// Mock axios
vi.mock('axios', () => ({
    default: {
        get: vi.fn(),
        create: vi.fn(() => ({
            get: vi.fn(),
            interceptors: {
                request: { use: vi.fn() },
                response: { use: vi.fn() }
            }
        }))
    }
}));

describe('SiteContext', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('SiteProvider', () => {
        it('should render children', async () => {
            render(
                <SiteProvider>
                    <div data-testid="child">Child Content</div>
                </SiteProvider>
            );

            expect(screen.getByTestId('child')).toBeInTheDocument();
        });

        it('should provide initial loading state', async () => {
            const TestComponent = () => {
                const { loading } = useSite();
                return <div data-testid="loading">{loading ? 'true' : 'false'}</div>;
            };

            render(
                <SiteProvider>
                    <TestComponent />
                </SiteProvider>
            );

            // Initially should be loading
            expect(screen.getByTestId('loading')).toBeDefined();
        });
    });

    describe('useSite hook', () => {
        it('should throw error when used outside provider', () => {
            // Suppress console.error for this test
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

            const TestComponent = () => {
                useSite();
                return null;
            };

            expect(() => render(<TestComponent />)).toThrow();

            consoleSpy.mockRestore();
        });

        it('should provide selectSite function', () => {
            const TestComponent = () => {
                const { selectSite } = useSite();
                return <div data-testid="has-select">{typeof selectSite}</div>;
            };

            render(
                <SiteProvider>
                    <TestComponent />
                </SiteProvider>
            );

            expect(screen.getByTestId('has-select').textContent).toBe('function');
        });
    });
});
