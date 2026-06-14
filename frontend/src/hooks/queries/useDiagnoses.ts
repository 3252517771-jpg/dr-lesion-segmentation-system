import { useQuery } from "@tanstack/react-query";

import { getDiagnoses, getDiagnosis } from "../../api/diagnoses";

export function useDiagnoses(patientId?: number) {
  return useQuery({
    queryKey: ["diagnoses", patientId],
    queryFn: () => getDiagnoses({ size: 50, patient_id: patientId }),
  });
}

export function useDiagnosis(id: number) {
  return useQuery({ queryKey: ["diagnosis", id], queryFn: () => getDiagnosis(id), enabled: Number.isFinite(id) });
}
