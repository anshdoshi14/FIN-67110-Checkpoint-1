# PepsiCo (PEP) — source-checked audit worksheet for fallback report

**Company and ticker chosen by partner:** PepsiCo, Inc. (`PEP`) — student-confirmed 2026-10-29. **Partner name:** **Zainab Fashola**

**Sources saved in this package:** 2025 Form 10-K accession `0000077476-26-000007` (FY ended 2025-12-27); 2026 third-quarter Form 10-Q accession `0000077476-26-000048` (12 weeks ended 2026-09-05); Item 2.02 Form 8-K with Exhibit 99.1 accession `0000077476-26-000050` (release dated 2026-10-08).

**Source cross-check date:** 2026-10-29.

**Errors (Wrong + Unsupported): 0** across 11 required core claims and two supplemental market/peer claim groups, *after clarifying the course-standard FCF definition in the report*. **Missing claims: 0.** All eleven required report figures are present. **Core audit coverage: 11/11 claims cross-checked.** Supplementary rows #12–13 are checked using separately identified non-PEP sources.

**#9 — Correct (ZF)** and **#11 — Correct (ZF)**.

| # | Claim | Report says | What the saved filing / independent source shows | Mark | Precise reference, period, and calculation |
|---|---|---|---|---|---|
| 1 | Latest FY total net revenue | $93.925B | $93,925m for FY 2025 | Correct | `10-K.txt` L003883 (also L003518); `Revenues` FY 2024-12-29 to 2025-12-27; USD millions |
| 2 | FY revenue growth | 2.25% | $93,925m vs $91,854m; **2.2547% → 2.25%** | Correct | `10-K.txt` L003883; `(93,925−91,854)/91,854`; FY 2025 vs FY 2024, not organic growth |
| 3 | Operating profit and operating margin | $11.498B / 12.24% | $11,498m; **11,498/93,925 = 12.2417%** | Correct | `10-K.txt` L003883–L003888; 2025 `OperatingIncomeLoss`; filing rounds margin to 12.2% at L003520 |
| 4 | Net income attributable to PepsiCo | $8.240B | $8,240m attributable to PepsiCo (vs $8,295m consolidated) | Correct | `10-K.txt` L003893–L003895; `NetIncomeLoss`, FY 2025; do not substitute consolidated net income |
| 5 | GAAP diluted EPS, full year | $6.00 | $6.00 diluted, not basic $6.02 | Correct | `10-K.txt` L003896–L003901 (also L003529); `EarningsPerShareDiluted`, FY 2025 |
| 6 | Return on average common equity | 42.86% | $8,240m / [($20,406m + $18,041m)/2] = **42.8642%** | Correct | `10-K.txt` L003895, L004027–L004035; `StockholdersEquity` 2025-12-27 and 2024-12-28; PepsiCo common equity, excluding noncontrolling interests |
| 7 | Long-term borrowings/equity, *including their current maturities* | 2.27x (227.14%) | ($42,321m noncurrent + $4,030m current maturities) / $20,406m = **2.2714x** | Correct | `10-K.txt` L003995 (USD millions), L004019–L004035 and **Note 8 L005286–L005306**. This is **long-term debt including its current maturities**, not all interest-bearing borrowings: including *all* short-term debt obligations ($6,861m, which already include $4,030m maturities) gives **2.4102x**; never double count the $4,030m |
| 8 | Free cash flow, **course convention = CFO − capex** | $7.672B | $12,087m CFO − $4,415m capital spending = **$7,672m**, correct **by the course's formula** | Correct | `10-K.txt` L003923–L003954; `ratios.json`. **Definition trap:** PepsiCo *itself* defines non-GAAP FCF as CFO − capex **+ $528m proceeds from PPE sales = $8,200m** (`10-K.txt` L003641–L003643 and L003748–L003755). $7.672B must be labeled the **simple/course convention**, not the company's published FCF |
| 9 | Latest release 12-week GAAP net revenue | $25.274B (Q3 2026) | **$25,274m** in 2026 quarter column; **$23,937m** in 2025 comparison | Correct | `release_EX-99.1.txt` **L000157–L000162**; independently cross-checked `10-Q.txt` L002068–L002073. Column: **12 weeks ended 2026-09-05**, *not* 36 weeks. |
| 10 | Same-quarter year-ago GAAP net-revenue growth | 5.59% | ($25,274m − $23,937m) / $23,937m = **5.5855% → 5.59%** | Correct | `release_EX-99.1.txt` L000159–L000162; `10-Q.txt` L002070–L002073. Reported GAAP net revenue, **not** organic growth (3.1% in release L000052) |
| 11 | Quarterly **GAAP diluted EPS** | $2.23 | **$2.23** vs $1.90 prior-year quarter in the 12-week **diluted** line | Correct | `release_EX-99.1.txt` **L000157–L000176** (GAAP condensed income statement, in millions except per-share amounts); `10-Q.txt` **L002086–L002091**, Note 9 L003010–L003019. **Not** 36-week $6.10 and **not** core EPS. |
| 12 | Pre-release close and stated P/E | $123.73 on 2026-10-07; 20.62x | Oct. 7, 2026 closing price **$123.73** corroborated by two non-filing historical market-data sources; **123.73 / FY 2025 diluted EPS $6.00 = 20.6217x** | Correct | Market data (not SEC): [Stock Analysis, PEP history](https://stockanalysis.com/stocks/pep/history/) and [Twelve Data, PEP history](https://twelvedata.com/markets/106776/stock/nasdaq/pep/historical-data). Source EPS: `10-K.txt` L003898. This is an **FY-2025-EPS P/E at the pre-release date**, not a current or trailing-twelve-month P/E. The claimed original LSEG lookup was not saved in the archive, so the source-provider attribution is not independently established |
| 13 | Three peer FY operating margins | KO 28.71%; KDP 21.53%; MDLZ 9.21% | **KO:** 13,762/47,941=28.7061%; **KDP:** 3,575/16,603=21.5323%; **MDLZ:** 3,548/38,537=9.2067% | Correct | Saved `peers.json` + separate official FY2025 filings: [KO 2025 10-K](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm) (net *operating* revenues); [KDP 2025 10-K](https://www.sec.gov/Archives/edgar/data/1418135/000141813526000016/kdp-20251231.htm) (*net sales*); [MDLZ 2025 10-K](https://www.sec.gov/Archives/edgar/data/1103982/000162828026005345/mdlz-20251231.htm) (*net revenues*). All FY ended 2025-12-31; these peer filings are **not included as local .txt files** |
| Template | Five required report sections | All five headings present | Overview; Market Positioning and Growth Outlook; Valuation Insights; Future Developments and Strategic Recommendations; Investment Recommendation | Correct | `runs/PEPSICO_INC_PEP_2026-10-29_014807_UTC/PEP_fallback_report.md` |
| Recommendation | Hold supported by numbers | **Provisional Hold**, 5.59% 12-week net-revenue growth vs FY operating-profit decline | The chosen evidence is accurate: Q3 GAAP revenue **$25,274m** vs $23,937m; FY operating profit **$11,498m** vs **$12,887m** (a decline of ~10.8%). Recommendation remains judgmental, not proved by one metric | Correct | `release_EX-99.1.txt` L000162, `10-K.txt` L003518–L003522; checks accuracy of numeric support, **not a guarantee that Hold is optimal** |

## Definition traps / specific checks

1. **Free cash flow:** the course checklist uses CFO less PP&E/capital spending ($7.672B), but PepsiCo explicitly labels **$8.200B** as its own non-GAAP FCF after adding $528m of sales of PP&E. The fallback report now calls the $7.672B metric the *simple/course* FCF and also states the company's figure.
2. **Debt/equity:** 2.27x is the clearly labeled *long-term debt including its current maturities* over PepsiCo common equity. Do **not** present that as all-debt/equity; all outstanding short-term debt obligations yield approximately 2.41x. The $4.030B current portion came from Note 8; it was **not** a current-debt XBRL tag.
3. **Quarter and GAAP:** the release shows 12-week and 36-week columns. Use Q3 2026 12-week GAAP net revenue $25.274B and **GAAP diluted** EPS $2.23; organic revenue growth and core EPS are different non-GAAP measures.
4. **Valuation:** price $123.73 is the October 7 close, before the October 8 publication; the 20.62x figure divides by **2025 fiscal-year** diluted EPS, not a rolling EPS estimate.

**Most likely to mislead the reader:** The **$7.672B “free cash flow”** line looks comparable to management-reported FCF, but PepsiCo's defined non-GAAP FCF was **$8.200B**; a reader could attribute the wrong cash-generation figure to the company. The 2.27x long-term debt ratio also needs its restricted denominator/numerator description.

## Partner two-claim spot-check / initials

- **Claim #9:** ZF verified the saved Exhibit 99.1 and 10-Q 12-week GAAP revenue columns; mark **Correct (ZF)**.
- **Claim #11:** ZF verified the 12-week GAAP diluted EPS in both sources; mark **Correct (ZF)**.

## Student final audit sign-off

Student acceptance recorded after personal review of the eleven core marks and counts above:

- **Student initials:** AD  **Date:** 2026-10-29  **Final audit disposition (accept/correct):** Accept — 11/11 claims correct; 0 errors; 0 missing.

## Brief reflection — suggested wording for student to review and personalize

**Weakest step, and why:** The weakest step is translating raw accounting fields into comparable financial ratios. Values can be numerically correct but have different definitions, as the two free-cash-flow measures and debt categories demonstrate.

**Which role would fail first for a new company:** The Financial Analyst role is most at risk when a new company uses different XBRL revenue tags, debt categories, or non-GAAP definitions.

**One concrete change to that role:** Require a pre-publication check table for every metric: exact formula, GAAP/non-GAAP label, fiscal period, unit, filing accession and line, plus a reconciliation to management-defined alternatives and an explicit warning for ambiguous tags.

**Number most likely to fool the reader:** **$7.672B of course-formula FCF**, because the company's own FCF presentation says **$8.200B**. This is a *definition* mismatch, not a subtraction error.

**Reflection status:** Draft completed from evidence, **not represented as the student's personal experience**; student should read, edit if necessary, and accept in their own words.

This is a learning exercise, not financial advice.

AI assistance: ChatGPT assisted with the code, report drafting, and audit worksheet. I independently reviewed and accepted the eleven core audit claims; the final investment judgment remains mine.
