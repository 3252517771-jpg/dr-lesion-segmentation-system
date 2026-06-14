import client from "./client";
import type { LesionFrequencyResponse, StatsOverview, TrendResponse } from "../types/stats";

export async function getStatsOverview(): Promise<StatsOverview> {
  const response = await client.get<StatsOverview>("/stats/overview");
  return response.data;
}

export async function getLesionFrequencies(): Promise<LesionFrequencyResponse> {
  const response = await client.get<LesionFrequencyResponse>("/stats/lesions");
  return response.data;
}

export async function getTrend(days = 30): Promise<TrendResponse> {
  const response = await client.get<TrendResponse>("/stats/trend", { params: { days } });
  return response.data;
}
