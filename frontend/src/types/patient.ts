export interface Patient {
  id: number;
  name: string;
  gender: string;
  age: number;
  patient_id: string;
  diagnosis_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface PatientCreate {
  name: string;
  gender: string;
  age: number;
  patient_id: string;
}

export interface PatientUpdate {
  name?: string;
  gender?: string;
  age?: number;
  patient_id?: string;
}

export interface PatientListResponse {
  patients: Patient[];
  total: number;
  page: number;
  size: number;
}
