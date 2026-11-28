# RM-001/014 — Civil-time launch qualification

P2 · Baseline `d3da240` · 23 November 2026

Validate D03 and D04 at engine entry points using the pinned DE442 short
kernel, leap table, timezone rules and original Bulletin A snapshot. Record
the supported windows by operation, role of predictions, and customer-facing
behaviour for exact, approximate and unknown birth times.

Run the original-source coverage replay and existing historical and
uncertain-time tests. Verify strict UTC cut-offs, observed/predicted transition,
prediction expiry and structured failures. Treat the results as engineering
evidence for the launch policy. Aria Galaxy integration must verify the same
rules against its active source data and user entry flow.
