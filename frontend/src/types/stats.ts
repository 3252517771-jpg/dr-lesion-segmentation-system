export interface StatsOverview {
  total_diagnoses: number;
  today_diagnoses: number;
  total_patients: number;
}

export interface LesionFrequency {
  lesion_type: string;
  count: number;
  percentage: number;
  total_count: number;
  total_area: number;
}

export interface LesionFrequencyResponse {
  lesion_frequencies: LesionFrequency[];
}

export interface TrendPoint {
  date: string;
  HE: number;
  EX: number;
  MA: number;
  SE: number;
}

export interface TrendResponse {
  dates: string[];
  trend: TrendPoint[];
}
