import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const Truck = ({ startPos, endPos, color, speed = 0.5, offset = 0 }) => {
    const mesh = useRef();
    const progress = useRef(offset);

    useFrame((state, delta) => {
        if (!mesh.current) return;

        // Update progress (looped 0 to 1)
        progress.current += (delta * speed) * 0.1; // Slow down
        if (progress.current > 1) progress.current = 0;

        // Lerp Position
        // Simple straight line for now
        // Could enable "Arc" by adding Y offset based on Sine of progress
        const p = progress.current;

        // Vector Math
        const vStart = new THREE.Vector3(...startPos);
        const vEnd = new THREE.Vector3(...endPos);

        const currentPos = new THREE.Vector3().lerpVectors(vStart, vEnd, p);

        // Add a little "Arc" jump for fun (simulating going up ramp?)
        // currentPos.y += Math.sin(p * Math.PI) * 5; 

        mesh.current.position.copy(currentPos);
        mesh.current.lookAt(vEnd); // Face destination
    });

    return (
        <mesh ref={mesh} castShadow>
            <boxGeometry args={[3, 2, 5]} /> {/* Truck Shape */}
            <meshStandardMaterial color={color} />
        </mesh>
    );
};

const HaulageRenderer = ({ activeTasks = [], activityAreas = [], stockpiles = [] }) => {
    const routes = useMemo(() => {
        const r = [];

        // Map data for fast lookup
        const areaMap = new Map(activityAreas.map(a => [a.area_id, a]));

        // Hardcoded Destinations (Dumps/Stockpiles) if not in DB yet
        // Ideally fetch 'flowNodes' but we can use stockpiles for Coal
        const wasteDumpPos = [-50, 0, -50]; // Left side
        const romPadPos = [150, 0, -50]; // Right side (default)

        if (stockpiles.length > 0) {
            // Use first stockpile as ROM for demo
            // romPadPos = ... 
            // Keeping simple logic for now
        }

        activeTasks.forEach((task, i) => {
            const area = areaMap.get(task.activity_area_id);
            if (!area) return;

            const startPos = area.geometry.position; // [x, y, z]

            // Logic: Is it Coal or Waste?
            // We need to look at slices, but for MVP let's guess based on existing slices
            // Or use the Task's planned quantity?
            // Let's assume if slice contains "Coal" -> ROM, else Waste
            const isCoal = area.slice_states?.[0]?.material === 'Coal';

            const endPos = isCoal ? romPadPos : wasteDumpPos;
            const color = isCoal ? "#fbbf24" : "#ef4444"; // Yellow trucks for Coal, Red for Waste (or White trucks with colored payload)

            // Spawn 3 trucks per task
            for (let j = 0; j < 3; j++) {
                r.push({
                    id: `${task.task_id}-${j}`,
                    startPos,
                    endPos,
                    color: "white", // Standard White Truck
                    payloadColor: isCoal ? "black" : "brown",
                    offset: Math.random(), // Stagger start
                    speed: 0.5 + Math.random() * 0.5 // Random speed
                });
            }
        });

        return r;
    }, [activeTasks, activityAreas]);

    if (routes.length === 0) return null;

    return (
        <group>
            {routes.map(truck => (
                <Truck
                    key={truck.id}
                    startPos={truck.startPos}
                    endPos={truck.endPos}
                    color={truck.color}
                    speed={truck.speed}
                    offset={truck.offset}
                />
            ))}
        </group>
    );
};

export default HaulageRenderer;
