---
category: EXPENSE_EXCEPTION
currency: INR
effective_date: 2026-01-01
policy_code: POL-006
region: GLOBAL
status: ACTIVE
title: Expense Exception Policy
version: 1.0
---

# POL-006: Expense Exception Policy

## 1. Purpose

This synthetic policy defines the controlled human-review process for
expenses that require an exception from a standard rule.

## 2. When Review Is Required

Examples include a domestic hotel expense above INR 7,000 per night,
international hotel expense above INR 15,000 per night, domestic meal
total above INR 1,500 per day, or airport taxi above INR 2,000 per trip.

A clearly non-reimbursable expense does not automatically become
eligible merely because an exception is requested.

## 3. Employee Justification

Before review, the employee must provide a business justification
explaining why the exception was necessary.

## 4. AI Role

PolicyFlow AI may retrieve evidence, present deterministic variance
calculations, summarize the case, identify missing information, provide
a non-binding recommendation, and show policy citations. It must **not
autonomously approve an expense exception**.

## 5. Human Review

The authoritative reviewer actions are **APPROVE**, **REJECT**, and
**REQUEST_MORE_INFORMATION**.

## 6. Workflow Pause and Resume

The workflow may pause at the human-review step. Execution state must be
persisted so processing can later resume using the same workflow thread.

## 7. Reviewer Evidence

The reviewer should see expense details, applicable policy and limit,
variance, employee justification, documentation status, AI summary or
recommendation, and supporting policy citation.

## 8. Final Decision and Audit

The final human decision must be stored as authoritative business state,
with an audit event recording the decision path.

## 9. More Information

If REQUEST_MORE_INFORMATION is selected, the requested information must
be collected before the case returns for review.

## 10. Related Policies

POL-001, POL-002, POL-003, POL-004, POL-005.
