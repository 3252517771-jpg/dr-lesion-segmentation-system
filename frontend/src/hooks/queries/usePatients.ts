import { useQuery } from "@tanstack/react-query";

import { getPatient, getPatients } from "../../api/patients";

export function usePatients(params?: { page?: number; size?: number; search?: string }) {
  return useQuery({
    queryKey: ["patients", params],
    queryFn: () => getPatients({ size: 100, ...params }),
  });
}

export function usePatient(id: number) {
  return useQuery({ queryKey: ["patient", id], queryFn: () => getPatient(id), enabled: Number.isFinite(id) });
}
