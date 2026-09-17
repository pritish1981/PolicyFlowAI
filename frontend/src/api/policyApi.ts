import { AxiosError } from "axios";
import { apiClient } from "./client";
import type { PolicyAnswerResponse, PolicyQueryRequest } from "./types";

export async function queryPolicy(
  request: PolicyQueryRequest,
  signal?: AbortSignal,
): Promise<PolicyAnswerResponse> {
  try {
    const response = await apiClient.post<PolicyAnswerResponse>("/api/v1/policy/query", request, {
      signal,
    });
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") throw new Error(detail);
      if (detail && typeof detail.message === "string") throw new Error(detail.message);
    }
    throw new Error("Policy Q&A is temporarily unavailable. Please try again.");
  }
}
