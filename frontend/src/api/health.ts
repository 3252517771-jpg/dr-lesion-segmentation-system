import client from "./client";
import type { HealthStatus } from "../types/diagnosis";

export async function getHealth(): Promise<HealthStatus> {
  const response = await client.get<HealthStatus>("/health");
  return response.data;
}
