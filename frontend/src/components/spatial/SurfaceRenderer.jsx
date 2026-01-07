/**
 * SurfaceRenderer.jsx - 3D TIN Surface Visualization
 * 
 * Renders TIN (Triangulated Irregular Network) surfaces using React Three Fiber.
 * Supports:
 * - Multiple overlapping surfaces with transparency
 * - Color by elevation (gradient)
 * - Surface selection for query operations
 * - Wireframe mode toggle
 */

import React, { useMemo, useState, useRef, useCallback } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Color scale for elevation visualization
 */
const getElevationColor = (elevation, minZ, maxZ, colorScheme = 'terrain') => {
    const t = maxZ > minZ ? (elevation - minZ) / (maxZ - minZ) : 0.5;

    if (colorScheme === 'terrain') {
        // Terrain colors: blue (low) -> green -> yellow -> brown -> white (high)
        if (t < 0.2) return new THREE.Color().setHSL(0.6, 0.8, 0.3 + t * 0.5);      // Blue
        if (t < 0.4) return new THREE.Color().setHSL(0.3, 0.7, 0.35 + t * 0.4);     // Green
        if (t < 0.6) return new THREE.Color().setHSL(0.15, 0.75, 0.4 + t * 0.3);    // Yellow-green
        if (t < 0.8) return new THREE.Color().setHSL(0.08, 0.6, 0.35 + t * 0.25);   // Brown
        return new THREE.Color().setHSL(0.0, 0.0, 0.7 + t * 0.3);                    // White/gray
    } else if (colorScheme === 'seam') {
        // Coal seam colors: darker, more industrial
        return new THREE.Color().lerpColors(
            new THREE.Color(0x1a1a1a),  // Dark coal
            new THREE.Color(0x4a4a4a),  // Lighter gray
            t
        );
    } else if (colorScheme === 'design') {
        // Design surface: single color with slight variation
        return new THREE.Color().setHSL(0.55, 0.6, 0.4 + t * 0.2);
    }

    // Default gradient
    return new THREE.Color().setHSL(t * 0.3, 0.7, 0.5);
};

/**
 * Single surface mesh component
 */
const SurfaceMesh = ({
    vertices,
    triangles,
    name,
    surfaceType = 'terrain',
    opacity = 1.0,
    wireframe = false,
    selected = false,
    onClick,
    colorScheme
}) => {
    const meshRef = useRef();

    // Determine color scheme based on surface type
    const scheme = colorScheme || (
        surfaceType.includes('seam') ? 'seam' :
            surfaceType.includes('design') ? 'design' : 'terrain'
    );

    // Create geometry with vertex colors
    const geometry = useMemo(() => {
        if (!vertices || !triangles || vertices.length === 0 || triangles.length === 0) {
            return null;
        }

        const geo = new THREE.BufferGeometry();

        // Convert vertices to positions array
        const positions = [];
        const colors = [];
        const normals = [];

        // Find Z range for color mapping
        const zValues = vertices.map(v => v[2]);
        const minZ = Math.min(...zValues);
        const maxZ = Math.max(...zValues);

        // Build indexed geometry
        for (const tri of triangles) {
            const [i, j, k] = tri;

            if (i >= vertices.length || j >= vertices.length || k >= vertices.length) {
                continue;
            }

            const v0 = vertices[i];
            const v1 = vertices[j];
            const v2 = vertices[k];

            // Add vertices (unindexed for per-face normals)
            positions.push(v0[0], v0[1], v0[2]);
            positions.push(v1[0], v1[1], v1[2]);
            positions.push(v2[0], v2[1], v2[2]);

            // Calculate face normal
            const ax = v1[0] - v0[0], ay = v1[1] - v0[1], az = v1[2] - v0[2];
            const bx = v2[0] - v0[0], by = v2[1] - v0[1], bz = v2[2] - v0[2];
            const nx = ay * bz - az * by;
            const ny = az * bx - ax * bz;
            const nz = ax * by - ay * bx;
            const len = Math.sqrt(nx * nx + ny * ny + nz * nz);
            const nnx = nx / len, nny = ny / len, nnz = nz / len;

            normals.push(nnx, nny, nnz);
            normals.push(nnx, nny, nnz);
            normals.push(nnx, nny, nnz);

            // Vertex colors based on elevation
            const c0 = getElevationColor(v0[2], minZ, maxZ, scheme);
            const c1 = getElevationColor(v1[2], minZ, maxZ, scheme);
            const c2 = getElevationColor(v2[2], minZ, maxZ, scheme);

            colors.push(c0.r, c0.g, c0.b);
            colors.push(c1.r, c1.g, c1.b);
            colors.push(c2.r, c2.g, c2.b);
        }

        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        geo.computeBoundingBox();
        geo.computeBoundingSphere();

        return geo;
    }, [vertices, triangles, scheme]);

    const handleClick = useCallback((event) => {
        event.stopPropagation();
        if (onClick) {
            // Get intersection point
            const point = event.point;
            onClick({
                name,
                surfaceType,
                point: { x: point.x, y: point.y, z: point.z }
            });
        }
    }, [onClick, name, surfaceType]);

    if (!geometry) {
        return null;
    }

    return (
        <mesh
            ref={meshRef}
            geometry={geometry}
            onClick={handleClick}
        >
            <meshStandardMaterial
                vertexColors
                side={THREE.DoubleSide}
                transparent={opacity < 1}
                opacity={opacity}
                wireframe={wireframe}
                emissive={selected ? new THREE.Color(0x3366ff) : new THREE.Color(0x000000)}
                emissiveIntensity={selected ? 0.2 : 0}
            />
        </mesh>
    );
};

/**
 * Contour lines component
 */
const ContourLines = ({ contours, color = '#ffffff', lineWidth = 1 }) => {
    const linesRef = useRef();

    const geometry = useMemo(() => {
        if (!contours || contours.length === 0) {
            return null;
        }

        const positions = [];

        for (const contour of contours) {
            const pts = contour.points || [];
            for (let i = 0; i < pts.length - 1; i += 2) {
                // Points come in pairs from triangle edges
                positions.push(pts[i][0], pts[i][1], pts[i][2]);
                if (i + 1 < pts.length) {
                    positions.push(pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]);
                }
            }
        }

        if (positions.length === 0) {
            return null;
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        return geo;
    }, [contours]);

    if (!geometry) {
        return null;
    }

    return (
        <lineSegments ref={linesRef} geometry={geometry}>
            <lineBasicMaterial color={color} linewidth={lineWidth} />
        </lineSegments>
    );
};

/**
 * Main SurfaceRenderer component
 */
const SurfaceRenderer = ({
    surfaces = [],
    selectedSurfaceId = null,
    showWireframe = false,
    showContours = false,
    contours = [],
    opacity = 1.0,
    onSurfaceClick,
    colorScheme
}) => {
    return (
        <group name="surfaces">
            {surfaces.map((surface) => (
                <SurfaceMesh
                    key={surface.surface_id || surface.name}
                    vertices={surface.vertices}
                    triangles={surface.triangles}
                    name={surface.name}
                    surfaceType={surface.surface_type}
                    opacity={opacity}
                    wireframe={showWireframe}
                    selected={surface.surface_id === selectedSurfaceId}
                    onClick={onSurfaceClick}
                    colorScheme={colorScheme}
                />
            ))}

            {showContours && contours.length > 0 && (
                <ContourLines contours={contours} />
            )}
        </group>
    );
};

export default SurfaceRenderer;
export { SurfaceMesh, ContourLines, getElevationColor };
