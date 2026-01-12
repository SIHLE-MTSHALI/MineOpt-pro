/**
 * SiteContext.jsx - Site Selection Context
 * 
 * Provides site selection state across all components.
 * Replaces hardcoded "site-001" values throughout the app.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Use environment variable with fallback
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const SiteContext = createContext(null);

export const useSite = () => {
    const context = useContext(SiteContext);
    if (!context) {
        throw new Error('useSite must be used within a SiteProvider');
    }
    return context;
};

export const SiteProvider = ({ children }) => {
    const [sites, setSites] = useState([]);
    const [currentSiteId, setCurrentSiteId] = useState(null);
    const [currentSite, setCurrentSite] = useState(null);
    const [loading, setLoading] = useState(true);

    // Fetch sites on mount
    useEffect(() => {
        fetchSites();
    }, []);

    // Update currentSite when currentSiteId changes
    useEffect(() => {
        if (currentSiteId && sites.length > 0) {
            const site = sites.find(s => s.site_id === currentSiteId);
            setCurrentSite(site || null);
        }
    }, [currentSiteId, sites]);

    const fetchSites = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_BASE}/config/sites`);
            const siteList = Array.isArray(response.data) ? response.data : [response.data];
            setSites(siteList);

            // Auto-select first site if none selected
            if (siteList.length > 0 && !currentSiteId) {
                setCurrentSiteId(siteList[0].site_id);
                setCurrentSite(siteList[0]);
            }
        } catch (error) {
            console.error('Failed to fetch sites:', error);
            // Set demo fallback if API fails
            const fallback = { site_id: 'demo-site', name: 'Demo Mine Site' };
            setSites([fallback]);
            setCurrentSiteId('demo-site');
            setCurrentSite(fallback);
        } finally {
            setLoading(false);
        }
    };

    const selectSite = (siteId) => {
        setCurrentSiteId(siteId);
    };

    const value = {
        sites,
        currentSiteId,
        currentSite,
        loading,
        selectSite,
        refreshSites: fetchSites
    };

    return (
        <SiteContext.Provider value={value}>
            {children}
        </SiteContext.Provider>
    );
};

export default SiteContext;
