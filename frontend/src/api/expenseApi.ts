import { AxiosError } from "axios";
import { apiClient } from "./client";
import type { ExpenseAssessment, ExpenseRequest } from "./types";

function explain(error: unknown): never {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (detail && typeof detail.message === "string") throw new Error(detail.message);
  }
  throw new Error("Expense assessment is temporarily unavailable. Please try again.");
}

export async function submitExpense(request: ExpenseRequest, key: string): Promise<ExpenseAssessment> {
  try {
    const response = await apiClient.post<ExpenseAssessment>("/api/v1/expenses", request,
      { headers: { "Idempotency-Key": key } });
    return response.data;
  } catch (error) { return explain(error); }
}

export async function clarifyExpense(id: string, request: ExpenseRequest): Promise<ExpenseAssessment> {
  try {
    const response = await apiClient.post<ExpenseAssessment>(
      `/api/v1/expenses/${encodeURIComponent(id)}/clarifications`, request);
    return response.data;
  } catch (error) { return explain(error); }
}
