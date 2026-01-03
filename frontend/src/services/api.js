/**
 * api.js - Centralized API Service
 * 
 * Provides a configured axios instance and API helper functions
 * for all backend endpoints. Handles authentication, error handling,
 * and base URL configuration.
 */

import axios from 'axios';

// Base API configuration
const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with defaults
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

// ============================================
// Authentication API
// ============================================
export const authAPI = {
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await api.post('/auth/token', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    register: async (username, password, email) => {
        const response = await api.post('/auth/register', { username, password, email });
        return response.data;
    },

    getCurrentUser: async () => {
        const response = await api.get('/auth/users/me');
        return response.data;
    }
};

// ============================================
// Configuration API (Sites, Resources, etc.)
// ============================================
export const configAPI = {
    getSites: async () => {
        const response = await api.get('/config/sites');
        return response.data;
    },

    getResources: async (siteId) => {
        const response = await api.get(`/config/resources?site_id=${siteId || ''}`);
        return response.data;
    },

    seedDemoData: async () => {
        const response = await api.post('/config/seed-demo-data');
        return response.data;
    },

    getFlowNetwork: async (siteId) => {
        const response = await api.get(`/config/flow-network/${siteId}`);
        return response.data;
    },

    saveFlowNetwork: async (siteId, data) => {
        const response = await api.put(`/config/flow-network/${siteId}`, data);
        return response.data;
    }
};

// ============================================
// Stockpile API
// ============================================
export const stockpileAPI = {
    getStockpiles: async (siteId) => {
        const response = await api.get(`/stockpiles/site/${siteId}`);
        return response.data;
    },

    getStockpile: async (stockpileId) => {
        const response = await api.get(`/stockpiles/${stockpileId}`);
        return response.data;
    },

    dumpMaterial: async (stockpileId, data) => {
        const response = await api.post(`/stockpiles/${stockpileId}/dump`, data);
        return response.data;
    },

    reclaimMaterial: async (stockpileId, quantity) => {
        const response = await api.post(`/stockpiles/${stockpileId}/reclaim`, { quantity });
        return response.data;
    },

    getInventoryHistory: async (stockpileId, days = 7) => {
        const response = await api.get(`/stockpiles/${stockpileId}/history?days=${days}`);
        return response.data;
    }
};

// ============================================
// Wash Plant API
// ============================================
export const washPlantAPI = {
    getPlants: async (siteId) => {
        const response = await api.get(`/washplant/site/${siteId}`);
        return response.data;
    },

    getWashTable: async (plantId) => {
        const response = await api.get(`/washplant/${plantId}/wash-table`);
        return response.data;
    },

    updateWashTable: async (plantId, rows) => {
        const response = await api.put(`/washplant/${plantId}/wash-table`, { rows });
        return response.data;
    },

    getParameters: async (plantId) => {
        const response = await api.get(`/washplant/${plantId}/parameters`);
        return response.data;
    },

    updateParameters: async (plantId, params) => {
        const response = await api.put(`/washplant/${plantId}/parameters`, params);
        return response.data;
    }
};

// ============================================
// Schedule API
// ============================================
export const scheduleAPI = {
    getVersions: async (siteId) => {
        const response = await api.get(`/schedule/site/${siteId}/versions`);
        return response.data;
    },

    getVersion: async (versionId) => {
        const response = await api.get(`/schedule/versions/${versionId}`);
        return response.data;
    },

    createVersion: async (siteId, name) => {
        const response = await api.post(`/schedule/site/${siteId}/versions`, { name });
        return response.data;
    },

    getTasks: async (versionId) => {
        const response = await api.get(`/schedule/versions/${versionId}/tasks`);
        return response.data;
    },

    updateTask: async (taskId, data) => {
        const response = await api.put(`/schedule/tasks/${taskId}`, data);
        return response.data;
    },

    runOptimization: async (siteId, versionId, constraints) => {
        const response = await api.post('/schedule/optimize', {
            site_id: siteId,
            version_id: versionId,
            constraints
        });
        return response.data;
    },

    publishVersion: async (versionId) => {
        const response = await api.post(`/schedule/versions/${versionId}/publish`);
        return response.data;
    }
};

// ============================================
// Geology API
// ============================================
export const geologyAPI = {
    getBlocks: async (siteId) => {
        const response = await api.get(`/geology/site/${siteId}/blocks`);
        return response.data;
    },

    getBlock: async (blockId) => {
        const response = await api.get(`/geology/blocks/${blockId}`);
        return response.data;
    },

    updateBlockStatus: async (blockId, status) => {
        const response = await api.put(`/geology/blocks/${blockId}/status`, { status });
        return response.data;
    },

    getBlockStatistics: async (siteId) => {
        const response = await api.get(`/geology/site/${siteId}/statistics`);
        return response.data;
    }
};

// ============================================
// Quality API
// ============================================
export const qualityAPI = {
    getSpecs: async (siteId) => {
        const response = await api.get(`/quality/site/${siteId}/specs`);
        return response.data;
    },

    createSpec: async (siteId, spec) => {
        const response = await api.post(`/quality/site/${siteId}/specs`, spec);
        return response.data;
    },

    updateSpec: async (specId, spec) => {
        const response = await api.put(`/quality/specs/${specId}`, spec);
        return response.data;
    },

    deleteSpec: async (specId) => {
        const response = await api.delete(`/quality/specs/${specId}`);
        return response.data;
    }
};

// ============================================
// Reporting API
// ============================================
export const reportingAPI = {
    getDashboard: async (scheduleVersionId) => {
        const params = scheduleVersionId ? `?schedule_version_id=${scheduleVersionId}` : '';
        const response = await api.get(`/reporting/dashboard${params}`);
        return response.data;
    },

    getCycleTimes: async (resourceId) => {
        const params = resourceId ? `?resource_id=${resourceId}` : '';
        const response = await api.get(`/analytics/cycle-times${params}`);
        return response.data;
    },

    getProductionSummary: async (siteId, period) => {
        const response = await api.get(`/reporting/site/${siteId}/summary?period=${period}`);
        return response.data;
    },

    exportReport: async (siteId, format = 'csv') => {
        const response = await api.get(`/reporting/site/${siteId}/export?format=${format}`, {
            responseType: format === 'pdf' ? 'blob' : 'text'
        });
        return response.data;
    }
};

// ============================================
// Settings API
// ============================================
export const settingsAPI = {
    getSettings: async (siteId) => {
        const response = await api.get(`/settings/site/${siteId}`);
        return response.data;
    },

    updateSettings: async (siteId, settings) => {
        const response = await api.put(`/settings/site/${siteId}`, settings);
        return response.data;
    },

    getUserPreferences: async () => {
        const response = await api.get('/settings/preferences');
        return response.data;
    },

    updateUserPreferences: async (preferences) => {
        const response = await api.put('/settings/preferences', preferences);
        return response.data;
    }
};

// Default export
export default api;
