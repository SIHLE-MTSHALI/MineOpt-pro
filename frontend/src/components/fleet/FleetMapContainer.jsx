/**
 * FleetMapContainer.jsx
 * 
 * Container component that fetches fleet positions and renders FleetMapOverlay
 * with automatic polling for position updates.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { fleetAPI } from '../../services/api';
import FleetMapOverlay from './FleetMapOverlay';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Polling interval in milliseconds
const POLL_INTERVAL = 5000;

const FleetMapContainer = ({ siteId }) => {
    const [positions, setPositions] = useState([]);
    const [selectedEquipmentId, setSelectedEquipmentId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const pollRef = useRef(null);

    const fetchPositions = useCallback(async () => {
        if (!siteId) return;

        try {
            setIsLoading(true);
            const data = await fleetAPI.getPositions(siteId);
            setPositions(Array.isArray(data) ? data : []);
            setError(null);
        } catch (err) {
            console.warn('Failed to fetch fleet positions:', err);
            setError('Unable to load fleet positions');
            // Keep existing positions on error
        } finally {
            setIsLoading(false);
        }
    }, [siteId]);

    // Initial fetch and setup polling
    useEffect(() => {
        fetchPositions();

        // Setup polling
        pollRef.current = setInterval(fetchPositions, POLL_INTERVAL);

        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
            }
        };
    }, [fetchPositions]);

    // Default map bounds (South Africa mining region)
    const mapBounds = {
        minLat: -26.5,
        maxLat: -26.0,
        minLon: 27.5,
        maxLon: 28.0,
        width: 800,
        height: 600
    };

    // If no positions yet, show placeholder map
    if (positions.length === 0 && !isLoading) {
        return (
            <div className="h-full flex items-center justify-center bg-slate-800/50 rounded-xl border border-slate-700">
                <div className="text-center p-8">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-400">
                            <circle cx="12" cy="10" r="3" />
                            <path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 6.9 8 11.7z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-300 mb-2">No Fleet Positions</h3>
                    <p className="text-sm text-slate-400">
                        {error || 'No equipment positions available. Equipment GPS data will appear here when available.'}
                    </p>
                    <button
                        onClick={fetchPositions}
                        className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full relative bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
            {/* Map Container */}
            <div className="absolute inset-0">
                <MapContainer
                    center={[-26.2, 27.8]}
                    zoom={13}
                    style={{ height: '100%', width: '100%' }}
                    className="leaflet-dark"
                >
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    />

                    {/* Equipment markers would be rendered here as Leaflet markers */}
                    {positions.map(pos => {
                        if (!pos.latitude || !pos.longitude) return null;
                        return (
                            <EquipmentMarker
                                key={pos.equipment_id}
                                position={pos}
                                isSelected={selectedEquipmentId === pos.equipment_id}
                                onClick={() => setSelectedEquipmentId(pos.equipment_id)}
                            />
                        );
                    })}
                </MapContainer>
            </div>

            {/* Overlay Controls */}
            <FleetMapOverlay
                siteId={siteId}
                positions={positions}
                selectedEquipmentId={selectedEquipmentId}
                onSelectEquipment={setSelectedEquipmentId}
                onRefresh={fetchPositions}
                isLoading={isLoading}
                mapBounds={mapBounds}
            />

            {/* Loading indicator */}
            {isLoading && (
                <div className="absolute top-4 left-4 bg-slate-900/80 px-3 py-1.5 rounded-full text-xs text-slate-300 flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                    Updating...
                </div>
            )}
        </div>
    );
};

// Simple equipment marker component
const EquipmentMarker = ({ position, isSelected, onClick }) => {
    const map = useMap();

    useEffect(() => {
        // Create a custom marker using Leaflet
        if (!window.L) return;

        const marker = window.L.circleMarker([position.latitude, position.longitude], {
            radius: isSelected ? 12 : 8,
            fillColor: getStatusColor(position.status),
            color: '#fff',
            weight: isSelected ? 3 : 1,
            opacity: 1,
            fillOpacity: 0.9
        });

        marker.bindPopup(`
            <div style="min-width: 150px;">
                <strong>${position.fleet_number || 'Unknown'}</strong><br/>
                Type: ${position.equipment_type?.replace(/_/g, ' ') || 'N/A'}<br/>
                Status: ${position.status || 'Unknown'}<br/>
                Speed: ${position.speed_kmh?.toFixed(1) || 0} km/h
            </div>
        `);

        marker.on('click', onClick);
        marker.addTo(map);

        return () => {
            map.removeLayer(marker);
        };
    }, [map, position, isSelected, onClick]);

    return null;
};

const getStatusColor = (status) => {
    const colors = {
        operating: '#22c55e',
        standby: '#eab308',
        maintenance: '#3b82f6',
        breakdown: '#ef4444',
        refueling: '#f97316',
        shift_change: '#8b5cf6',
        off_site: '#6b7280'
    };
    return colors[status] || '#888';
};

export default FleetMapContainer;
