export interface LesionStats {
  HE: number;
  EX: number;
  MA: number;
  SE: number;
}

export interface LesionCounts {
  HE: number;
  EX: number;
  MA: number;
  SE: number;
}

export const LESION_LABELS: Record<keyof LesionStats, string> = {
  HE: "出血",
  EX: "渗出",
  MA: "微动脉瘤",
  SE: "棉絮斑",
};

export const LESION_COLORS: Record<keyof LesionStats, string> = {
  HE: "#ff4d4f",
  EX: "#d4a106",
  MA: "#52c41a",
  SE: "#1677ff",
};

export const LESION_ORDER = ["HE", "EX", "MA", "SE"] as const;

export interface DiagnosisResult {
  id: number;
  patient_id: number;
  patient_name?: string;
  image_path: string;
  contour_path: string | null;
  image_url?: string | null;
  contour_url?: string | null;
  lesion_areas: LesionStats;
  lesion_counts: LesionCounts;
  severity: string;
  notes: string;
  created_at: string;
  updated_at?: string;
}

export interface DiagnosisListResponse {
  diagnoses: DiagnosisResult[];
  total: number;
  page: number;
  size: number;
}

export interface DiagnoseResponse {
  diagnosis: DiagnosisResult;
  mode: "placeholder" | "real";
}

export type ModelBackend = "placeholder" | "real" | "auto";

export interface HealthStatus {
  status: string;
  db: boolean;
  model_backend: ModelBackend;
  model_loaded: boolean;
  model: string | null;
  segmentation_classes: string[];
}
