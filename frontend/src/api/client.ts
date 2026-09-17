import axios from "axios";
import type { HealthResponse, ReadinessResponse } from "./types";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 10000,
});

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/health", { signal });
  return response.data;
}

export async function getReadiness(signal?: AbortSignal): Promise<ReadinessResponse> {
  const response = await apiClient.get<ReadinessResponse>("/ready", {
    signal,
    validateStatus: (status: number) => status === 200 || status === 503,
  });
  return response.data;
}
