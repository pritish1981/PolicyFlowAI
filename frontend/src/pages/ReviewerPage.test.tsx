// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewerPage } from "./ReviewerPage";
import * as api from "../api/reviewApi";

vi.mock("../api/reviewApi");
const item = { exception_id: "ex-1", expense_id: "expense-1", expense_type: "HOTEL",
  amount: "9500.00", currency: "INR", policy_limit: "7000.00", variance_amount: "2500.00",
  justification: "Approved hotels were unavailable near the venue.", created_at: "2026-09-20T00:00:00Z" };

describe("ReviewerPage", () => {
  beforeEach(() => {
    vi.mocked(api.pendingReviews).mockResolvedValue([item]);
    vi.mocked(api.reviewDetail).mockResolvedValue({ ...item, thread_id: "thread-1",
      status: "PENDING_REVIEW", purpose: "Client conference", location: "Bengaluru",
      summary_status: "AVAILABLE", review_summary: { summary: "Neutral facts only.", key_facts: [],
        risk_or_attention_points: [], citation_chunk_ids: [] }, citations: [],
      information_history: [], latest_reviewer_comments: null });
    vi.mocked(api.submitReview).mockResolvedValue({ exception_id: "ex-1", expense_id: "expense-1",
      thread_id: "thread-1", status: "MORE_INFORMATION_REQUIRED", variance_amount: "2500.00",
      next_action: "PROVIDE_MORE_INFORMATION", reviewer_comments: "Need evidence." });
  });

  it("labels AI assistance and submits an explicit human action", async () => {
    render(<ReviewerPage />);
    fireEvent.click(await screen.findByRole("button", { name: /HOTEL/ }));
    expect(await screen.findByText("AI-generated non-authoritative summary")).toBeInTheDocument();
    expect(screen.getByText("Neutral facts only.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Reviewer comments"), { target: { value: "Need evidence." } });
    fireEvent.click(screen.getByRole("button", { name: "REQUEST MORE INFORMATION" }));
    await waitFor(() => expect(api.submitReview).toHaveBeenCalledWith(
      "ex-1", "REQUEST_MORE_INFORMATION", "Need evidence."));
    expect(await screen.findByText(/MORE INFORMATION REQUIRED: human decision recorded/)).toBeInTheDocument();
  });
});
