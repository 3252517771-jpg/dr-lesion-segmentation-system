import { useQuery } from "@tanstack/react-query";

import { getLesionFrequencies, getStatsOverview, getTrend } from "../../api/stats";

export function useStatsOverview() {
  return useQuery({ queryKey: ["stats", "overview"], queryFn: getStatsOverview });
}

export function useLesionFrequencies() {
  return useQuery({ queryKey: ["stats", "lesions"], queryFn: getLesionFrequencies });
}

export function useTrend(days = 30) {
  return useQuery({ queryKey: ["stats", "trend", days], queryFn: () => getTrend(days) });
}
