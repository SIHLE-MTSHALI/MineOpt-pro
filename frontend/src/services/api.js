/**
 * api.js - Enterprise API Service Layer
 * 
 * Provides a comprehensive, production-ready API client with:
 * - Centralized axios instance with interceptors
 * - Authentication token management
 * - Automatic retry logic with exponential backoff
 * - Request/response caching for performance
 * - Comprehensive error handling
 * - Full TypeScript-style JSDoc documentation
 * - All backend endpoint coverage
 * 
 * @module api
 * @version 2.0.0
 */

import axios from 'axios';

// =============================================================================
// CONFIGURATION
// =============================================================================

/** Base API URL from environment or fallback */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** Default request timeout in milliseconds */
const DEFAULT_TIMEOUT = 30000;

/** Maximum retry attempts for failed requests */
const MAX_RETRIES = 3;

/** Base delay for exponential backoff (ms) */
const RETRY_BASE_DELAY = 1000;

/** HTTP status codes that should trigger a retry */
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

// =============================================================================
// REQUEST CACHE
// =============================================================================

/**
 * Simple in-memory cache for GET requests
 * Key: URL + query params, Value: { data, timestamp }
 */
const requestCache = new Map();
const CACHE_TTL = 30000; // 30 seconds

/**
 * Get cached response if still valid
 * @param {string} key - Cache key
 * @returns {any|null} Cached data or null
 */
const getCached = (key) => {
    const cached = requestCache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    requestCache.delete(key);
    return null;
};

/**
 * Store response in cache
 * @param {string} key - Cache key
 * @param {any} data - Data to cache
 */
const setCache = (key, data) => {
    requestCache.set(key, { data, timestamp: Date.now() });
};

/**
 * Clear all cached data (useful after mutations)
 */
export const clearCache = () => {
    requestCache.clear();
};

/**
 * Clear cached data matching a pattern
 * @param {string} pattern - URL pattern to match
 */
export const clearCachePattern = (pattern) => {
    for (const key of requestCache.keys()) {
        if (key.includes(pattern)) {
            requestCache.delete(key);
        }
    }
};

// =============================================================================
// AXIOS INSTANCE
// =============================================================================

/**
 * Configured axios instance with base settings
 */
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: DEFAULT_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

// =============================================================================
// INTERCEPTORS
// =============================================================================

/**
 * Request interceptor - Adds auth token to all requests
 */
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp for debugging
        config.metadata = { startTime: Date.now() };

        return config;
    },
    (error) => Promise.reject(error)
);

/**
 * Response interceptor - Handles errors and logging
 */
api.interceptors.response.use(
    (response) => {
        // Log slow requests in development
        if (import.meta.env.DEV && response.config.metadata) {
            const duration = Date.now() - response.config.metadata.startTime;
            if (duration > 1000) {
                console.warn(`[API] Slow request: ${response.config.url} took ${duration}ms`);
            }
        }
        return response;
    },
    async (error) => {
        const { config, response } = error;

        // Handle authentication errors
        if (response?.status === 401) {
            const isAuthEndpoint = config?.url?.includes('/auth/');
            if (isAuthEndpoint) {
                localStorage.removeItem('token');
                window.location.href = '/';
                return Promise.reject(error);
            }
        }

        // Implement retry logic for retryable errors
        if (config && !config._retry && RETRYABLE_STATUS_CODES.includes(response?.status)) {
            config._retryCount = config._retryCount || 0;

            if (config._retryCount < MAX_RETRIES) {
                config._retryCount++;
                config._retry = true;

                // Exponential backoff
                const delay = RETRY_BASE_DELAY * Math.pow(2, config._retryCount - 1);
                await new Promise(resolve => setTimeout(resolve, delay));

                console.warn(`[API] Retrying request (${config._retryCount}/${MAX_RETRIES}): ${config.url}`);
                return api(config);
            }
        }

        // Enhanced error logging
        if (import.meta.env.DEV) {
            console.error('[API Error]', {
                url: config?.url,
                method: config?.method,
                status: response?.status,
                message: response?.data?.detail || error.message
            });
        }

        return Promise.reject(error);
    }
);

// =============================================================================
// HELPER UTILITIES
// =============================================================================

/**
 * Build URL with query parameters
 * @param {string} base - Base URL path
 * @param {Object} params - Query parameters object
 * @returns {string} Full URL with query string
 */
const buildUrl = (base, params = {}) => {
    const filteredParams = Object.entries(params)
        .filter(([_, v]) => v !== undefined && v !== null && v !== '')
        .reduce((acc, [k, v]) => ({ ...acc, [k]: v }), {});

    if (Object.keys(filteredParams).length === 0) return base;

    const queryString = new URLSearchParams(filteredParams).toString();
    return `${base}?${queryString}`;
};

/**
 * Make a cached GET request
 * @param {string} url - Request URL
 * @param {boolean} useCache - Whether to use caching (default: true)
 * @returns {Promise<any>} Response data
 */
const cachedGet = async (url, useCache = true) => {
    if (useCache) {
        const cached = getCached(url);
        if (cached) return cached;
    }

    const response = await api.get(url);
    if (useCache) setCache(url, response.data);
    return response.data;
};

// =============================================================================
// AUTHENTICATION API
// =============================================================================

/**
 * Authentication and user management endpoints
 * @namespace authAPI
 */
export const authAPI = {
    /**
     * Login with username and password
     * @param {string} username - User's username
     * @param {string} password - User's password
     * @returns {Promise<{access_token: string, token_type: string}>}
     */
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await api.post('/auth/token', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    /**
     * Register a new user account
     * @param {string} username - Desired username
     * @param {string} password - Password (min 6 characters)
     * @param {string} email - Email address
     * @returns {Promise<{user_id: string, username: string}>}
     */
    register: async (username, password, email) => {
        const response = await api.post('/auth/register', { username, password, email });
        return response.data;
    },

    /**
     * Get current authenticated user's profile
     * @returns {Promise<{user_id: string, username: string, email: string, roles: string[]}>}
     */
    getCurrentUser: async () => {
        const response = await api.get('/auth/users/me');
        return response.data;
    },

    /**
     * Update current user's password
     * @param {string} currentPassword - Current password
     * @param {string} newPassword - New password
     * @returns {Promise<{success: boolean}>}
     */
    changePassword: async (currentPassword, newPassword) => {
        const response = await api.post('/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword
        });
        return response.data;
    },

    /**
     * Logout - clear local token
     */
    logout: () => {
        localStorage.removeItem('token');
        clearCache();
    }
};

// =============================================================================
// CONFIGURATION API
// =============================================================================

/**
 * Site configuration and resource management
 * @namespace configAPI
 */
export const configAPI = {
    /**
     * Get all available sites
     * @returns {Promise<Array<{site_id: string, name: string, timezone: string}>>}
     */
    getSites: async () => {
        return cachedGet('/config/sites');
    },

    /**
     * Get a specific site by ID
     * @param {string} siteId - Site identifier
     * @returns {Promise<{site_id: string, name: string, timezone: string}>}
     */
    getSite: async (siteId) => {
        return cachedGet(`/config/sites/${siteId}`);
    },

    /**
     * Get resources for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{resource_id: string, name: string, resource_type: string}>>}
     */
    getResources: async (siteId) => {
        const url = buildUrl('/config/resources', { site_id: siteId });
        return cachedGet(url);
    },

    /**
     * Get activity areas (mining blocks) for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{area_id: string, name: string, geometry: Object}>>}
     */
    getActivityAreas: async (siteId) => {
        const url = buildUrl('/config/activity-areas', { site_id: siteId });
        return cachedGet(url);
    },

    /**
     * Get flow network nodes (stockpiles, plants, dumps)
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{node_id: string, name: string, node_type: string}>>}
     */
    getNetworkNodes: async (siteId) => {
        const url = buildUrl('/config/network-nodes', { site_id: siteId });
        return cachedGet(url);
    },

    /**
     * Get complete flow network configuration
     * @param {string} siteId - Site identifier
     * @returns {Promise<{nodes: Array, arcs: Array}>}
     */
    getFlowNetwork: async (siteId) => {
        return cachedGet(`/config/flow-network/${siteId}`);
    },

    /**
     * Save flow network configuration
     * @param {string} siteId - Site identifier
     * @param {Object} data - Network configuration
     * @returns {Promise<{success: boolean}>}
     */
    saveFlowNetwork: async (siteId, data) => {
        clearCachePattern('/config/');
        const response = await api.put(`/config/flow-network/${siteId}`, data);
        return response.data;
    },

    /**
     * Seed comprehensive demo data
     * @returns {Promise<{sites_created: number, equipment_created: number}>}
     */
    seedDemoData: async () => {
        clearCache();
        const response = await api.post('/config/seed-demo-data');
        return response.data;
    }
};

// =============================================================================
// CALENDAR API
// =============================================================================

/**
 * Calendar and scheduling period management
 * @namespace calendarAPI
 */
export const calendarAPI = {
    /**
     * Get calendars for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{calendar_id: string, name: string, shift_hours: number}>>}
     */
    getCalendars: async (siteId) => {
        return cachedGet(`/calendar/site/${siteId}`);
    },

    /**
     * Get a specific calendar
     * @param {string} calendarId - Calendar identifier
     * @returns {Promise<{calendar_id: string, name: string, periods: Array}>}
     */
    getCalendar: async (calendarId) => {
        return cachedGet(`/calendar/${calendarId}`);
    },

    /**
     * Get periods for a calendar
     * @param {string} calendarId - Calendar identifier
     * @returns {Promise<Array<{period_id: string, start_date: string, end_date: string}>>}
     */
    getPeriods: async (calendarId) => {
        return cachedGet(`/calendar/${calendarId}/periods`);
    },

    /**
     * Create a new calendar
     * @param {string} siteId - Site identifier
     * @param {Object} data - Calendar configuration
     * @returns {Promise<{calendar_id: string}>}
     */
    createCalendar: async (siteId, data) => {
        clearCachePattern('/calendar/');
        const response = await api.post(`/calendar/site/${siteId}`, data);
        return response.data;
    },

    /**
     * Generate periods for a calendar
     * @param {string} calendarId - Calendar identifier
     * @param {string} startDate - Start date (ISO format)
     * @param {string} endDate - End date (ISO format)
     * @returns {Promise<{periods_created: number}>}
     */
    generatePeriods: async (calendarId, startDate, endDate) => {
        clearCachePattern('/calendar/');
        const response = await api.post(`/calendar/${calendarId}/generate-periods`, {
            start_date: startDate,
            end_date: endDate
        });
        return response.data;
    }
};

// =============================================================================
// SCHEDULE API
// =============================================================================

/**
 * Schedule version and task management
 * @namespace scheduleAPI
 */
export const scheduleAPI = {
    /**
     * Get all schedule versions for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{version_id: string, name: string, status: string}>>}
     */
    getVersions: async (siteId) => {
        return cachedGet(`/schedule/site/${siteId}/versions`);
    },

    /**
     * Get a specific schedule version
     * @param {string} versionId - Version identifier
     * @returns {Promise<{version_id: string, name: string, status: string, created_at: string}>}
     */
    getVersion: async (versionId) => {
        return cachedGet(`/schedule/versions/${versionId}`);
    },

    /**
     * Create a new schedule version
     * @param {string} siteId - Site identifier
     * @param {string} name - Version name
     * @returns {Promise<{version_id: string}>}
     */
    createVersion: async (siteId, name) => {
        clearCachePattern('/schedule/');
        const response = await api.post(`/schedule/site/${siteId}/versions`, { name });
        return response.data;
    },

    /**
     * Fork an existing schedule version
     * @param {string} versionId - Source version identifier
     * @param {string} newName - Name for the forked version
     * @returns {Promise<{version_id: string}>}
     */
    forkVersion: async (versionId, newName) => {
        clearCachePattern('/schedule/');
        const response = await api.post(
            `/schedule/versions/${versionId}/fork?new_name=${encodeURIComponent(newName)}`
        );
        return response.data;
    },

    /**
     * Get tasks for a schedule version
     * @param {string} versionId - Version identifier
     * @returns {Promise<Array<{task_id: string, resource_id: string, period_id: string, planned_quantity: number}>>}
     */
    getTasks: async (versionId) => {
        return cachedGet(`/schedule/versions/${versionId}/tasks`, false);
    },

    /**
     * Create a new task
     * @param {string} versionId - Version identifier
     * @param {Object} taskData - Task configuration
     * @returns {Promise<{task_id: string}>}
     */
    createTask: async (versionId, taskData) => {
        clearCachePattern('/schedule/');
        const response = await api.post(`/schedule/versions/${versionId}/tasks`, taskData);
        return response.data;
    },

    /**
     * Update an existing task
     * @param {string} taskId - Task identifier
     * @param {Object} data - Updated task data
     * @returns {Promise<{task_id: string}>}
     */
    updateTask: async (taskId, data) => {
        clearCachePattern('/schedule/');
        const response = await api.put(`/schedule/tasks/${taskId}`, data);
        return response.data;
    },

    /**
     * Delete a task
     * @param {string} taskId - Task identifier
     * @returns {Promise<{success: boolean}>}
     */
    deleteTask: async (taskId) => {
        clearCachePattern('/schedule/');
        const response = await api.delete(`/schedule/tasks/${taskId}`);
        return response.data;
    },

    /**
     * Publish a schedule version
     * @param {string} versionId - Version identifier
     * @returns {Promise<{status: string}>}
     */
    publishVersion: async (versionId) => {
        clearCachePattern('/schedule/');
        const response = await api.post(`/schedule/versions/${versionId}/publish`);
        return response.data;
    }
};

// =============================================================================
// OPTIMIZATION API
// =============================================================================

/**
 * Schedule optimization and solver endpoints
 * @namespace optimizationAPI
 */
export const optimizationAPI = {
    /**
     * Run schedule optimization
     * @param {string} siteId - Site identifier
     * @param {string} scheduleVersionId - Schedule version to optimize
     * @param {Object} options - Optimization options
     * @returns {Promise<{message: string, tasks_updated: number}>}
     */
    runOptimization: async (siteId, scheduleVersionId, options = {}) => {
        clearCachePattern('/schedule/');
        const response = await api.post('/optimization/run', {
            site_id: siteId,
            schedule_version_id: scheduleVersionId,
            ...options
        });
        return response.data;
    },

    /**
     * Run fast pass optimization (quick heuristic)
     * @param {string} siteId - Site identifier
     * @param {string} scheduleVersionId - Schedule version
     * @returns {Promise<{message: string, duration_ms: number}>}
     */
    runFastPass: async (siteId, scheduleVersionId) => {
        clearCachePattern('/schedule/');
        const response = await api.post('/optimization/fast-pass', {
            site_id: siteId,
            schedule_version_id: scheduleVersionId
        });
        return response.data;
    },

    /**
     * Get optimization status
     * @param {string} jobId - Optimization job identifier
     * @returns {Promise<{status: string, progress: number, result: Object}>}
     */
    getOptimizationStatus: async (jobId) => {
        const response = await api.get(`/optimization/status/${jobId}`);
        return response.data;
    },

    /**
     * Run CP solver for constraint satisfaction
     * @param {Object} problem - Problem definition
     * @returns {Promise<{solution: Object, feasible: boolean}>}
     */
    runCPSolver: async (problem) => {
        const response = await api.post('/cp-solver/solve', problem);
        return response.data;
    }
};

// =============================================================================
// STOCKPILE API
// =============================================================================

/**
 * Stockpile management and inventory tracking
 * @namespace stockpileAPI
 */
export const stockpileAPI = {
    /**
     * Get all stockpiles for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{stockpile_id: string, name: string, current_tonnes: number}>>}
     */
    getStockpiles: async (siteId) => {
        return cachedGet(`/stockpiles/site/${siteId}`);
    },

    /**
     * Get a specific stockpile with details
     * @param {string} stockpileId - Stockpile identifier
     * @returns {Promise<{stockpile_id: string, name: string, current_tonnes: number, quality: Object}>}
     */
    getStockpile: async (stockpileId) => {
        return cachedGet(`/stockpiles/${stockpileId}`);
    },

    /**
     * Dump material to stockpile
     * @param {string} stockpileId - Stockpile identifier
     * @param {Object} data - Material data (tonnes, quality)
     * @returns {Promise<{transaction_id: string, new_balance: number}>}
     */
    dumpMaterial: async (stockpileId, data) => {
        clearCachePattern('/stockpiles/');
        const response = await api.post(`/stockpiles/${stockpileId}/dump`, data);
        return response.data;
    },

    /**
     * Reclaim material from stockpile
     * @param {string} stockpileId - Stockpile identifier
     * @param {number} quantity - Tonnes to reclaim
     * @returns {Promise<{transaction_id: string, new_balance: number, reclaimed_quality: Object}>}
     */
    reclaimMaterial: async (stockpileId, quantity) => {
        clearCachePattern('/stockpiles/');
        const response = await api.post(`/stockpiles/${stockpileId}/reclaim`, { quantity });
        return response.data;
    },

    /**
     * Get inventory history for a stockpile
     * @param {string} stockpileId - Stockpile identifier
     * @param {number} days - Number of days of history (default: 7)
     * @returns {Promise<Array<{timestamp: string, balance: number, transaction_type: string}>>}
     */
    getInventoryHistory: async (stockpileId, days = 7) => {
        return cachedGet(`/stockpiles/${stockpileId}/history?days=${days}`);
    },

    /**
     * Get stockpile balance at a specific time
     * @param {string} stockpileId - Stockpile identifier
     * @param {string} timestamp - ISO timestamp
     * @returns {Promise<{balance: number, quality: Object}>}
     */
    getBalanceAt: async (stockpileId, timestamp) => {
        const response = await api.get(`/stockpiles/${stockpileId}/balance-at?timestamp=${timestamp}`);
        return response.data;
    }
};

// =============================================================================
// WASH PLANT API
// =============================================================================

/**
 * Wash plant configuration and processing
 * @namespace washPlantAPI
 */
export const washPlantAPI = {
    /**
     * Get all wash plants for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{plant_id: string, name: string, capacity_tph: number}>>}
     */
    getPlants: async (siteId) => {
        return cachedGet(`/wash-plants/site/${siteId}`);
    },

    /**
     * Get wash table for a plant
     * @param {string} plantId - Plant identifier
     * @returns {Promise<{rows: Array<{sg: number, yield_percent: number}>}>}
     */
    getWashTable: async (plantId) => {
        return cachedGet(`/washplant/${plantId}/wash-table`);
    },

    /**
     * Update wash table
     * @param {string} plantId - Plant identifier
     * @param {Array} rows - Wash table rows
     * @returns {Promise<{success: boolean}>}
     */
    updateWashTable: async (plantId, rows) => {
        clearCachePattern('/wash');
        const response = await api.put(`/washplant/${plantId}/wash-table`, { rows });
        return response.data;
    },

    /**
     * Get plant operating parameters
     * @param {string} plantId - Plant identifier
     * @returns {Promise<{cutpoint: number, throughput: number}>}
     */
    getParameters: async (plantId) => {
        return cachedGet(`/washplant/${plantId}/parameters`);
    },

    /**
     * Update plant parameters
     * @param {string} plantId - Plant identifier
     * @param {Object} params - Updated parameters
     * @returns {Promise<{success: boolean}>}
     */
    updateParameters: async (plantId, params) => {
        clearCachePattern('/wash');
        const response = await api.put(`/washplant/${plantId}/parameters`, params);
        return response.data;
    },

    /**
     * Simulate wash plant processing
     * @param {string} plantId - Plant identifier
     * @param {Object} input - Input material specification
     * @returns {Promise<{product_tonnes: number, yield_percent: number, product_quality: Object}>}
     */
    simulateProcess: async (plantId, input) => {
        const response = await api.post(`/washplant/${plantId}/simulate`, input);
        return response.data;
    }
};

// =============================================================================
// GEOLOGY API
// =============================================================================

/**
 * Geological data and block model management
 * @namespace geologyAPI
 */
export const geologyAPI = {
    /**
     * Get all blocks for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{block_id: string, name: string, status: string}>>}
     */
    getBlocks: async (siteId) => {
        return cachedGet(`/geology/site/${siteId}/blocks`);
    },

    /**
     * Get a specific block with full details
     * @param {string} blockId - Block identifier
     * @returns {Promise<{block_id: string, geometry: Object, qualities: Object}>}
     */
    getBlock: async (blockId) => {
        return cachedGet(`/geology/blocks/${blockId}`);
    },

    /**
     * Update block status
     * @param {string} blockId - Block identifier
     * @param {string} status - New status (available, scheduled, mined)
     * @returns {Promise<{block_id: string, status: string}>}
     */
    updateBlockStatus: async (blockId, status) => {
        clearCachePattern('/geology/');
        const response = await api.put(`/geology/blocks/${blockId}/status`, { status });
        return response.data;
    },

    /**
     * Get block statistics summary for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<{total_blocks: number, total_tonnes: number, avg_quality: Object}>}
     */
    getBlockStatistics: async (siteId) => {
        return cachedGet(`/geology/site/${siteId}/statistics`);
    }
};

// =============================================================================
// QUALITY API
// =============================================================================

/**
 * Quality specification and blend management
 * @namespace qualityAPI
 */
export const qualityAPI = {
    /**
     * Get quality specifications for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{spec_id: string, name: string, limits: Object}>>}
     */
    getSpecs: async (siteId) => {
        return cachedGet(`/quality/site/${siteId}/specs`);
    },

    /**
     * Create a new quality specification
     * @param {string} siteId - Site identifier
     * @param {Object} spec - Specification data
     * @returns {Promise<{spec_id: string}>}
     */
    createSpec: async (siteId, spec) => {
        clearCachePattern('/quality/');
        const response = await api.post(`/quality/site/${siteId}/specs`, spec);
        return response.data;
    },

    /**
     * Update a quality specification
     * @param {string} specId - Specification identifier
     * @param {Object} spec - Updated specification data
     * @returns {Promise<{spec_id: string}>}
     */
    updateSpec: async (specId, spec) => {
        clearCachePattern('/quality/');
        const response = await api.put(`/quality/specs/${specId}`, spec);
        return response.data;
    },

    /**
     * Delete a quality specification
     * @param {string} specId - Specification identifier
     * @returns {Promise<{success: boolean}>}
     */
    deleteSpec: async (specId) => {
        clearCachePattern('/quality/');
        const response = await api.delete(`/quality/specs/${specId}`);
        return response.data;
    },

    /**
     * Run Monte Carlo blend simulation
     * @param {Object} blendConfig - Blend configuration with sources
     * @param {number} iterations - Number of simulation iterations
     * @returns {Promise<{results: Object, confidence_bands: Object, compliance_probability: number}>}
     */
    runSimulation: async (blendConfig, iterations = 1000) => {
        const response = await api.post('/quality/simulate', {
            ...blendConfig,
            iterations
        });
        return response.data;
    }
};

// =============================================================================
// ANALYTICS API
// =============================================================================

/**
 * Analytics and reporting endpoints
 * @namespace analyticsAPI
 */
export const analyticsAPI = {
    /**
     * Get dashboard summary metrics
     * @param {string} siteId - Site identifier
     * @returns {Promise<{planned_tonnes: number, actual_tonnes: number, variance: number, quality_compliance: number}>}
     */
    getDashboardSummary: async (siteId) => {
        const url = buildUrl('/analytics/dashboard-summary', { site_id: siteId });
        return cachedGet(url);
    },

    /**
     * Get cycle time analytics
     * @param {string} resourceId - Optional resource filter
     * @returns {Promise<Array<{resource_id: string, avg_cycle_time: number, cycles: number}>>}
     */
    getCycleTimes: async (resourceId) => {
        const url = buildUrl('/analytics/cycle-times', { resource_id: resourceId });
        return cachedGet(url);
    },

    /**
     * Get productivity metrics
     * @param {string} siteId - Site identifier
     * @param {string} startDate - Start date (ISO format)
     * @param {string} endDate - End date (ISO format)
     * @returns {Promise<{daily_tonnes: Array, utilization: number}>}
     */
    getProductivity: async (siteId, startDate, endDate) => {
        const url = buildUrl('/analytics/productivity', {
            site_id: siteId,
            start_date: startDate,
            end_date: endDate
        });
        return cachedGet(url);
    },

    /**
     * Get equipment utilization report
     * @param {string} siteId - Site identifier
     * @param {string} period - Time period (day, week, month)
     * @returns {Promise<Array<{equipment_id: string, utilization_percent: number}>>}
     */
    getEquipmentUtilization: async (siteId, period = 'week') => {
        const url = buildUrl('/analytics/equipment-utilization', {
            site_id: siteId,
            period
        });
        return cachedGet(url);
    }
};

// =============================================================================
// REPORTING API
// =============================================================================

/**
 * Report generation and export
 * @namespace reportingAPI
 */
export const reportingAPI = {
    /**
     * Get dashboard report data
     * @param {string} scheduleVersionId - Optional schedule version filter
     * @returns {Promise<Object>}
     */
    getDashboard: async (scheduleVersionId) => {
        const url = buildUrl('/reporting/dashboard', { schedule_version_id: scheduleVersionId });
        return cachedGet(url);
    },

    /**
     * Get production summary report
     * @param {string} siteId - Site identifier
     * @param {string} period - Report period (day, week, month)
     * @returns {Promise<Object>}
     */
    getProductionSummary: async (siteId, period) => {
        return cachedGet(`/reporting/site/${siteId}/summary?period=${period}`);
    },

    /**
     * Export report in specified format
     * @param {string} siteId - Site identifier
     * @param {string} format - Export format (csv, pdf, xlsx)
     * @returns {Promise<Blob|string>}
     */
    exportReport: async (siteId, format = 'csv') => {
        const response = await api.get(`/reporting/site/${siteId}/export?format=${format}`, {
            responseType: format === 'pdf' ? 'blob' : 'text'
        });
        return response.data;
    },

    /**
     * Run ad-hoc query
     * @param {Object} queryConfig - Query configuration
     * @returns {Promise<{columns: Array, rows: Array}>}
     */
    runQuery: async (queryConfig) => {
        const response = await api.post('/reports/query', queryConfig);
        return response.data;
    },

    /**
     * Schedule a recurring report
     * @param {Object} scheduleConfig - Schedule configuration
     * @returns {Promise<{schedule_id: string}>}
     */
    scheduleReport: async (scheduleConfig) => {
        const response = await api.post('/reports/schedules', scheduleConfig);
        return response.data;
    },

    /**
     * Get scheduled reports
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array>}
     */
    getScheduledReports: async (siteId) => {
        return cachedGet(`/reports/schedules?site_id=${siteId}`);
    }
};

// =============================================================================
// FLEET MANAGEMENT API
// =============================================================================

/**
 * Fleet management and equipment tracking
 * @namespace fleetAPI
 */
export const fleetAPI = {
    /**
     * Get equipment list for a site
     * @param {string} siteId - Site identifier
     * @param {string} type - Optional equipment type filter
     * @param {string} status - Optional status filter
     * @returns {Promise<Array<{equipment_id: string, name: string, type: string, status: string}>>}
     */
    getEquipmentList: async (siteId, type, status) => {
        const params = new URLSearchParams();
        if (type) params.append('equipment_type', type);
        if (status) params.append('status', status);
        const url = `/fleet/sites/${siteId}/equipment${params.toString() ? '?' + params : ''}`;
        return cachedGet(url);
    },

    /**
     * Get detailed equipment information
     * @param {string} equipmentId - Equipment identifier
     * @returns {Promise<Object>}
     */
    getEquipment: async (equipmentId) => {
        return cachedGet(`/fleet/equipment/${equipmentId}`);
    },

    /**
     * Update equipment status
     * @param {string} equipmentId - Equipment identifier
     * @param {string} status - New status
     * @param {string} operatorId - Optional operator ID
     * @returns {Promise<{equipment_id: string, status: string}>}
     */
    updateStatus: async (equipmentId, status, operatorId) => {
        clearCachePattern('/fleet/');
        const response = await api.patch(`/fleet/equipment/${equipmentId}/status`, {
            status,
            operator_id: operatorId
        });
        return response.data;
    },

    /**
     * Get current equipment positions
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{equipment_id: string, lat: number, lng: number, heading: number}>>}
     */
    getPositions: async (siteId) => {
        // Don't cache GPS positions - always get fresh data
        const response = await api.get(`/fleet/sites/${siteId}/positions`);
        return response.data;
    },

    /**
     * Get pending maintenance items
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array>}
     */
    getMaintenancePending: async (siteId) => {
        return cachedGet(`/fleet/sites/${siteId}/maintenance/pending`);
    },

    /**
     * Schedule maintenance
     * @param {Object} data - Maintenance schedule data
     * @returns {Promise<{maintenance_id: string}>}
     */
    scheduleMaintenance: async (data) => {
        clearCachePattern('/fleet/');
        const response = await api.post('/fleet/maintenance', data);
        return response.data;
    },

    /**
     * Get haul cycles for analysis
     * @param {string} siteId - Site identifier
     * @param {string} startDate - Start date
     * @param {string} endDate - End date
     * @returns {Promise<Array<{cycle_id: string, duration_minutes: number, payload_tonnes: number}>>}
     */
    getHaulCycles: async (siteId, startDate, endDate) => {
        const url = buildUrl(`/fleet/sites/${siteId}/haul-cycles`, {
            start_date: startDate,
            end_date: endDate
        });
        return cachedGet(url);
    },

    /**
     * Get geofences for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{geofence_id: string, name: string, geometry: Object}>>}
     */
    getGeofences: async (siteId) => {
        return cachedGet(`/fleet/sites/${siteId}/geofences`);
    },

    /**
     * Get geofence violations
     * @param {string} siteId - Site identifier
     * @param {number} hours - Lookback hours (default: 24)
     * @returns {Promise<Array>}
     */
    getGeofenceViolations: async (siteId, hours = 24) => {
        return cachedGet(`/fleet/sites/${siteId}/geofence-violations?hours=${hours}`);
    }
};

// =============================================================================
// DRILL & BLAST API
// =============================================================================

/**
 * Drill and blast pattern management
 * @namespace drillBlastAPI
 */
export const drillBlastAPI = {
    /**
     * Get blast patterns for a site
     * @param {string} siteId - Site identifier
     * @param {string} status - Optional status filter
     * @returns {Promise<Array<{pattern_id: string, name: string, status: string}>>}
     */
    getPatterns: async (siteId, status) => {
        const url = buildUrl(`/drill-blast/sites/${siteId}/patterns`, { status });
        return cachedGet(url);
    },

    /**
     * Get a specific pattern with holes
     * @param {string} patternId - Pattern identifier
     * @returns {Promise<{pattern_id: string, holes: Array, parameters: Object}>}
     */
    getPattern: async (patternId) => {
        return cachedGet(`/drill-blast/patterns/${patternId}`);
    },

    /**
     * Create a new blast pattern
     * @param {Object} data - Pattern configuration
     * @returns {Promise<{pattern_id: string}>}
     */
    createPattern: async (data) => {
        clearCachePattern('/drill-blast/');
        const response = await api.post('/drill-blast/patterns', data);
        return response.data;
    },

    /**
     * Update a blast pattern
     * @param {string} patternId - Pattern identifier
     * @param {Object} data - Updated pattern data
     * @returns {Promise<{pattern_id: string}>}
     */
    updatePattern: async (patternId, data) => {
        clearCachePattern('/drill-blast/');
        const response = await api.put(`/drill-blast/patterns/${patternId}`, data);
        return response.data;
    },

    /**
     * Get drill holes for a pattern
     * @param {string} patternId - Pattern identifier
     * @returns {Promise<Array<{hole_id: string, x: number, y: number, depth: number}>>}
     */
    getHoles: async (patternId) => {
        return cachedGet(`/drill-blast/patterns/${patternId}/holes`);
    },

    /**
     * Create a blast event (log a blast)
     * @param {Object} data - Blast event data
     * @returns {Promise<{event_id: string}>}
     */
    createBlastEvent: async (data) => {
        clearCachePattern('/drill-blast/');
        const response = await api.post('/drill-blast/events', data);
        return response.data;
    },

    /**
     * Predict fragmentation using Kuz-Ram model
     * @param {Object} params - Blast parameters
     * @returns {Promise<{x50: number, x80: number, uniformity_index: number}>}
     */
    predictFragmentation: async (params) => {
        const response = await api.post('/drill-blast/predict-fragmentation', params);
        return response.data;
    }
};

// =============================================================================
// OPERATIONS API
// =============================================================================

/**
 * Shift operations and material tracking
 * @namespace operationsAPI
 */
export const operationsAPI = {
    /**
     * Get active shift for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<{shift_id: string, shift_type: string, started_at: string}|null>}
     */
    getActiveShift: async (siteId) => {
        try {
            const response = await api.get(`/operations/sites/${siteId}/active-shift`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 404) return null;
            throw error;
        }
    },

    /**
     * Start a new shift
     * @param {Object} data - Shift start data
     * @returns {Promise<{shift_id: string}>}
     */
    startShift: async (data) => {
        clearCachePattern('/operations/');
        const response = await api.post('/operations/shifts', data);
        return response.data;
    },

    /**
     * End a shift
     * @param {string} shiftId - Shift identifier
     * @returns {Promise<{shift_id: string, ended_at: string}>}
     */
    endShift: async (shiftId) => {
        clearCachePattern('/operations/');
        const response = await api.post(`/operations/shifts/${shiftId}/end`);
        return response.data;
    },

    /**
     * Get load tickets for a shift
     * @param {string} shiftId - Shift identifier
     * @returns {Promise<Array<{ticket_id: string, tonnes: number, material_type: string}>>}
     */
    getShiftTickets: async (shiftId) => {
        return cachedGet(`/operations/shifts/${shiftId}/tickets`);
    },

    /**
     * Create a load ticket
     * @param {Object} data - Ticket data
     * @returns {Promise<{ticket_id: string}>}
     */
    createTicket: async (data) => {
        clearCachePattern('/operations/');
        const response = await api.post('/operations/tickets', data);
        return response.data;
    },

    /**
     * Create a shift handover
     * @param {Object} data - Handover data
     * @returns {Promise<{handover_id: string}>}
     */
    createHandover: async (data) => {
        clearCachePattern('/operations/');
        const response = await api.post('/operations/handovers', data);
        return response.data;
    },

    /**
     * Get recent shifts
     * @param {string} siteId - Site identifier
     * @param {number} limit - Number of shifts to retrieve
     * @returns {Promise<Array>}
     */
    getRecentShifts: async (siteId, limit = 10) => {
        return cachedGet(`/operations/sites/${siteId}/shifts?limit=${limit}`);
    },

    /**
     * Log an incident
     * @param {Object} data - Incident data
     * @returns {Promise<{incident_id: string}>}
     */
    logIncident: async (data) => {
        const response = await api.post('/operations/incidents', data);
        return response.data;
    }
};

// =============================================================================
// MONITORING API
// =============================================================================

/**
 * Geotechnical and environmental monitoring
 * @namespace monitoringAPI
 */
export const monitoringAPI = {
    /**
     * Get slope stability alerts
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{alert_id: string, prism_id: string, severity: string, displacement_mm: number}>>}
     */
    getSlopeAlerts: async (siteId) => {
        return cachedGet(`/monitoring/sites/${siteId}/slope-alerts`);
    },

    /**
     * Get prism readings for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{prism_id: string, name: string, latest_reading: Object}>>}
     */
    getPrisms: async (siteId) => {
        return cachedGet(`/monitoring/sites/${siteId}/prisms`);
    },

    /**
     * Get prism reading history
     * @param {string} prismId - Prism identifier
     * @param {number} days - Days of history
     * @returns {Promise<Array<{timestamp: string, displacement_mm: number}>>}
     */
    getPrismHistory: async (prismId, days = 30) => {
        return cachedGet(`/monitoring/prisms/${prismId}/history?days=${days}`);
    },

    /**
     * Get dust exceedances
     * @param {string} siteId - Site identifier
     * @param {string} startDate - Start date
     * @param {string} endDate - End date
     * @returns {Promise<Array<{monitor_id: string, timestamp: string, pm10: number, pm25: number}>>}
     */
    getDustExceedances: async (siteId, startDate, endDate) => {
        const url = buildUrl(`/monitoring/sites/${siteId}/dust-exceedances`, {
            start_date: startDate,
            end_date: endDate
        });
        return cachedGet(url);
    },

    /**
     * Get dust monitors for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array>}
     */
    getDustMonitors: async (siteId) => {
        return cachedGet(`/monitoring/sites/${siteId}/dust-monitors`);
    },

    /**
     * Create a monitoring prism
     * @param {Object} data - Prism configuration
     * @returns {Promise<{prism_id: string}>}
     */
    createPrism: async (data) => {
        clearCachePattern('/monitoring/');
        const response = await api.post('/monitoring/prisms', data);
        return response.data;
    },

    /**
     * Create a dust monitor
     * @param {Object} data - Monitor configuration
     * @returns {Promise<{monitor_id: string}>}
     */
    createDustMonitor: async (data) => {
        clearCachePattern('/monitoring/');
        const response = await api.post('/monitoring/dust-monitors', data);
        return response.data;
    },

    /**
     * Get water level readings
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array>}
     */
    getWaterLevels: async (siteId) => {
        return cachedGet(`/monitoring/sites/${siteId}/water-levels`);
    }
};

// =============================================================================
// SETTINGS API
// =============================================================================

/**
 * Site and user settings management
 * @namespace settingsAPI
 */
export const settingsAPI = {
    /**
     * Get site settings
     * @param {string} siteId - Site identifier
     * @returns {Promise<Object>}
     */
    getSettings: async (siteId) => {
        return cachedGet(`/settings/site/${siteId}`);
    },

    /**
     * Update site settings
     * @param {string} siteId - Site identifier
     * @param {Object} settings - Updated settings
     * @returns {Promise<{success: boolean}>}
     */
    updateSettings: async (siteId, settings) => {
        clearCachePattern('/settings/');
        const response = await api.put(`/settings/site/${siteId}`, settings);
        return response.data;
    },

    /**
     * Get user preferences
     * @returns {Promise<Object>}
     */
    getUserPreferences: async () => {
        return cachedGet('/settings/preferences');
    },

    /**
     * Update user preferences
     * @param {Object} preferences - Updated preferences
     * @returns {Promise<{success: boolean}>}
     */
    updateUserPreferences: async (preferences) => {
        clearCachePattern('/settings/');
        const response = await api.put('/settings/preferences', preferences);
        return response.data;
    }
};

// =============================================================================
// SURFACE API
// =============================================================================

/**
 * Terrain surface and 3D data management
 * @namespace surfaceAPI
 */
export const surfaceAPI = {
    /**
     * Get surfaces for a site
     * @param {string} siteId - Site identifier
     * @returns {Promise<Array<{surface_id: string, name: string, type: string}>>}
     */
    getSurfaces: async (siteId) => {
        return cachedGet(`/surfaces/site/${siteId}`);
    },

    /**
     * Get surface mesh data
     * @param {string} surfaceId - Surface identifier
     * @returns {Promise<{vertices: Array, faces: Array}>}
     */
    getSurfaceMesh: async (surfaceId) => {
        return cachedGet(`/surfaces/${surfaceId}/mesh`);
    },

    /**
     * Get surface versions (historical)
     * @param {string} surfaceId - Surface identifier
     * @returns {Promise<Array>}
     */
    getSurfaceVersions: async (surfaceId) => {
        return cachedGet(`/surfaces/${surfaceId}/versions`);
    },

    /**
     * Compare two surfaces (cut/fill volumes)
     * @param {string} surfaceId1 - First surface
     * @param {string} surfaceId2 - Second surface
     * @returns {Promise<{cut_volume: number, fill_volume: number, net_volume: number}>}
     */
    compareSurfaces: async (surfaceId1, surfaceId2) => {
        const response = await api.get(`/surfaces/compare?surface1=${surfaceId1}&surface2=${surfaceId2}`);
        return response.data;
    },

    /**
     * Upload a surface file
     * @param {FormData} formData - File upload form data
     * @returns {Promise<{surface_id: string}>}
     */
    uploadSurface: async (formData) => {
        clearCachePattern('/surfaces/');
        const response = await api.post('/surfaces/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    }
};

// =============================================================================
// INTEGRATION API
// =============================================================================

/**
 * External system integration
 * @namespace integrationAPI
 */
export const integrationAPI = {
    /**
     * Get external ID mappings
     * @param {string} entityType - Entity type (parcel, resource, location, product)
     * @returns {Promise<Array<{external_id: string, internal_id: string}>>}
     */
    getMappings: async (entityType) => {
        return cachedGet(`/integration/mappings/${entityType}`);
    },

    /**
     * Create external ID mapping
     * @param {string} entityType - Entity type
     * @param {Object} mapping - Mapping data
     * @returns {Promise<{mapping_id: string}>}
     */
    createMapping: async (entityType, mapping) => {
        clearCachePattern('/integration/');
        const response = await api.post(`/integration/mappings/${entityType}`, mapping);
        return response.data;
    },

    /**
     * Import lab results
     * @param {FormData} formData - Lab results file
     * @returns {Promise<{records_imported: number}>}
     */
    importLabResults: async (formData) => {
        const response = await api.post('/integration/lab-results', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    /**
     * Trigger BI extract
     * @param {Object} config - Extract configuration
     * @returns {Promise<{extract_id: string}>}
     */
    triggerBIExtract: async (config) => {
        const response = await api.post('/integration/bi-extract', config);
        return response.data;
    },

    /**
     * Get integration connections status
     * @returns {Promise<Array<{system: string, status: string, last_sync: string}>>}
     */
    getConnectionsStatus: async () => {
        return cachedGet('/integration/connections');
    }
};

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default api;
