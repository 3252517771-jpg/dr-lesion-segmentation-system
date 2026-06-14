import { useQuery } from "@tanstack/react-query";

import { getPatient, getPatients } from "../../api/patients";

export function usePatients(search?: string) {
  return useQuery({ queryKey: ["patients", search], queryFn: () => getPatients({ size: 100, search }) });
}

export function usePatient(id: number) {
  return useQuery({ queryKey: ["patient", id], queryFn: () => getPatient(id), enabled: Number.isFinite(id) });
}
