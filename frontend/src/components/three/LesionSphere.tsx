import { Html, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo, useState } from "react";
import type { Vector3Tuple } from "three";

import LesionLegend from "../diagnosis/LesionLegend";
import { LESION_COLORS, LESION_LABELS, LESION_ORDER, type DiagnosisResult } from "../../types/diagnosis";

interface Marker {
  lesion: (typeof LESION_ORDER)[number];
  position: Vector3Tuple;
  size: number;
}

interface LesionSphereProps {
  diagnosis: DiagnosisResult;
}

function seededValue(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function toSpherePoint(index: number, total: number, seed: number): Vector3Tuple {
  const offset = 2 / Math.max(total, 1);
  const y = 1 - (index + 0.5) * offset;
  const radius = Math.sqrt(Math.max(1 - y * y, 0));
  const theta = (index * Math.PI * (3 - Math.sqrt(5))) + seededValue(seed) * Math.PI * 0.6;
  return [radius * Math.cos(theta), y, radius * Math.sin(theta)];
}

function buildMarkers(diagnosis: DiagnosisResult): Marker[] {
  const markers: Marker[] = [];
  LESION_ORDER.forEach((lesion, lesionIndex) => {
    const count = Math.min(Math.max(diagnosis.lesion_counts[lesion], 0), 48);
    const area = diagnosis.lesion_areas[lesion];
    const markerTotal = count > 0 ? Math.max(1, Math.min(count, 18)) : area > 0 ? 1 : 0;
    for (let index = 0; index < markerTotal; index += 1) {
      markers.push({
        lesion,
        position: toSpherePoint(index + lesionIndex * 19, markerTotal + 60, diagnosis.id + lesionIndex * 13),
        size: Math.max(0.045, Math.min(0.13, 0.045 + area * 0.018)),
      });
    }
  });
  return markers;
}

function Scene({ diagnosis }: LesionSphereProps) {
  const [active, setActive] = useState<Marker | null>(null);
  const markers = useMemo(() => buildMarkers(diagnosis), [diagnosis]);

  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight position={[3, 4, 5]} intensity={1.35} />
      <mesh>
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial color="#c8d0dc" transparent opacity={0.24} roughness={0.62} />
      </mesh>
      <mesh>
        <sphereGeometry args={[1.01, 48, 48]} />
        <meshBasicMaterial color="#49627f" wireframe transparent opacity={0.12} />
      </mesh>
      {markers.map((marker, index) => (
        <mesh
          key={`${marker.lesion}-${index}`}
          position={marker.position.map((value) => value * 1.08) as Vector3Tuple}
          onPointerOver={(event) => {
            event.stopPropagation();
            setActive(marker);
          }}
          onPointerOut={() => setActive(null)}
        >
          <boxGeometry args={[marker.size, marker.size, marker.size]} />
          <meshStandardMaterial color={LESION_COLORS[marker.lesion]} roughness={0.35} />
        </mesh>
      ))}
      {active ? (
        <Html position={active.position.map((value) => value * 1.32) as Vector3Tuple} center>
          <div className="lesion-tooltip">
            <strong>{LESION_LABELS[active.lesion]}</strong>
            <span>{diagnosis.lesion_counts[active.lesion]} 处</span>
            <span>{diagnosis.lesion_areas[active.lesion].toFixed(4)}%</span>
          </div>
        </Html>
      ) : null}
      <OrbitControls enablePan={false} minDistance={2.1} maxDistance={4.4} />
    </>
  );
}

export default function LesionSphere({ diagnosis }: LesionSphereProps) {
  return (
    <div className="lesion-sphere">
      <div className="sphere-legend">
        <LesionLegend />
      </div>
      <Canvas camera={{ position: [0, 0.2, 3.1], fov: 45 }}>
        <Scene diagnosis={diagnosis} />
      </Canvas>
      <div className="sphere-summary">
        {LESION_ORDER.map((lesion) => (
          <span key={lesion}>
            {LESION_LABELS[lesion]} {diagnosis.lesion_counts[lesion]} / {diagnosis.lesion_areas[lesion].toFixed(3)}%
          </span>
        ))}
      </div>
    </div>
  );
}
