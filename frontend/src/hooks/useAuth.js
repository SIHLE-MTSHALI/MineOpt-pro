/**
 * useAuth.js - Authentication Hook
 * 
 * Provides centralized authentication state management with:
 * - User session management
 * - Token persistence
 * - Auto-refresh on mount
 * - Logout functionality
 * - Loading and error states
 * 
 * @module hooks/useAuth
 */

import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { authAPI, clearCache } from '../services/api';

// =============================================================================
// AUTH CONTEXT
// =============================================================================

const AuthContext = createContext(null);

/**
 * Authentication state shape
 * @typedef {Object} AuthState
 * @property {Object|null} user - Current user object
 * @property {boolean} loading - Loading state
 * @property {boolean} isAuthenticated - Whether user is authenticated
 * @property {Error|null} error - Any authentication error
 */

/**
 * Authentication Provider Component
 * Wraps application to provide auth context to all children
 */
export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    /**
     * Check if user has a valid token and fetch user data
     */
    const checkAuth = useCallback(async () => {
        const token = localStorage.getItem('token');

        if (!token) {
            setLoading(false);
            return;
        }

        try {
            const userData = await authAPI.getCurrentUser();
            setUser({
                ...userData,
                initials: getInitials(userData.username || userData.email),
                displayName: userData.username || userData.email?.split('@')[0] || 'User'
            });
            setError(null);
        } catch (err) {
            // Token is invalid - clear it
            console.warn('[Auth] Token validation failed:', err.message);
            localStorage.removeItem('token');
            setUser(null);
            setError(null); // Don't show error for expired tokens
        } finally {
            setLoading(false);
        }
    }, []);

    /**
     * Login with credentials
     * @param {string} username 
     * @param {string} password 
     * @returns {Promise<Object>} User data
     */
    const login = useCallback(async (username, password) => {
        setLoading(true);
        setError(null);

        try {
            const response = await authAPI.login(username, password);
            localStorage.setItem('token', response.access_token);

            // Fetch full user data
            const userData = await authAPI.getCurrentUser();
            setUser({
                ...userData,
                initials: getInitials(userData.username || username),
                displayName: userData.username || username
            });

            return userData;
        } catch (err) {
            const message = err.response?.data?.detail || 'Login failed. Please check your credentials.';
            setError(new Error(message));
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    /**
     * Register a new account
     * @param {string} username 
     * @param {string} password 
     * @param {string} email 
     * @returns {Promise<Object>} User data
     */
    const register = useCallback(async (username, password, email) => {
        setLoading(true);
        setError(null);

        try {
            await authAPI.register(username, password, email);
            // Auto-login after registration
            return await login(username, password);
        } catch (err) {
            const message = err.response?.data?.detail || 'Registration failed. Please try again.';
            setError(new Error(message));
            throw err;
        } finally {
            setLoading(false);
        }
    }, [login]);

    /**
     * Logout current user
     */
    const logout = useCallback(() => {
        localStorage.removeItem('token');
        clearCache();
        setUser(null);
        setError(null);
    }, []);

    /**
     * Update user data (after profile changes)
     * @param {Object} updates - Partial user data to merge
     */
    const updateUser = useCallback((updates) => {
        setUser(prev => prev ? { ...prev, ...updates } : null);
    }, []);

    // Check authentication on mount
    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const value = {
        user,
        loading,
        error,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        checkAuth,
        updateUser
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * Hook to access authentication state and methods
 * @returns {AuthState & {login: Function, logout: Function, register: Function}}
 */
export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }

    return context;
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get initials from a name string
 * @param {string} name - User name or email
 * @returns {string} Up to 2 character initials
 */
function getInitials(name) {
    if (!name) return 'U';

    const parts = name.split(/[\s@._-]+/).filter(Boolean);

    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }

    return name.substring(0, 2).toUpperCase();
}

/**
 * Check if user has a specific role
 * @param {Object} user - User object
 * @param {string} role - Role to check
 * @returns {boolean}
 */
export function hasRole(user, role) {
    if (!user || !user.roles) return false;
    return user.roles.includes(role);
}

/**
 * Check if user has any of the specified roles
 * @param {Object} user - User object
 * @param {string[]} roles - Roles to check
 * @returns {boolean}
 */
export function hasAnyRole(user, roles) {
    if (!user || !user.roles) return false;
    return roles.some(role => user.roles.includes(role));
}

export default useAuth;
