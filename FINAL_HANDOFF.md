# Checkpoint 1 — final handoff (29 October 2026)

**PEP partner selection, ZF's two-claim verification, and student AD's final independent audit acceptance are recorded. Submission still requires a public GitHub permanent commit link.**

## What is included

- `desk.py`, `sec_desk.py`, `roles.py`: seven-step SEC desk and four separately called OpenAI roles.
- `runs/COSTCO...` (two runs), `runs/Walmart...` (one): existing downloaded SEC data evidence; no Costco five-part report saved.
- `runs/PEPSICO.../PEP_fallback_report.md`: course-permitted five-part fallback on PEP, plus 10-K / 10-Q / 8-K / EX-99.1, companyfacts and peer outputs.
- `audits/PEP_audit.md`: detailed source-checked worksheet with filing references and definition cautions. Zainab Fashola (ZF) recorded a two-claim spot-check of #9 and #11; student AD accepted all 11 core claims on 2026-10-29.
- Tests: the updated package review reports **11/11 automated tests passed**. Automated tests validate code behavior only; they do not replace the required source audit.
- Source correction: PEP current debt maturities in saved 10-K Note 8, line 5291, are **$4,030m**; ratio `(42,321 + 4,030)/20,406 = 2.2714x`. This appears in the revised report and audit. It is note-sourced, not XBRL current-debt data.

## You must do

1. **Partner ticker confirmed:** PepsiCo, Inc. (`PEP`), confirmed by the student on 2026-10-29. The included `PEP_fallback_report.md` is the partner report.
2. Student AD accepted the PEP 11-claim audit on 2026-10-29 after reviewing the saved PEP 10-K, 10-Q, Item 2.02 8-K and EX-99.1. Retain an approved exchange/LSEG source for the October 7 pre-release price with the submission evidence. The Lab 03 Costco hand-audit remains a separate expected exercise.
3. Check the local `.env` has SEC_USER_AGENT and API_KEY; it is deliberately excluded from this ZIP. Never commit secrets. If an earlier archive or repository exposed a developer key, revoke and rotate it before publishing.
4. Upload the **contents** of this folder, not the original ZIP or its `.env` / `.venv`, to your public GitHub repository. Verify the report, code and data are visible without logging in.
5. Copy the complete permanent commit URL from GitHub and submit to Brightspace → Checkpoint 1 by Oct 29, 2026, 11:59 PM Eastern. Only submit an actual URL, never placeholders.

## Submission status

**Ready for Checkpoint 1 content review:** PEP selection, ZF's two partner checks, and student AD's audit acceptance are recorded. Before final submission, retain the approved price-source evidence and create an immutable public GitHub commit URL. The included PEP fallback report is permissible under the documented course fallback rule.

| Requirement | Status |
|---|---|
| PEP report and SEC evidence | Present |
| All 11 audit claim marks | Completed |
| Error and missing counts | Both 0 |
| ZF's two partner checks | Complete |
| Brief reflection fields | Drafted; student should review and personalize |
| Your personal initials/date | Complete — AD, 2026-10-29; accepted 11/11 claims, 0 errors, 0 missing |
| GitHub permanent commit link | Still needed; no repository/commit link is saved here |

## Other checks passed

| Item | Result |
|---|---|
| Seven-step Python desk | Included |
| Four AI-role implementation | Included |
| Costco and Walmart data runs | Included |
| PEP five-section fallback report | Included |
| PEP 10-K, 10-Q, 8-K, and release evidence | Included |
| ZIP integrity and required files | Passed (per the updated package review) |
| PEP financial evidence and arithmetic | Spot-checks passed |
| ZF's two partner checks | Recorded |
| Automated Python tests | 11/11 passed (per the updated package review) |
| API secrets exposed in the submission package | No populated `.env` was reported in the updated package review; the local populated `.env` must remain excluded from any upload |

This is a learning exercise, not financial advice.

AI assistance: ChatGPT assisted with the code review, report drafting, and evidence-backed correction. Student AD independently accepted the 11 core audit claims on 2026-10-29; the final investment judgment remains the student's responsibility.

Any remaining errors are my own.
