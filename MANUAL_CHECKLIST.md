# Human action checklist — FIN 67110 Week 2

These boxes are deliberately unmarked; only the student/partner can verify them.

- [ ] Open `.env` locally; set actual `SEC_USER_AGENT` with your own name and email; set developer `API_KEY` privately. Never commit it.
- [ ] Confirm all seven SEC steps with `python desk.py COST --peers WMT,TGT,BJ --price <VERIFIED_PRICE> --price-date YYYY-MM-DD --data-only`.
- [ ] Compare COST CIK, 10-K, 10-Q, last earnings 8-K's Item 2.02 and index-page Accepted time with EDGAR.
- [ ] Open and compare every saved filing and EX-99.1; confirm correct exhibit, not 8-K body.
- [ ] Match EVERY current-year numeric fact's tag, period end, units and value to the latest 10-K. Resolve any tag traps or extension tags.
- [ ] Redo all five ratio calculations by hand, including prior-year average equity and current portion of long-term debt. For PEP, independently check 10-K Note 8 L005291 ($4,030m) and calculate `(42,321 + 4,030) / 20,406 = 2.2714x`.
- [ ] Check release quarter total revenue, growth and GAAP diluted EPS directly in Exhibit 99.1 (not adjusted EPS).
- [ ] Verify peers' own latest 10-K periods, revenue definitions and operating margins; do not assume fiscal ends align.
- [ ] Run model roles and confirm four names print; check all five sections are in the saved report.
- [ ] Complete `audits/COST_audit_TEMPLATE.md` by hand, including all eleven claims, extra numbers, recommendation and the two counts; partner inspects two marks.
- [ ] Confirm PEP is the partner's chosen U.S. October earnings-reporting company. The PEP evidence folder and permitted fallback report are saved; if the partner changes the selection, rerun the desk and replace the report/audit.
- [x] Partner checks two core claims for the PEP report: Zainab Fashola (ZF) marked claims #9 and #11 `Correct (ZF)` in `audits/PEP_audit.md`.
- [x] Student AD accepted the PEP report's 11 core audit claims on 2026-10-29 (0 errors; 0 missing), including a review for model quotations that do not exist in the filings.
- [x] Student audit date and final disposition are recorded in `audits/PEP_audit.md`; the PEP report's audit-status wording has been updated.
- [ ] Check `.env` is absent from `git status` and absent from the public repository. A previously exposed key should be revoked and rotated.
- [ ] Commit and push the code, facts folders, audit and final partner report to the PUBLIC repository. Confirm both report and facts are readable from incognito browser.
- [ ] Brightspace → Checkpoint 1 → submit immutable commit link before Thu Oct 29, 2026, 11:59 PM Eastern.

# Short answer prompts for partner review

**Figure 1:** An agentic workflow is coordinated by a coded harness; distinct models operate as roles, while the harness enforces handoffs and validation. The diagram alone does not give the workflow unrestricted autonomy.

**SEC filing forms:** 10-K = audited annual report; 10-Q = quarterly filing (usually unaudited); 8-K Item 2.02 + Exhibit 99.1 = earnings announcement/release; XBRL = financial reporting data with tagged concept, unit, time and source.

**Tag trap:** The same concept can be tagged differently across years or companies; a reader must select tags that actually describe total revenue, use the proper latest-year fiscal end and verify each value with the 10-K.

**Human sign-off:** The model can generate fluent unsupported figures; auditor independently checks evidence/definitions, marks missing/errors, and takes responsibility before publishing.

**Reflection prompts:** Weakest step and reason; which role would fail on a new company; one concrete change to that role; the one number most likely to fool a reader.

This is a learning exercise, not financial advice.

AI assistance: ChatGPT helped build this checklist; verification and judgments remain the student's responsibility.

Any remaining errors are my own.
