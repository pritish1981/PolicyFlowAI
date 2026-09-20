import { AxiosError } from "axios";
import { apiClient } from "./client";
import type { ExceptionOutcome, ReviewDecision, ReviewDetail, ReviewListItem } from "./types";

const employee = { "X-Demo-Role": "EMPLOYEE" };
const reviewer = { "X-Demo-Role": "REVIEWER", "X-Demo-User": "reviewer-demo" };
function fail(error: unknown): never {
  if (error instanceof AxiosError) throw new Error(error.response?.data?.detail ?? "Review request failed.");
  throw new Error("Review request failed.");
}
export async function submitException(expenseId: string, justification: string): Promise<ExceptionOutcome> {
  try { return (await apiClient.post(`/api/v1/expenses/${expenseId}/exceptions`, { justification }, { headers: employee })).data; }
  catch (error) { return fail(error); }
}
export async function addExceptionInformation(id: string, information: string): Promise<ExceptionOutcome> {
  try { return (await apiClient.post(`/api/v1/exceptions/${id}/information`, { information }, { headers: employee })).data; }
  catch (error) { return fail(error); }
}
export async function pendingReviews(): Promise<ReviewListItem[]> {
  try { return (await apiClient.get("/api/v1/reviews/pending", { headers: reviewer })).data; }
  catch (error) { return fail(error); }
}
export async function reviewDetail(id: string): Promise<ReviewDetail> {
  try { return (await apiClient.get(`/api/v1/reviews/${id}`, { headers: reviewer })).data; }
  catch (error) { return fail(error); }
}
export async function submitReview(id: string, decision: ReviewDecision, comments: string): Promise<ExceptionOutcome> {
  try { return (await apiClient.post(`/api/v1/reviews/${id}/decision`, { decision, comments }, { headers: reviewer })).data; }
  catch (error) { return fail(error); }
}
