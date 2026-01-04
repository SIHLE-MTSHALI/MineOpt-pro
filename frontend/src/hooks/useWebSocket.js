/**
 * useWebSocket.js - React hook for WebSocket real-time collaboration
 * 
 * Provides:
 * - Automatic connection and reconnection
 * - Presence tracking (who else is viewing)
 * - Real-time entity change notifications
 * - Editing lock coordination
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE = 'ws://localhost:8000';

/**
 * Hook for managing WebSocket connection and real-time updates
 * 
 * @param {string} userId - Current user's ID
 * @param {string} username - Current user's display name
 * @param {string} scheduleVersionId - Current schedule being viewed
 * @returns {object} WebSocket state and methods
 */
export const useWebSocket = (userId, username, scheduleVersionId) => {
    const [isConnected, setIsConnected] = useState(false);
    const [connectedUsers, setConnectedUsers] = useState([]);
    const [entityChanges, setEntityChanges] = useState([]);
    const [reconnectAttempt, setReconnectAttempt] = useState(0);

    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    // Connect to WebSocket
    const connect = useCallback(() => {
        if (!userId || !username) return;

        const wsUrl = `${WS_BASE}/ws/connect?user_id=${userId}&username=${encodeURIComponent(username)}${scheduleVersionId ? `&schedule_version_id=${scheduleVersionId}` : ''}`;

        try {
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                setReconnectAttempt(0);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse WS message', e);
                }
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);

                // Attempt to reconnect with exponential backoff
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
                reconnectTimeoutRef.current = setTimeout(() => {
                    setReconnectAttempt(prev => prev + 1);
                    connect();
                }, delay);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error', error);
            };

            wsRef.current = ws;
        } catch (e) {
            console.error('Failed to create WebSocket', e);
        }
    }, [userId, username, scheduleVersionId, reconnectAttempt]);

    // Handle incoming messages
    const handleMessage = useCallback((data) => {
        switch (data.type) {
            case 'presence_list':
                setConnectedUsers(data.users || []);
                break;

            case 'user_joined':
                setConnectedUsers(prev => [...prev, {
                    user_id: data.user_id,
                    username: data.username,
                    is_editing: false
                }]);
                break;

            case 'user_left':
                setConnectedUsers(prev =>
                    prev.filter(u => u.user_id !== data.user_id)
                );
                break;

            case 'presence_update':
                setConnectedUsers(prev =>
                    prev.map(u => u.user_id === data.user_id
                        ? { ...u, entity_type: data.entity_type, entity_id: data.entity_id, is_editing: data.is_editing }
                        : u
                    )
                );
                break;

            case 'entity_changed':
                setEntityChanges(prev => [data, ...prev].slice(0, 50));
                break;

            case 'pong':
                // Heartbeat response
                break;
        }
    }, []);

    // Connect on mount and when schedule changes
    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [scheduleVersionId]);

    // Heartbeat ping every 30 seconds
    useEffect(() => {
        if (!isConnected) return;

        const pingInterval = setInterval(() => {
            sendMessage({ type: 'ping' });
        }, 30000);

        return () => clearInterval(pingInterval);
    }, [isConnected]);

    // Send a message through the WebSocket
    const sendMessage = useCallback((message) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    }, []);

    // Switch to a different schedule
    const switchSchedule = useCallback((newScheduleId) => {
        sendMessage({
            type: 'switch_schedule',
            schedule_version_id: newScheduleId
        });
    }, [sendMessage]);

    // Notify others that we're editing an entity
    const startEditing = useCallback((entityType, entityId) => {
        sendMessage({
            type: 'start_editing',
            entity_type: entityType,
            entity_id: entityId
        });
    }, [sendMessage]);

    // Notify others that we stopped editing
    const stopEditing = useCallback(() => {
        sendMessage({ type: 'stop_editing' });
    }, [sendMessage]);

    // Check if another user is editing a specific entity
    const isBeingEdited = useCallback((entityType, entityId) => {
        return connectedUsers.some(u =>
            u.is_editing &&
            u.entity_type === entityType &&
            u.entity_id === entityId &&
            u.user_id !== userId
        );
    }, [connectedUsers, userId]);

    // Get the user editing a specific entity
    const getEditor = useCallback((entityType, entityId) => {
        return connectedUsers.find(u =>
            u.is_editing &&
            u.entity_type === entityType &&
            u.entity_id === entityId &&
            u.user_id !== userId
        );
    }, [connectedUsers, userId]);

    return {
        isConnected,
        connectedUsers,
        entityChanges,
        sendMessage,
        switchSchedule,
        startEditing,
        stopEditing,
        isBeingEdited,
        getEditor
    };
};

export default useWebSocket;
