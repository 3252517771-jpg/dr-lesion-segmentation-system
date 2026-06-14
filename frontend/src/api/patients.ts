import client from "./client";
import type { Patient, PatientCreate, PatientListResponse, PatientUpdate } from "../types/patient";

export async function getPatients(params?: { page?: number; size?: number; search?: string }): Promise<PatientListResponse> {
  const response = await client.get<PatientListResponse>("/patients", { params });
  return response.data;
}

export async function getPatient(id: number): Promise<Patient> {
  const response = await client.get<{ patient: Patient }>(`/patients/${id}`);
  return response.data.patient;
}

export async function createPatient(data: PatientCreate): Promise<Patient> {
  const response = await client.post<{ patient: Patient }>("/patients", data);
  return response.data.patient;
}

export async function updatePatient(id: number, data: PatientUpdate): Promise<Patient> {
  const response = await client.put<{ patient: Patient }>(`/patients/${id}`, data);
  return response.data.patient;
}

export async function deletePatient(id: number): Promise<void> {
  await client.delete(`/patients/${id}`);
}
