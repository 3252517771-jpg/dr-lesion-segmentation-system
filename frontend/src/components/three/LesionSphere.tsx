import { Html, OrbitControls } from "@react-three/drei";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import { DoubleSide, InstancedMesh, MOUSE, NormalBlending } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import type { Vector3Tuple } from "three";

import { LESION_COLORS, LESION_LABELS, LESION_ORDER, type DiagnosisResult, type LesionKey } from "../../types/diagnosis";
import {
  buildLesionPoints,
  buildPillarBatches,
  buildPillars,
  createBoundaryTexture,
  createOrientationTexture,
  createPillarMatrix,
  SEVERITY_LABELS,
  type LesionPoint,
  type PillarSpec,
} from "./lesion-sphere-geometry";
import "./lesion-sphere.css";

const INITIAL_CAMERA: Vector3Tuple = [0, 0.12, 3.35];

type InteractionMode = "rotate" | "pan";
type LesionFilter = "ALL" | LesionKey;

interface LesionSphereProps {
  diagnosis: DiagnosisResult;
}

interface InstancedPillarBatchProps {
  lesion: LesionKey;
  specs: PillarSpec[];
  onActive: (point: LesionPoint | null) => void;
}

interface SceneProps extends LesionSphereProps {
  resetSignal: number;
  interactionMode: InteractionMode;
  lesionFilter: LesionFilter;
}

function InstancedPillarBatch({ lesion, specs, onActive }: InstancedPillarBatchProps) {
  const meshRef = useRef<InstancedMesh>(null);
  const matrices = useMemo(() => specs.map((spec) => createPillarMatrix(spec)), [specs]);

  useEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;

    matrices.forEach((matrix, index) => {
      mesh.setMatrixAt(index, matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
  }, [matrices]);

  if (specs.length === 0) {
    return null;
  }

  const handlePointerMove = (event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation();
    if (typeof event.instanceId === "number") {
      onActive(specs[event.instanceId]?.point ?? null);
    }
  };

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, specs.length]}
      onPointerMove={handlePointerMove}
      onPointerOut={() => onActive(null)}
    >
      <cylinderGeometry args={[1, 1, 1, 12, 1]} />
      <meshStandardMaterial color={LESION_COLORS[lesion]} roughness={0.5} metalness={0} />
    </instancedMesh>
  );
}

function CameraControls({ resetSignal, interactionMode }: { resetSignal: number; interactionMode: InteractionMode }) {
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const { camera } = useThree();
  const mouseButtons = useMemo(
    () => ({
      LEFT: interactionMode === "pan" ? MOUSE.PAN : MOUSE.ROTATE,
      MIDDLE: MOUSE.DOLLY,
      RIGHT: interactionMode === "pan" ? MOUSE.ROTATE : MOUSE.PAN,
    }),
    [interactionMode],
  );

  useEffect(() => {
    camera.position.set(...INITIAL_CAMERA);
    camera.lookAt(0, 0, 0);
    controlsRef.current?.target.set(0, 0, 0);
    controlsRef.current?.update();
  }, [camera, resetSignal]);

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      enablePan
      enableZoom
      enableRotate
      minDistance={1.75}
      maxDistance={5.2}
      panSpeed={0.72}
      rotateSpeed={0.82}
      mouseButtons={mouseButtons}
    />
  );
}

function Scene({ diagnosis, resetSignal, interactionMode, lesionFilter }: SceneProps) {
  const [active, setActive] = useState<LesionPoint | null>(null);
  const allLesionPoints = useMemo(() => buildLesionPoints(diagnosis), [diagnosis]);
  const lesionPoints = useMemo(
    () => (lesionFilter === "ALL" ? allLesionPoints : allLesionPoints.filter((point) => point.lesion === lesionFilter)),
    [allLesionPoints, lesionFilter],
  );
  const pillars = useMemo(() => buildPillars(lesionPoints), [lesionPoints]);
  const pillarBatches = useMemo(() => buildPillarBatches(pillars), [pillars]);
  const boundaryTexture = useMemo(() => createBoundaryTexture(lesionPoints), [lesionPoints]);
  const orientationTexture = useMemo(() => createOrientationTexture(), []);

  return (
    <>
      <ambientLight intensity={0.66} />
      <directionalLight position={[3, 4, 5]} intensity={0.9} />
      <mesh>
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial color="#d8dde5" transparent opacity={0.24} roughness={0.72} />
      </mesh>
      <mesh>
        <sphereGeometry args={[1.01, 48, 48]} />
        <meshBasicMaterial color="#5e7189" wireframe transparent opacity={0.008} />
      </mesh>
      {orientationTexture ? (
        <mesh>
          <sphereGeometry args={[1.025, 96, 96]} />
          <meshBasicMaterial
            map={orientationTexture}
            transparent
            opacity={1}
            depthWrite={false}
            blending={NormalBlending}
            side={DoubleSide}
          />
        </mesh>
      ) : null}
      {LESION_ORDER.map((lesion) => (
        <InstancedPillarBatch key={lesion} lesion={lesion} specs={pillarBatches[lesion]} onActive={setActive} />
      ))}
      {boundaryTexture && lesionPoints.length > 0 ? (
        <mesh>
          <sphereGeometry args={[1.046, 128, 128]} />
          <meshBasicMaterial
            map={boundaryTexture}
            transparent
            opacity={1}
            depthWrite={false}
            blending={NormalBlending}
            side={DoubleSide}
          />
        </mesh>
      ) : null}
      {active ? (
        <Html position={active.position.map((value) => value * 1.32) as Vector3Tuple} center>
          <div className="lesion-tooltip">
            <strong>{LESION_LABELS[active.lesion]}</strong>
            <span>{diagnosis.lesion_counts[active.lesion]} 处</span>
            <span>{diagnosis.lesion_areas[active.lesion].toFixed(4)}%</span>
            <span>高度分级：{SEVERITY_LABELS[active.severity]}</span>
          </div>
        </Html>
      ) : null}
      <CameraControls resetSignal={resetSignal} interactionMode={interactionMode} />
    </>
  );
}

export default function LesionSphere({ diagnosis }: LesionSphereProps) {
  const [resetSignal, setResetSignal] = useState(0);
  const [interactionMode, setInteractionMode] = useState<InteractionMode>("rotate");
  const [lesionFilter, setLesionFilter] = useState<LesionFilter>("ALL");
  const lesionPoints = useMemo(() => buildLesionPoints(diagnosis), [diagnosis]);

  return (
    <div className={`lesion-sphere is-${interactionMode}-mode`}>
      <div className="sphere-legend" aria-label="病灶视图筛选">
        <button
          className={lesionFilter === "ALL" ? "is-active" : ""}
          type="button"
          onClick={() => setLesionFilter("ALL")}
        >
          全部
        </button>
        {LESION_ORDER.map((lesion) => (
          <button
            key={lesion}
            className={lesionFilter === lesion ? "is-active" : ""}
            type="button"
            onClick={() => setLesionFilter(lesion)}
          >
            <span className="sphere-legend-dot" style={{ background: LESION_COLORS[lesion] }} />
            {LESION_LABELS[lesion]}
          </button>
        ))}
      </div>
      <div className="sphere-mode-switch" aria-label="3D 交互模式">
        <button
          className={interactionMode === "rotate" ? "is-active" : ""}
          type="button"
          onClick={() => setInteractionMode("rotate")}
        >
          旋转
        </button>
        <button className={interactionMode === "pan" ? "is-active" : ""} type="button" onClick={() => setInteractionMode("pan")}>
          平移
        </button>
      </div>
      <button className="sphere-reset-button" type="button" onClick={() => setResetSignal((value) => value + 1)}>
        重置视角
      </button>
      <div className="sphere-orientation-note">
        {interactionMode === "pan" ? "平移模式：左键拖动画布移动整个球体，滚轮缩放" : "旋转模式：左键拖动旋转球体，滚轮缩放"}
      </div>
      {lesionPoints.length === 0 ? (
        <div className="sphere-empty-note">该诊断记录缺少真实 3D 病灶坐标，请重新诊断后查看对应分布</div>
      ) : null}
      <Canvas className="sphere-canvas" camera={{ position: INITIAL_CAMERA, fov: 42 }}>
        <Scene diagnosis={diagnosis} resetSignal={resetSignal} interactionMode={interactionMode} lesionFilter={lesionFilter} />
      </Canvas>
      <div className="sphere-summary">
        {(lesionFilter === "ALL" ? LESION_ORDER : [lesionFilter]).map((lesion) => (
          <span key={lesion}>
            {LESION_LABELS[lesion]} {diagnosis.lesion_counts[lesion]} / {diagnosis.lesion_areas[lesion].toFixed(3)}%
          </span>
        ))}
      </div>
    </div>
  );
}
