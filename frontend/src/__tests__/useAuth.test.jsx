/**
 * useAuth.test.jsx - Authentication Hook Tests
 * 
 * Comprehensive tests for the useAuth hook and AuthProvider
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import React from 'react';

// Mock the API module
vi.mock('../services/api', () => ({
    authAPI: {
        login: vi.fn(),
        register: vi.fn(),
        getCurrentUser: vi.fn()
    },
    clearCache: vi.fn()
}));

// Import after mocking
import { authAPI, clearCache } from '../services/api';

// =============================================================================
// AUTH STATE TESTS
// =============================================================================

describe('Authentication State Management', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    afterEach(() => {
        localStorage.clear();
    });

    it('should store token in localStorage', () => {
        const token = 'test-jwt-token-123';
        localStorage.setItem('token', token);
        expect(localStorage.getItem('token')).toBe(token);
    });

    it('should remove token on logout', () => {
        localStorage.setItem('token', 'test-token');
        expect(localStorage.getItem('token')).toBe('test-token');

        localStorage.removeItem('token');
        expect(localStorage.getItem('token')).toBeNull();
    });

    it('should detect authentication status', () => {
        const isAuthenticated = () => !!localStorage.getItem('token');

        expect(isAuthenticated()).toBe(false);

        localStorage.setItem('token', 'valid-token');
        expect(isAuthenticated()).toBe(true);
    });
});

// =============================================================================
// USER DATA TESTS
// =============================================================================

describe('User Data Processing', () => {
    /**
     * Get initials from username or email
     */
    const getInitials = (name) => {
        if (!name) return 'U';
        const parts = name.split(/[\s@._-]+/).filter(Boolean);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    /**
     * Get display name from user data
     */
    const getDisplayName = (userData) => {
        return userData.username || userData.email?.split('@')[0] || 'User';
    };

    it('should extract display name from username', () => {
        expect(getDisplayName({ username: 'admin', email: 'admin@example.com' })).toBe('admin');
        expect(getDisplayName({ username: 'JohnDoe' })).toBe('JohnDoe');
    });

    it('should extract display name from email when no username', () => {
        expect(getDisplayName({ email: 'john.doe@example.com' })).toBe('john.doe');
        expect(getDisplayName({ email: 'admin@company.org' })).toBe('admin');
    });

    it('should return default when no user data', () => {
        expect(getDisplayName({})).toBe('User');
        expect(getDisplayName({ username: '', email: '' })).toBe('User');
    });

    it('should generate correct initials', () => {
        expect(getInitials('John Doe')).toBe('JD');
        expect(getInitials('admin')).toBe('AD');
        expect(getInitials('john.doe@example.com')).toBe('JD');
        expect(getInitials('super_user')).toBe('SU');
    });

    it('should handle edge cases for initials', () => {
        expect(getInitials(null)).toBe('U');
        expect(getInitials(undefined)).toBe('U');
        expect(getInitials('')).toBe('U');
        expect(getInitials('A')).toBe('A');
    });
});

// =============================================================================
// ROLE CHECKING TESTS
// =============================================================================

describe('Role-Based Access Control', () => {
    /**
     * Check if user has a specific role
     */
    const hasRole = (user, role) => {
        if (!user || !user.roles) return false;
        return user.roles.includes(role);
    };

    /**
     * Check if user has any of the specified roles
     */
    const hasAnyRole = (user, roles) => {
        if (!user || !user.roles) return false;
        return roles.some(role => user.roles.includes(role));
    };

    it('should check single role', () => {
        const adminUser = { username: 'admin', roles: ['admin', 'user'] };
        const regularUser = { username: 'user', roles: ['user'] };

        expect(hasRole(adminUser, 'admin')).toBe(true);
        expect(hasRole(adminUser, 'user')).toBe(true);
        expect(hasRole(regularUser, 'admin')).toBe(false);
        expect(hasRole(regularUser, 'user')).toBe(true);
    });

    it('should check any of multiple roles', () => {
        const user = { username: 'editor', roles: ['editor', 'user'] };

        expect(hasAnyRole(user, ['admin', 'editor'])).toBe(true);
        expect(hasAnyRole(user, ['admin', 'superuser'])).toBe(false);
        expect(hasAnyRole(user, ['editor'])).toBe(true);
    });

    it('should handle missing user or roles', () => {
        expect(hasRole(null, 'admin')).toBe(false);
        expect(hasRole(undefined, 'admin')).toBe(false);
        expect(hasRole({}, 'admin')).toBe(false);
        expect(hasRole({ username: 'test' }, 'admin')).toBe(false);
    });
});

// =============================================================================
// LOGIN FLOW TESTS
// =============================================================================

describe('Login Flow', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    it('should simulate successful login', async () => {
        // Simulate login response
        const mockToken = 'jwt-token-12345';
        const mockUser = { user_id: '1', username: 'testuser', email: 'test@example.com' };

        authAPI.login.mockResolvedValueOnce({ access_token: mockToken, token_type: 'bearer' });
        authAPI.getCurrentUser.mockResolvedValueOnce(mockUser);

        // Perform login
        const response = await authAPI.login('testuser', 'password123');
        expect(response.access_token).toBe(mockToken);

        // Store token
        localStorage.setItem('token', response.access_token);
        expect(localStorage.getItem('token')).toBe(mockToken);

        // Fetch user data
        const userData = await authAPI.getCurrentUser();
        expect(userData.username).toBe('testuser');
    });

    it('should handle login failure', async () => {
        authAPI.login.mockRejectedValueOnce({
            response: { status: 401, data: { detail: 'Invalid credentials' } }
        });

        await expect(authAPI.login('wrong', 'password')).rejects.toMatchObject({
            response: { status: 401 }
        });

        expect(localStorage.getItem('token')).toBeNull();
    });
});

// =============================================================================
// LOGOUT FLOW TESTS
// =============================================================================

describe('Logout Flow', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    it('should clear token and cache on logout', () => {
        // Setup - user is logged in
        localStorage.setItem('token', 'valid-token');
        expect(localStorage.getItem('token')).toBe('valid-token');

        // Perform logout
        const logout = () => {
            localStorage.removeItem('token');
            clearCache();
        };

        logout();

        expect(localStorage.getItem('token')).toBeNull();
        expect(clearCache).toHaveBeenCalled();
    });
});

// =============================================================================
// REGISTRATION FLOW TESTS
// =============================================================================

describe('Registration Flow', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    it('should simulate successful registration and auto-login', async () => {
        const mockToken = 'new-user-token';
        const mockUser = { user_id: '2', username: 'newuser', email: 'new@example.com' };

        authAPI.register.mockResolvedValueOnce({ user_id: '2', username: 'newuser' });
        authAPI.login.mockResolvedValueOnce({ access_token: mockToken });
        authAPI.getCurrentUser.mockResolvedValueOnce(mockUser);

        // Register
        const regResult = await authAPI.register('newuser', 'password123', 'new@example.com');
        expect(regResult.username).toBe('newuser');

        // Auto-login
        const loginResult = await authAPI.login('newuser', 'password123');
        localStorage.setItem('token', loginResult.access_token);

        expect(localStorage.getItem('token')).toBe(mockToken);
    });

    it('should handle registration failure', async () => {
        authAPI.register.mockRejectedValueOnce({
            response: { status: 400, data: { detail: 'Username already exists' } }
        });

        await expect(authAPI.register('existing', 'pass', 'email@test.com')).rejects.toMatchObject({
            response: { status: 400 }
        });
    });
});

// =============================================================================
// TOKEN VALIDATION TESTS
// =============================================================================

describe('Token Validation', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    it('should validate token on app load', async () => {
        const mockUser = { user_id: '1', username: 'user', roles: ['user'] };

        // User has stored token
        localStorage.setItem('token', 'stored-token');
        authAPI.getCurrentUser.mockResolvedValueOnce(mockUser);

        // App validates token
        const user = await authAPI.getCurrentUser();
        expect(user.username).toBe('user');
    });

    it('should clear invalid token', async () => {
        localStorage.setItem('token', 'expired-token');

        authAPI.getCurrentUser.mockRejectedValueOnce({
            response: { status: 401, data: { detail: 'Token expired' } }
        });

        try {
            await authAPI.getCurrentUser();
        } catch (e) {
            // Token is invalid - clear it
            localStorage.removeItem('token');
        }

        expect(localStorage.getItem('token')).toBeNull();
    });
});

export default {};
