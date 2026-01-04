/**
 * PresenceIndicator.jsx - Shows who else is viewing/editing
 * 
 * Displays:
 * - Avatars of connected users
 * - Editing status indicators
 * - User count badge
 */

import React from 'react';
import { Users, Edit3, Eye } from 'lucide-react';

/**
 * Avatar component showing user initials
 */
const UserAvatar = ({ username, isEditing, entityType }) => {
    const initials = username
        .split(' ')
        .map(part => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);

    // Generate consistent color from username
    const hashCode = username.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
    }, 0);

    const colors = [
        'bg-blue-500', 'bg-green-500', 'bg-purple-500',
        'bg-orange-500', 'bg-pink-500', 'bg-teal-500'
    ];
    const bgColor = colors[Math.abs(hashCode) % colors.length];

    return (
        <div className="relative group">
            <div
                className={`w-8 h-8 rounded-full ${bgColor} flex items-center justify-center text-white text-xs font-bold ring-2 ring-slate-900`}
                title={`${username}${isEditing ? ` (editing ${entityType})` : ''}`}
            >
                {initials}
            </div>

            {/* Status indicator */}
            {isEditing ? (
                <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-amber-400 rounded-full flex items-center justify-center ring-2 ring-slate-900">
                    <Edit3 size={8} className="text-slate-900" />
                </div>
            ) : (
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full ring-2 ring-slate-900" />
            )}

            {/* Tooltip */}
            <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                {username}
                {isEditing && <span className="text-amber-300 ml-1">editing {entityType}</span>}
            </div>
        </div>
    );
};

/**
 * Main presence indicator component
 */
const PresenceIndicator = ({
    connectedUsers = [],
    isConnected = false,
    maxDisplay = 4
}) => {
    // Filter out current user (will be handled by the hook)
    const displayUsers = connectedUsers.slice(0, maxDisplay);
    const overflowCount = Math.max(0, connectedUsers.length - maxDisplay);

    if (connectedUsers.length === 0) {
        return (
            <div className="flex items-center gap-2 text-slate-500 text-sm">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
                <span>{isConnected ? 'Connected' : 'Offline'}</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-2">
            {/* Connection status */}
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />

            {/* User avatars */}
            <div className="flex -space-x-2">
                {displayUsers.map(user => (
                    <UserAvatar
                        key={user.user_id}
                        username={user.username}
                        isEditing={user.is_editing}
                        entityType={user.entity_type}
                    />
                ))}

                {/* Overflow count */}
                {overflowCount > 0 && (
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white text-xs font-bold ring-2 ring-slate-900">
                        +{overflowCount}
                    </div>
                )}
            </div>

            {/* Count label */}
            <span className="text-slate-400 text-xs ml-1">
                {connectedUsers.length} online
            </span>
        </div>
    );
};

/**
 * Compact badge version for headers
 */
export const PresenceBadge = ({ count, isConnected }) => {
    if (count === 0) return null;

    return (
        <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800 rounded-full text-xs">
            <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            <Users size={12} className="text-slate-400" />
            <span className="text-slate-300">{count}</span>
        </div>
    );
};

/**
 * Entity lock indicator
 */
export const EditLockIndicator = ({ editor }) => {
    if (!editor) return null;

    return (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-900/50 border border-amber-700 rounded text-xs text-amber-200">
            <Edit3 size={12} />
            <span>{editor.username} is editing this</span>
        </div>
    );
};

export default PresenceIndicator;
