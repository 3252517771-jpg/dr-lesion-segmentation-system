import client from "./client";
import type { DiagnosisListResponse, DiagnosisResult, DiagnoseResponse } from "../types/diagnosis";

export async function diagnoseImage(patientId: number, file: File): Promise<DiagnoseResponse> {
  const formData = new FormData();
  formData.append("patient_id", String(patientId));
  formData.append("image", file);
  const response = await client.post<DiagnoseResponse>("/diagnose", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getDiagnoses(params?: { page?: number; size?: number; patient_id?: number }): Promise<DiagnosisListResponse> {
  const response = await client.get<DiagnosisListResponse>("/diagnoses", { params });
  return response.data;
}

export async function getDiagnosis(id: number): Promise<DiagnosisResult> {
  const response = await client.get<{ diagnosis: DiagnosisResult }>(`/diagnoses/${id}`);
  return response.data.diagnosis;
}

export async function updateDiagnosisNotes(id: number, notes: string): Promise<DiagnosisResult> {
  const response = await client.put<{ diagnosis: DiagnosisResult }>(`/diagnoses/${id}`, { notes });
  return response.data.diagnosis;
}
