import { useMutation, useQueryClient } from "@tanstack/react-query";

import { diagnoseImage } from "../../api/diagnoses";

export function useDiagnose() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ patientId, file }: { patientId: number; file: File }) => diagnoseImage(patientId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["diagnoses"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });
}
