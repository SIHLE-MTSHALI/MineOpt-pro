import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icon in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icons
const truckIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/71/71222.png', // Placeholder or local asset later
    iconSize: [25, 25],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
});

const shovelIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/2675/2675904.png',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15]
});

const MapController = ({ center }) => {
    const map = useMap();
    useEffect(() => {
        if (center) {
            map.setView(center, map.getZoom());
        }
    }, [center, map]);
    return null;
};

export default function MineMap({ trucks, shovels, center }) {
    return (
        <MapContainer 
            center={center || [-25.8772, 29.2302]} 
            zoom={13} 
            style={{ height: '100%', width: '100%' }}
        >
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {center && <MapController center={center} />}

            {shovels.map(shovel => (
                <Marker 
                    key={`shovel-${shovel.shovel_id}`} 
                    position={[shovel.location.latitude, shovel.location.longitude]}
                    icon={shovelIcon}
                >
                    <Popup>
                        <strong>{shovel.type_name}</strong><br/>
                        ID: {shovel.shovel_id}<br/>
                        Status: {shovel.status}<br/>
                        Queue: {shovel.current_queue}
                    </Popup>
                </Marker>
            ))}

            {trucks.map(truck => (
                <Marker 
                    key={`truck-${truck.truck_id}`} 
                    position={[truck.current_location.latitude, truck.current_location.longitude]}
                    icon={truckIcon}
                >
                    <Popup>
                        <strong>{truck.type_name}</strong><br/>
                        ID: {truck.truck_id}<br/>
                        Load: {truck.current_load.toFixed(1)}t<br/>
                        Status: {truck.status}
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
}
