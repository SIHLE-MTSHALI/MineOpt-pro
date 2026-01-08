/**
 * SurfaceTimelinePlayer.jsx
 * 
 * Timeline scrubber for temporal surface playback.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
    Play,
    Pause,
    SkipBack,
    SkipForward,
    Clock,
    Calendar,
    Settings,
    ChevronLeft,
    ChevronRight
} from 'lucide-react';

const SurfaceTimelinePlayer = ({
    versions = [],
    currentVersionId,
    onVersionChange,
    onCompare,
    isPlaying = false,
    onPlayPause,
    playbackSpeed = 1,
    onSpeedChange,
    className = ''
}) => {
    const [sliderValue, setSliderValue] = useState(0);
    const [showSpeedMenu, setShowSpeedMenu] = useState(false);
    const [compareMode, setCompareMode] = useState(false);
    const [compareVersionId, setCompareVersionId] = useState(null);
    const intervalRef = useRef(null);

    // Sorted versions by date
    const sortedVersions = [...versions].sort(
        (a, b) => new Date(a.version_date) - new Date(b.version_date)
    );

    // Current index
    const currentIndex = sortedVersions.findIndex(v => v.version_id === currentVersionId);

    // Update slider when version changes
    useEffect(() => {
        if (currentIndex >= 0) {
            setSliderValue(currentIndex);
        }
    }, [currentIndex]);

    // Playback loop
    useEffect(() => {
        if (isPlaying && sortedVersions.length > 0) {
            intervalRef.current = setInterval(() => {
                setSliderValue(prev => {
                    const next = prev + 1;
                    if (next >= sortedVersions.length) {
                        onPlayPause?.(false);
                        return prev;
                    }
                    onVersionChange?.(sortedVersions[next].version_id);
                    return next;
                });
            }, 2000 / playbackSpeed);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [isPlaying, playbackSpeed, sortedVersions, onVersionChange, onPlayPause]);

    const handleSliderChange = (e) => {
        const index = parseInt(e.target.value);
        setSliderValue(index);
        if (sortedVersions[index]) {
            onVersionChange?.(sortedVersions[index].version_id);
        }
    };

    const goToPrevious = () => {
        if (currentIndex > 0) {
            onVersionChange?.(sortedVersions[currentIndex - 1].version_id);
        }
    };

    const goToNext = () => {
        if (currentIndex < sortedVersions.length - 1) {
            onVersionChange?.(sortedVersions[currentIndex + 1].version_id);
        }
    };

    const goToFirst = () => {
        if (sortedVersions.length > 0) {
            onVersionChange?.(sortedVersions[0].version_id);
        }
    };

    const goToLast = () => {
        if (sortedVersions.length > 0) {
            onVersionChange?.(sortedVersions[sortedVersions.length - 1].version_id);
        }
    };

    const toggleCompareMode = () => {
        setCompareMode(!compareMode);
        if (!compareMode && currentIndex > 0) {
            setCompareVersionId(sortedVersions[currentIndex - 1].version_id);
        } else {
            setCompareVersionId(null);
            onCompare?.(null, null);
        }
    };

    const handleCompareVersionChange = (e) => {
        const versionId = e.target.value;
        setCompareVersionId(versionId);
        onCompare?.(currentVersionId, versionId);
    };

    const currentVersion = sortedVersions[currentIndex];

    const formatDate = (dateStr) => {
        if (!dateStr) return '--';
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    return (
        <div className={`surface-timeline-player ${className}`}>
            {/* Current Version Info */}
            <div className="version-info">
                <div className="version-badge">
                    <span className="version-number">v{currentVersion?.version_number || '--'}</span>
                    <span className="version-name">{currentVersion?.version_name || 'No version selected'}</span>
                </div>
                <div className="version-date">
                    <Calendar size={12} />
                    {formatDate(currentVersion?.version_date)}
                </div>
                {currentVersion?.source_type && (
                    <div className="version-source">{currentVersion.source_type}</div>
                )}
            </div>

            {/* Timeline Slider */}
            <div className="timeline-container">
                <div className="timeline-labels">
                    {sortedVersions.length > 0 && (
                        <>
                            <span className="label-start">{formatDate(sortedVersions[0]?.version_date)}</span>
                            <span className="label-end">{formatDate(sortedVersions[sortedVersions.length - 1]?.version_date)}</span>
                        </>
                    )}
                </div>

                <div className="timeline-track">
                    <input
                        type="range"
                        min={0}
                        max={Math.max(0, sortedVersions.length - 1)}
                        value={sliderValue}
                        onChange={handleSliderChange}
                        className="timeline-slider"
                    />

                    {/* Version markers */}
                    <div className="markers">
                        {sortedVersions.map((v, i) => (
                            <div
                                key={v.version_id}
                                className={`marker ${i === currentIndex ? 'active' : ''} ${v.is_approved ? 'approved' : ''}`}
                                style={{ left: `${sortedVersions.length > 1 ? (i / (sortedVersions.length - 1)) * 100 : 50}%` }}
                                title={`${v.version_name} - ${formatDate(v.version_date)}`}
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Playback Controls */}
            <div className="playback-controls">
                <button onClick={goToFirst} className="control-btn" title="First version">
                    <SkipBack size={14} />
                </button>
                <button onClick={goToPrevious} className="control-btn" title="Previous">
                    <ChevronLeft size={16} />
                </button>

                <button
                    onClick={() => onPlayPause?.(!isPlaying)}
                    className="control-btn play-btn"
                    title={isPlaying ? 'Pause' : 'Play'}
                >
                    {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                </button>

                <button onClick={goToNext} className="control-btn" title="Next">
                    <ChevronRight size={16} />
                </button>
                <button onClick={goToLast} className="control-btn" title="Last version">
                    <SkipForward size={14} />
                </button>

                {/* Speed Control */}
                <div className="speed-control">
                    <button
                        className="control-btn"
                        onClick={() => setShowSpeedMenu(!showSpeedMenu)}
                    >
                        {playbackSpeed}x
                    </button>
                    {showSpeedMenu && (
                        <div className="speed-menu">
                            {[0.5, 1, 2, 4].map(speed => (
                                <button
                                    key={speed}
                                    className={playbackSpeed === speed ? 'active' : ''}
                                    onClick={() => {
                                        onSpeedChange?.(speed);
                                        setShowSpeedMenu(false);
                                    }}
                                >
                                    {speed}x
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Compare Mode */}
            <div className="compare-section">
                <label className="compare-toggle">
                    <input
                        type="checkbox"
                        checked={compareMode}
                        onChange={toggleCompareMode}
                    />
                    <span>Compare with:</span>
                </label>

                {compareMode && (
                    <select
                        value={compareVersionId || ''}
                        onChange={handleCompareVersionChange}
                        className="compare-select"
                    >
                        <option value="">Select version...</option>
                        {sortedVersions
                            .filter(v => v.version_id !== currentVersionId)
                            .map(v => (
                                <option key={v.version_id} value={v.version_id}>
                                    v{v.version_number} - {v.version_name} ({formatDate(v.version_date)})
                                </option>
                            ))
                        }
                    </select>
                )}
            </div>

            {/* Version Count */}
            <div className="version-count">
                {currentIndex + 1} of {sortedVersions.length} versions
            </div>

            <style jsx>{`
        .surface-timeline-player {
          background: linear-gradient(145deg, #1a1a2e, #252538);
          border-radius: 12px;
          padding: 16px;
        }
        
        .version-info {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .version-badge {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .version-number {
          padding: 4px 8px;
          background: rgba(59, 130, 246, 0.2);
          border-radius: 4px;
          color: #3b82f6;
          font-size: 12px;
          font-weight: 600;
        }
        
        .version-name {
          font-weight: 600;
          color: #fff;
        }
        
        .version-date {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #888;
        }
        
        .version-source {
          padding: 2px 8px;
          background: rgba(255,255,255,0.05);
          border-radius: 4px;
          font-size: 10px;
          color: #aaa;
          text-transform: uppercase;
        }
        
        .timeline-container {
          margin-bottom: 16px;
        }
        
        .timeline-labels {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          color: #666;
          margin-bottom: 4px;
        }
        
        .timeline-track {
          position: relative;
          height: 24px;
        }
        
        .timeline-slider {
          width: 100%;
          height: 6px;
          -webkit-appearance: none;
          background: rgba(255,255,255,0.1);
          border-radius: 3px;
          cursor: pointer;
        }
        
        .timeline-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 16px;
          height: 16px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .markers {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 100%;
          pointer-events: none;
        }
        
        .marker {
          position: absolute;
          top: 50%;
          transform: translate(-50%, -50%);
          width: 8px;
          height: 8px;
          background: rgba(255,255,255,0.3);
          border-radius: 50%;
        }
        
        .marker.active {
          background: #3b82f6;
          width: 12px;
          height: 12px;
        }
        
        .marker.approved {
          border: 2px solid #22c55e;
        }
        
        .playback-controls {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
        }
        
        .control-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #aaa;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .control-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .play-btn {
          width: 40px;
          height: 40px;
          background: rgba(59,130,246,0.2);
          border-color: #3b82f6;
          color: #3b82f6;
        }
        
        .speed-control {
          position: relative;
        }
        
        .speed-menu {
          position: absolute;
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          padding: 4px;
          margin-bottom: 4px;
        }
        
        .speed-menu button {
          display: block;
          width: 100%;
          padding: 6px 12px;
          background: transparent;
          border: none;
          color: #aaa;
          font-size: 12px;
          cursor: pointer;
        }
        
        .speed-menu button.active, .speed-menu button:hover {
          background: rgba(59,130,246,0.2);
          color: #3b82f6;
        }
        
        .compare-section {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(0,0,0,0.2);
          border-radius: 8px;
          margin-bottom: 12px;
        }
        
        .compare-toggle {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #aaa;
          cursor: pointer;
        }
        
        .compare-select {
          flex: 1;
          padding: 6px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
        }
        
        .version-count {
          text-align: center;
          font-size: 11px;
          color: #666;
        }
      `}</style>
        </div>
    );
};

export default SurfaceTimelinePlayer;
