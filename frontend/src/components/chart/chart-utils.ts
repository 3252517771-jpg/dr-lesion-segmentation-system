import { LESION_COLORS, LESION_LABELS, LESION_ORDER, type LesionKey } from "../../types/diagnosis";
import type { LesionFrequency, TrendPoint } from "../../types/stats";

export interface OrderedLesionFrequency {
  lesion: LesionKey;
  label: string;
  color: string;
  count: number;
  percentage: number;
  totalCount: number;
  totalArea: number;
}

export interface PieSlice extends OrderedLesionFrequency {
  ratio: number;
  startRatio: number;
  endRatio: number;
}

export interface TooltipPayload {
  marker?: string;
  seriesName?: string;
  value?: unknown;
}

export interface ParametricEquation {
  u: {
    min: number;
    max: number;
    step: number;
  };
  v: {
    min: number;
    max: number;
    step: number;
  };
  x: (u: number, v: number) => number;
  y: (u: number, v: number) => number;
  z: (u: number, v: number) => number;
}

function isLesionKey(value: string): value is LesionKey {
  return (LESION_ORDER as readonly string[]).includes(value);
}

export function getOrderedFrequencyData(data: LesionFrequency[] = []): OrderedLesionFrequency[] {
  const lookup = data.reduce<Partial<Record<LesionKey, LesionFrequency>>>((accumulator, item) => {
    if (isLesionKey(item.lesion_type)) {
      accumulator[item.lesion_type] = item;
    }
    return accumulator;
  }, {});

  return LESION_ORDER.map((lesion) => ({
    lesion,
    label: LESION_LABELS[lesion],
    color: LESION_COLORS[lesion],
    count: Number(lookup[lesion]?.count ?? 0),
    percentage: Number(lookup[lesion]?.percentage ?? 0),
    totalCount: Number(lookup[lesion]?.total_count ?? 0),
    totalArea: Number(lookup[lesion]?.total_area ?? 0),
  }));
}

export function hasFrequencySignal(data: OrderedLesionFrequency[]) {
  return data.some((item) => item.totalCount > 0 || item.totalArea > 0);
}

export function hasTrendSignal(data: TrendPoint[] = []) {
  return data.some((point) => LESION_ORDER.some((lesion) => Number(point[lesion]) > 0));
}

export function formatPercent(value: number, digits = 1) {
  return `${value.toFixed(digits)}%`;
}

export function formatArea(value: number) {
  return `${value.toFixed(4)}%`;
}

export function compactDate(dateText: string) {
  return dateText.length >= 10 ? dateText.slice(5, 10) : dateText;
}

export function getTooltipPayload(params: unknown): TooltipPayload {
  const payload = Array.isArray(params) ? params[0] : params;
  if (payload && typeof payload === "object") {
    return payload as TooltipPayload;
  }
  return {};
}

export function buildPieSlices(data: OrderedLesionFrequency[]): PieSlice[] {
  const total = data.reduce((sum, item) => sum + item.totalCount, 0);
  let cursor = 0;

  return data.map((item) => {
    const ratio = total > 0 ? item.totalCount / total : 0;
    const slice = {
      ...item,
      ratio,
      startRatio: cursor,
      endRatio: cursor + ratio,
    };
    cursor += ratio;
    return slice;
  });
}

export function createPieParametricEquation(startRatio: number, endRatio: number, height: number): ParametricEquation {
  const startRadian = startRatio * Math.PI * 2;
  const endRadian = endRatio * Math.PI * 2;
  const innerDiameterRatio = 0.54;
  const ringThickness = (1 - innerDiameterRatio) / (1 + innerDiameterRatio);

  return {
    u: {
      min: -Math.PI,
      max: Math.PI * 3,
      step: Math.PI / 60,
    },
    v: {
      min: 0,
      max: Math.PI * 2,
      step: Math.PI / 24,
    },
    x: (u: number, v: number) => {
      const angle = Math.min(Math.max(u, startRadian), endRadian);
      return Math.cos(angle) * (1 + Math.cos(v) * ringThickness);
    },
    y: (u: number, v: number) => {
      const angle = Math.min(Math.max(u, startRadian), endRadian);
      return Math.sin(angle) * (1 + Math.cos(v) * ringThickness);
    },
    z: (_u: number, v: number) => (Math.sin(v) > 0 ? height : -0.05),
  };
}
