import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createPatient } from "../../api/patients";
import type { PatientCreate } from "../../types/patient";

export function useCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PatientCreate) => createPatient(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["patients"] }),
  });
}
