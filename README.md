# FIN 67110 — Week 2 | Checkpoint 1: The desk runs

**Status: the Lab 02 data-only runs for COST and WMT were saved on 2026-10-28 UTC, and the partner-selected PEP fallback report was saved on 2026-10-29 UTC after the configured API account reported no remaining credits. Zainab Fashola (ZF) recorded the required two partner checks (#9 and #11), and student AD accepted all 11 core claims on 2026-10-29 (0 errors; 0 missing). The GitHub submission remains incomplete.** This is not a claim that the assignment has been submitted.

Week 2, Lab 02 (seven SEC data steps) + Lab 03 (four model roles, five-part report, human audit, partner company), are one checkpoint. **Due Thursday October 29, 2026, 11:59 PM Eastern in Brightspace, by an immutable GitHub commit link.** Instructor references: [Week 2](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/index.html), [report audit](https://cinderzhang.github.io/FIN67110-Fall2026/reference/audit-checklist.html), [grading](https://cinderzhang.github.io/FIN67110-Fall2026/grading.html), [schedule](https://cinderzhang.github.io/FIN67110-Fall2026/schedule.html).

## Set up locally (Windows, VS Code terminal)

Open this folder in VS Code. In its terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
py check_env.py
py -m pytest -q
```

If PowerShell blocks activation, skip that line and use `.\.venv\Scripts\python.exe` instead of `py` in the subsequent commands. Never share your API key or put `.env` in GitHub; if a key was shared previously, revoke it and generate a new one.

Populate `.env` with your *real* name/email in `SEC_USER_AGENT` and a *developer console* OpenAI `API_KEY`. A ChatGPT subscription is not the API key. `MODEL_NAME` is configurable; the default is an OpenAI model identifier and may need adjustment to an available model for your account. The program uses the **official `openai` Python SDK** for the four roles. It does not use ChatGPT chat credentials.

## Commands — Lab 02 (data-only, no model charges)

Use the verified official close `P` from the instructor's run, or if unavailable, a pre-release closing price from your approved source; pass the **actual number**, not the letter `P`. Supply its date for a reproducible P/E.

```powershell
py desk.py COST --peers WMT,TGT,BJ --price P --price-date YYYY-MM-DD --data-only
py desk.py WMT --peers COST,TGT,BJ --data-only
py desk.py COST --peers WMT,TGT,BJ --data-only --step 4
```

**Replace `P` and `YYYY-MM-DD` before running**. To run Lab 02 without any price, simply omit `--price` and `--price-date`; P/E will show missing, not a fabricated figure. `--step 4` runs only the prerequisite stages through step 4, saves the artifacts up to that step, and prints only step 4's detail.

The seven printed stages are: (1) ticker → SEC CIK; (2) locate latest 10-K, 10-Q and the latest 8-K actually reporting Item 2.02, with accession and EDGAR Accepted timestamp; (3) download and convert all three filings and Exhibit 99.1 into numbered/line-readable plain text; (4) latest 10-K fiscal-year SEC XBRL facts with tag, unit, fiscal end, accession and comparable prior year; (5) code-only ratio arithmetic; (6) exact candidate release lines for quarter revenue and diluted EPS; (7) fiscal-year peer facts and margins, comparing **operating income / total revenue**.

A run creates `runs/TICKER_YYYY-MM-DD_HHMMSS_UTC/` with `10-K.txt`, `10-Q.txt`, `earnings_8-K.txt`, `release_EX-99.1.txt`, `filings.json`, `facts.json`, `ratios.json`, `release_lines.json`, `peers.json`, and `run_manifest.json`.

**Validation is mandatory:** SEC tags sometimes represent *net sales rather than total revenue*, a different accounting period, or debts with current portions already included. The script flags likely traps rather than quietly treating a missing or ambiguous figure as authoritative. The 8-K release-line finder lists potential lines, and a human must select the correct **quarter**, **GAAP** and **year-ago** comparatives. If SEC does not expose a concept using the supported US-GAAP tags, the figure stays `MISSING` until you inspect the company's extension tags and the filing. If a 10-K debt note explicitly states current maturities of long-term debt, an auditor may provide that precise line and its table scale with `--debt-note-line N --debt-note-scale 1|1000|1000000`; the calculator records it as filing-note evidence, **not** as an XBRL tag, and retains a human-verification caution.

## Commands — Lab 03 (four model roles)

Once the data-only run succeeds and `API_KEY` is set:

```powershell
py desk.py COST --peers WMT,TGT,BJ --price P --price-date YYYY-MM-DD
```

This runs the same seven steps, followed by distinct `Research Analyst`, `Financial Analyst`, `Investment Advisor` and `Strategy Manager` calls. Each receives a JSON handoff with task, context and expected output. The Manager checks the draft and may send a failing role back **once**. The program compiles the exact five required headings and saves `COST_report.md` and `role_outputs.json` in that run folder. The first report line identifies its filings/accessions; the second records UTC runtime and model. A generated report is **not** an audited report.

The five report parts are:

1. Overview
2. Market Positioning and Growth Outlook
3. Valuation Insights
4. Future Developments and Strategic Recommendations
5. Investment Recommendation

The model is not allowed to calculate ratios. It receives calculator outputs, XBRL tags, and line-numbered filing/release excerpts. It must flag missing evidence instead of inventing quarterly numbers, peer comparisons, or valuation claims. Manually compare **every** numeric claim and every quoted line with source filings. The Strategy Manager is not a substitute for the required human audit.

## Audit after first Costco run

Open `audits/COST_audit_TEMPLATE.md` and the official [audit checklist](https://cinderzhang.github.io/FIN67110-Fall2026/reference/audit-checklist.html). By hand, verify all 11 standard claims: 8 from the 10-K, 3 from Exhibit 99.1. Add every additional Financial Analyst number, price and P/E, and peer margin; mark Correct / Wrong / Unsupported / Missing / Not in filings. Count **Wrong + Unsupported** as errors and count **Missing** separately, at the top. Two more rows check template and investment recommendation. Ask your partner to check and initial two of your marks. Do **not** declare your marks verified unless you actually did the work.

## Partner's choice (the essential Checkpoint 1 artifact)

Get a U.S. company ticker **chosen by your partner** that filed an earnings release **in October 2026** (ideally a current Item 2.02 8-K with EX-99.1). Run the exact same pipeline without editing company-specific production code:

```powershell
py desk.py PARTNER_TICKER --peers PEER1,PEER2 --price P --price-date YYYY-MM-DD
```

Replace placeholders with the actual ticker, appropriate peers, and an official **pre-release** closing price/date. The output should include `PARTNER_TICKER_report.md`. Have your partner verify two claims by hand and record the marks at the top of `audits/PARTNER_TICKER_audit_TEMPLATE.md`; finish your own full 11-claim audit before Session 4. Confirm that the current quarter quoted is in the actual **October** release, not an older release, and that it is GAAP EPS, not adjusted EPS.

## Push to your PUBLIC GitHub repo

Copy generated output folders `runs/` into your work repository; the ZIP does not contain them because live SEC/model runs were not accessible in this environment. Check that `runs` contains filings/facts, Costco report, and **partner report**, and that the correct audits are present. Then:

```powershell
git status --short
git check-ignore .env
git add desk.py sec_desk.py roles.py check_env.py requirements.txt README.md .gitignore .env.example tests audits MANUAL_CHECKLIST.md runs
git commit -m "Week 2: SEC seven-step desk, four-role reports and audits"
git push
# prints full permanent hash of the commit:
git rev-parse HEAD
```

Do not run `git add .env`; check `git status` and GitHub after pushing to verify that secrets were not committed. **If `.env` appears in the Git history, revoke the exposed key immediately and clean the public history.** With a full hash from `git rev-parse HEAD`, your immutable submission link is:

`https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/tree/YOUR_FULL_COMMIT_SHA`

Paste that link in **Brightspace → Checkpoint 1**. The project page shows this same commit-permalink pattern. `CHECKPOINT1_SUBMISSION.txt` is a placeholder to fill, not a final link. Use incognito to confirm the commit and the partner report open publicly.

## If the API is down or the desk fails

The Week 2 [fallback](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/index.html#the-fallback) is **accepted for this checkpoint**: obtain the latest 10-K income statement, balance sheet and cash flow statement plus the latest earnings Exhibit 99.1; paste these into any model with the four role tasks and five report headings. Save the response as `runs/PARTNER_TICKER_fallback_report.md` (first line: company and filing accession/URL names; second line: `fallback`) and push it with your desk code and audit. Do not invent filing values or claim a full live run. The human audit is still required. The fallback is not a substitute for actually publishing the report and permalinking the commit.

## Limitations and design notes

- SEC API/web requests require a usable Internet connection and legitimate `SEC_USER_AGENT`, may be throttled, and can change their layouts. The saved COST and WMT data-only folders were fetched from live EDGAR on 2026-10-28 UTC, and the PEP folder on 2026-10-29 UTC. Their figures and definitions still require the student's filing-by-filing audit. The PEP fallback report was used because the configured API account returned `credit_balance_exhausted`; the tests are not proof of a correct filing run.
- The script examines SEC's recent submissions list; unusually inactive filers, some amended-only histories, malformed filings and unusual issuer-specific XBRL extensions may need additional support. Failure is explicit rather than hidden.
- An Item 2.02 8-K that lacks an EX-99.1 exhibit in the expected EDGAR index will be reported as an error, rather than treating some other exhibit as if it were the earnings release.
- No live market price is scraped. `--price` and `--price-date` must come from the user / LSEG / official exchange close before the earnings release.
- For text extraction, long filings are saved fully, but only bounded excerpts are passed to the model. A source quote outside those excerpts must not be fabricated: inspect the saved filing.
- No company names or figures are hard-coded into the production data pipeline or model role logic. Costco and peers appear only as usage/test instructions.
- Audits must be personally performed; code cannot sign off in a student's name.


## Optional: calculate the two quarterly revenue periods without model arithmetic

If the latest earnings release has a complex table and you want its quarter figures computed in code, copy `examples/quarter_review_TEMPLATE.json` into a new JSON file and enter the **two comparable quarter revenue values as printed in the EX-99.1 table**, the quarter's **GAAP** diluted EPS, unit and the exact line numbers from the saved `release_EX-99.1.txt`. The two revenue values must be in the same unit. The ticker must equal the run ticker. Then rerun with:

```powershell
py desk.py PARTNER_TICKER --peers PEER1,PEER2 --price P --price-date YYYY-MM-DD --quarter-review quarter_my_company.json
```

The calculator prints `(current quarter revenue − same quarter last year) / same quarter last year`. The role receives the resulting growth rate, so **the model does not do arithmetic**. The values remain marked as human-transcribed and require human filing verification; the program cannot prove which quarter columns you selected. Do not use the template's nulls or a Costco file for a different company.

This is a learning exercise, not financial advice.

AI assistance: ChatGPT assisted in drafting the code and documentation. I must independently verify the sources before asserting that I verified them; the judgments remain mine.

Any remaining errors are my own.
