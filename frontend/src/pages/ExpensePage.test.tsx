// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ExpensePage } from "./ExpensePage";
import * as expenseApi from "../api/expenseApi";
import * as reviewApi from "../api/reviewApi";

vi.mock("../api/expenseApi");
vi.mock("../api/reviewApi");

describe("ExpensePage", () => {
  it("submits an eligible exception without presenting it as approved", async () => {
    vi.mocked(expenseApi.submitExpense).mockResolvedValue({ expense_id: "expense-1",
      thread_id: "thread-1", request_id: "request-1", decision: "NEEDS_REVIEW",
      policy_limit: "7000.00", confidence: "1", explanation: "Human review required.",
      citations: [], next_action: "SUBMIT_EXCEPTION_JUSTIFICATION", missing_fields: [] });
    vi.mocked(reviewApi.submitException).mockResolvedValue({ exception_id: "ex-1",
      expense_id: "expense-1", thread_id: "thread-1", status: "PENDING_REVIEW",
      variance_amount: "2500.00", next_action: "WAIT_FOR_REVIEW", reviewer_comments: null });
    render(<ExpensePage />);
    fireEvent.change(screen.getByLabelText("Expense type"), { target: { value: "HOTEL" } });
    fireEvent.change(screen.getByLabelText("Travel type"), { target: { value: "DOMESTIC" } });
    fireEvent.change(screen.getByLabelText("Amount (INR)"), { target: { value: "9500" } });
    fireEvent.change(screen.getByLabelText("Location"), { target: { value: "Bengaluru" } });
    fireEvent.change(screen.getByLabelText("Purpose"), { target: { value: "Client conference" } });
    fireEvent.change(screen.getByLabelText("Receipt available"), { target: { value: "true" } });
    fireEvent.click(screen.getByRole("button", { name: "Assess expense" }));
    expect(await screen.findByText("Human review required")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Exception justification"), { target: {
      value: "Approved hotels were unavailable near the conference venue." } });
    fireEvent.click(screen.getByRole("button", { name: "Submit for human review" }));
    await waitFor(() => expect(reviewApi.submitException).toHaveBeenCalled());
    expect(await screen.findByText("PENDING REVIEW")).toBeInTheDocument();
    expect(screen.queryByText(/^APPROVED$/)).not.toBeInTheDocument();
  });
});
