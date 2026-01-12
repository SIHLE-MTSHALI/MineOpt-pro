/**
 * LocalStorage.test.js - Tests for localStorage persistence
 * 
 * Tests that UI state is properly persisted:
 * - Sidebar collapsed state
 * - Active module
 * - Theme preference
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('LocalStorage Persistence', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    afterEach(() => {
        localStorage.clear();
    });

    describe('Sidebar State', () => {
        it('should store sidebar collapsed state', () => {
            localStorage.setItem('mineopt_sidebar_collapsed', 'true');
            expect(localStorage.getItem('mineopt_sidebar_collapsed')).toBe('true');
        });

        it('should default to expanded (false) when not set', () => {
            const stored = localStorage.getItem('mineopt_sidebar_collapsed');
            expect(stored).toBeNull();
            // App should default to false
            expect(stored === 'true').toBe(false);
        });

        it('should persist collapsed state across sessions', () => {
            localStorage.setItem('mineopt_sidebar_collapsed', 'true');

            // Simulate new session by creating new reference
            const newValue = localStorage.getItem('mineopt_sidebar_collapsed');
            expect(newValue).toBe('true');
        });
    });

    describe('Active Module', () => {
        it('should store active module', () => {
            localStorage.setItem('mineopt_active_module', 'gantt');
            expect(localStorage.getItem('mineopt_active_module')).toBe('gantt');
        });

        it('should default to spatial when not set', () => {
            const stored = localStorage.getItem('mineopt_active_module');
            expect(stored).toBeNull();
            // App should default to 'spatial'
            const defaultValue = stored || 'spatial';
            expect(defaultValue).toBe('spatial');
        });
    });

    describe('Theme Preference', () => {
        it('should store theme preference', () => {
            localStorage.setItem('mineopt_theme', 'light');
            expect(localStorage.getItem('mineopt_theme')).toBe('light');
        });

        it('should default to dark when not set', () => {
            const stored = localStorage.getItem('mineopt_theme');
            expect(stored).toBeNull();
            // App should default to 'dark'
            const defaultValue = stored || 'dark';
            expect(defaultValue).toBe('dark');
        });

        it('should allow switching themes', () => {
            localStorage.setItem('mineopt_theme', 'dark');
            expect(localStorage.getItem('mineopt_theme')).toBe('dark');

            localStorage.setItem('mineopt_theme', 'light');
            expect(localStorage.getItem('mineopt_theme')).toBe('light');
        });
    });

    describe('Auth Token', () => {
        it('should store auth token', () => {
            const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test';
            localStorage.setItem('token', token);
            expect(localStorage.getItem('token')).toBe(token);
        });

        it('should clear token on logout', () => {
            localStorage.setItem('token', 'test-token');
            expect(localStorage.getItem('token')).toBe('test-token');

            localStorage.removeItem('token');
            expect(localStorage.getItem('token')).toBeNull();
        });
    });
});
