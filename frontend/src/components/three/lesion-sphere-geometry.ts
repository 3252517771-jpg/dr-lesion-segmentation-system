import {
  CanvasTexture,
  LinearFilter,
  Matrix4,
  Quaternion,
  SRGBColorSpace,
  Vector3,
  type Vector3Tuple,
} from "three";

import { LESION_COLORS, LESION_ORDER, type DiagnosisResult, type LesionKey } from "../../types/diagnosis";

export type SeverityLevel = "low" | "medium" | "high";

export const SEVERITY_LABELS: Record<SeverityLevel, string> = {
  low: "低",
  medium: "中",
  high: "高",
};

export interface LesionPoint {
  lesion: LesionKey;
  u: number;
  v: number;
  radius: number;
  height: number;
  severity: SeverityLevel;
  areaRatio: number;
  aspect: number;
  rotation: number;
  seed: number;
  position: Vector3Tuple;
}

export interface PillarSpec {
  point: LesionPoint;
  position: Vector3Tuple;
  height: number;
  radius: number;
}

export type PillarBatches = Record<LesionKey, PillarSpec[]>;

function seededValue(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function normalizeAreaRatio(value: number) {
  return Math.max(0.004, Math.min(value > 1 ? value / 100 : value, 0.08));
}

function mapImageToVisibleSphereU(x: number) {
  return 0.25 + (x - 0.5) * 0.72;
}

function toSpherePoint(u: number, v: number): Vector3Tuple {
  const phi = u * Math.PI * 2;
  const theta = v * Math.PI;
  return [-Math.sin(theta) * Math.cos(phi), Math.cos(theta), Math.sin(theta) * Math.sin(phi)];
}

function getSeverity(areaRatio: number): SeverityLevel {
  if (areaRatio >= 0.045) return "high";
  if (areaRatio >= 0.018) return "medium";
  return "low";
}

function getHeight(areaRatio: number) {
  return clamp(0.02 + Math.sqrt(areaRatio) * 0.22, 0.026, 0.082);
}

function getMaxComponents(lesion: LesionKey) {
  if (lesion === "MA") return 28;
  if (lesion === "HE") return 16;
  if (lesion === "EX") return 14;
  return 12;
}

export function buildLesionPoints(diagnosis: DiagnosisResult): LesionPoint[] {
  const points: LesionPoint[] = [];

  LESION_ORDER.forEach((lesion) => {
    const measuredPositions = diagnosis.lesion_positions?.[lesion] ?? [];
    measuredPositions
      .filter((position) => position.area >= 12 || position.area_ratio >= 0.008)
      .sort((left, right) => right.area - left.area)
      .slice(0, getMaxComponents(lesion))
      .forEach((position) => {
        const areaRatio = normalizeAreaRatio(position.area_ratio);
        const bboxWidth = Math.max(position.bbox?.[2] ?? 12, 4);
        const bboxHeight = Math.max(position.bbox?.[3] ?? 12, 4);
        const u = clamp(mapImageToVisibleSphereU(position.x), 0.04, 0.46);
        const v = clamp(0.5 + (position.y - 0.5) * 0.9, 0.12, 0.88);

        points.push({
          lesion,
          u,
          v,
          radius: clamp((Math.max(bboxWidth, bboxHeight) / 512) * 0.36 + Math.sqrt(areaRatio) * 0.018, 0.008, 0.024),
          height: getHeight(areaRatio),
          severity: getSeverity(areaRatio),
          areaRatio,
          aspect: clamp(bboxWidth / bboxHeight, 0.62, 1.8),
          rotation: seededValue(position.x * 997 + position.y * 619) * Math.PI,
          seed: position.x * 997 + position.y * 619,
          position: toSpherePoint(u, v),
        });
      });
  });

  return points;
}

function getContourWobble(point: LesionPoint, angle: number) {
  return 1 + Math.sin(angle * 3 + point.seed * 0.013) * 0.12 + Math.cos(angle * 5 + point.seed * 0.021) * 0.08;
}

function rotateLocal(localX: number, localY: number, rotation: number) {
  return {
    x: localX * Math.cos(rotation) - localY * Math.sin(rotation),
    y: localX * Math.sin(rotation) + localY * Math.cos(rotation),
  };
}

function traceLesionPath(context: CanvasRenderingContext2D, point: LesionPoint, x: number, y: number, radius: number) {
  const pointsOnContour = 34;
  context.beginPath();
  for (let index = 0; index <= pointsOnContour; index += 1) {
    const t = (index / pointsOnContour) * Math.PI * 2;
    const wobble = getContourWobble(point, t);
    const localX = Math.cos(t) * radius * point.aspect * wobble;
    const localY = Math.sin(t) * radius * wobble;
    const rotated = rotateLocal(localX, localY, point.rotation);
    if (index === 0) {
      context.moveTo(x + rotated.x, y + rotated.y);
    } else {
      context.lineTo(x + rotated.x, y + rotated.y);
    }
  }
  context.closePath();
}

export function createBoundaryTexture(points: LesionPoint[]) {
  const size = 1024;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");

  if (!context) {
    return null;
  }

  context.clearRect(0, 0, size, size);
  points.forEach((point) => {
    const x = point.u * size;
    const y = point.v * size;
    const radius = point.radius * size;
    const color = LESION_COLORS[point.lesion];

    traceLesionPath(context, point, x, y, radius);
    context.fillStyle = `${color}20`;
    context.fill();

    traceLesionPath(context, point, x, y, radius);
    context.strokeStyle = "rgba(255,255,255,0.92)";
    context.lineWidth = 5;
    context.lineJoin = "round";
    context.lineCap = "round";
    context.stroke();

    traceLesionPath(context, point, x, y, radius);
    context.strokeStyle = color;
    context.lineWidth = 3;
    context.stroke();
  });

  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  texture.minFilter = LinearFilter;
  texture.magFilter = LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

export function createOrientationTexture() {
  const size = 1024;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");

  if (!context) {
    return null;
  }

  const centerX = size * 0.25;
  const centerY = size * 0.5;
  const radius = size * 0.31;

  context.clearRect(0, 0, size, size);
  context.strokeStyle = "rgba(72, 91, 116, 0.26)";
  context.lineWidth = 4;
  context.setLineDash([14, 16]);
  context.beginPath();
  context.arc(centerX, centerY, radius, 0, Math.PI * 2);
  context.stroke();

  context.setLineDash([]);
  context.strokeStyle = "rgba(72, 91, 116, 0.18)";
  context.lineWidth = 3;
  context.beginPath();
  context.moveTo(centerX - radius * 0.84, centerY);
  context.lineTo(centerX + radius * 0.84, centerY);
  context.moveTo(centerX, centerY - radius * 0.84);
  context.lineTo(centerX, centerY + radius * 0.84);
  context.stroke();

  context.fillStyle = "rgba(33, 57, 93, 0.52)";
  context.font = "600 34px sans-serif";
  context.fillText("上", centerX - 17, centerY - radius - 18);
  context.fillText("鼻侧", centerX + radius + 18, centerY + 12);

  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  texture.minFilter = LinearFilter;
  texture.magFilter = LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

export function buildPillars(points: LesionPoint[]): PillarSpec[] {
  const pillars: PillarSpec[] = [];

  points.forEach((point) => {
    const columns = clamp(Math.round(10 + point.radius * 520), 10, 22);
    const rows = clamp(Math.round(columns / Math.max(point.aspect, 0.72)), 8, 20);
    const stepX = (point.radius * point.aspect * 1.86) / Math.max(columns - 1, 1);
    const stepY = (point.radius * 1.86) / Math.max(rows - 1, 1);
    const pillarRadius = clamp(Math.min(stepX, stepY) * 0.7, 0.004, 0.011);

    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const gridX = (column - (columns - 1) / 2) * stepX;
        const gridY = (row - (rows - 1) / 2) * stepY;
        const localAngle = Math.atan2(gridY, gridX / Math.max(point.aspect, 0.001));
        const boundaryScale = getContourWobble(point, localAngle);
        const normalizedDistance = Math.sqrt(
          (gridX / (point.radius * point.aspect * boundaryScale)) ** 2 +
            (gridY / (point.radius * boundaryScale)) ** 2,
        );

        if (normalizedDistance > 1) {
          continue;
        }

        const rotated = rotateLocal(gridX, gridY, point.rotation);
        const u = clamp(point.u + rotated.x, 0.035, 0.465);
        const v = clamp(point.v + rotated.y, 0.105, 0.895);
        const centerFalloff = 0.54 + (1 - normalizedDistance) * 0.52;
        const jitter = 0.96 + seededValue(point.seed + row * 53 + column * 29) * 0.08;
        const height = point.height * centerFalloff * jitter;

        pillars.push({
          point,
          position: toSpherePoint(u, v),
          height,
          radius: pillarRadius,
        });
      }
    }
  });

  return pillars;
}

export function createPillarMatrix(spec: PillarSpec) {
  const normal = new Vector3(spec.position[0], spec.position[1], spec.position[2]).normalize();
  const quaternion = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), normal);
  const position = normal.clone().multiplyScalar(1.038 + spec.height * 0.5);
  const scale = new Vector3(spec.radius, spec.height, spec.radius);
  return new Matrix4().compose(position, quaternion, scale);
}

export function buildPillarBatches(pillars: PillarSpec[]) {
  const batches = LESION_ORDER.reduce((accumulator, lesion) => {
    accumulator[lesion] = [];
    return accumulator;
  }, {} as PillarBatches);

  pillars.forEach((pillar) => {
    batches[pillar.point.lesion].push(pillar);
  });

  return batches;
}
