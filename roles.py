"""Four explicitly separated model roles with JSON task/context/output handoffs.

Numerical calculators live in sec_desk.py; model output is not a data source.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Any

FIVE_HEADINGS = (
    'Overview',
    'Market Positioning and Growth Outlook',
    'Valuation Insights',
    'Future Developments and Strategic Recommendations',
    'Investment Recommendation',
)

RESEARCH_SYSTEM = """You are the Research Analyst in a four-role equity research desk.
You receive JSON containing only Strategy Manager approved tasks and contexts.
Use only the provided 10-K business/MD&A excerpts and earnings release.
Describe business model, competitive positioning, catalysts and recent developments.
For EACH factual claim, quote a short exact phrase from a supplied line and cite
[10-K accession L000123] or [EX-99.1 accession L000123]. If excerpt insufficient,
state 'Not established by the excerpts' rather than inventing facts.
Return valid JSON only with keys overview, market_positioning_and_growth_outlook,
future_developments_and_strategic_recommendations. Markdown strings as values.
No financial calculations."""

FINANCIAL_SYSTEM = """You are the Financial Analyst in a four-role desk.
Use ONLY supplied XBRL evidence (tag, fiscal period, accession), SEC filing lines,
the calculator's results, and release excerpts. Never do new arithmetic.
Each numeric claim MUST show source tag, period end and 10-K accession OR exact
Exhibit 99.1 quotation and line, plus arithmetic supplied by the calculator.
Required: annual total revenue, growth, operating income and margin, net income
attributable to company, GAAP diluted EPS, return on average equity, debt/equity
including current portion, free cash flow, latest quarterly revenue and its growth
versus the same quarter last year, latest quarter GAAP diluted EPS, P/E from supplied
price, and peer operating margins on a consistent total-revenue definition.
Avoid falsely treating net sales as total revenue; if ambiguous, flag for human
review. When quarter figures are not unequivocally supported by release lines,
explicitly say 'Not established' rather than guessing numbers. Report any
missing tags, unknown GAAP basis, period ambiguities and debt double-count risks.
Do not compute numbers yourself or infer figures from memory. Calculator output
is authoritative only when the underlying inputs and definitions are valid.
Return valid JSON only with keys financial_analysis and valuation_insights,
both Markdown strings."""

INVESTMENT_SYSTEM = """You are the Investment Advisor. You receive ONLY Research Analyst
and Financial Analyst outputs, no original external data or invented valuation.
Choose one of Buy, Hold, Sell, label it provisional, and state the one specific
supported number that decides the choice, as cited by the Financial Analyst.
If the evidence cannot support a reasonable directional claim, choose Hold,
explicitly citing the strongest supported number and explaining the uncertainty.
Do not project an unsupported price target or pretend P/E alone proves fair value.
Return valid JSON only with key investment_recommendation as Markdown."""

MANAGER_SYSTEM = """You are the Strategy Manager, verifier of completeness and coherence.
You see the draft five-part report and a compact financial data manifest.
Return JSON only: {"status":"PASS" or "REVISE", "issues":[{"role":"Research Analyst"
 or "Financial Analyst" or "Investment Advisor", "reason":"..."}]}.
Check exact five headings, eleven core claims or explicit unsupported/missing
statements, sources for every figure, calculator arithmetic, peer periods,
three separate roles' outputs, and thesis consistency. Check model quotes against
provided excerpts if possible. Do not introduce, edit, or recompute facts.
Flag mismatches and unsupported claims. The caller will send one revision request
to each failing role, at most once, then compile the report in code."""


def parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned, flags=re.I)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find('{'), cleaned.rfind('}')
    if start >= 0 and end > start:
        data = json.loads(cleaned[start:end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError('Model did not return parseable JSON object; do not silently publish.')


def call_role(api, model: str, role: str, instructions: str, task: str,
              context: dict, expected_output: Any, revision: str = '') -> dict:
    print(f'ROLE — {role}', flush=True)
    request = {'task': task, 'context': context, 'expected_output': expected_output}
    if revision:
        request['one_revision_requested'] = revision
    response = api.responses.create(model=model, instructions=instructions,
                                    input=json.dumps(request, ensure_ascii=False, default=str))
    return parse_json(response.output_text)


def compose(parts: dict) -> str:
    mapping = {
        'Overview': parts.get('overview', ''),
        'Market Positioning and Growth Outlook': parts.get('market_positioning_and_growth_outlook', ''),
        'Valuation Insights': parts.get('valuation_insights', ''),
        'Future Developments and Strategic Recommendations': parts.get('future_developments_and_strategic_recommendations', ''),
        'Investment Recommendation': parts.get('investment_recommendation', ''),
    }
    return '\n\n'.join('## ' + heading + '\n\n' + (body.strip() if isinstance(body, str) else str(body))
                       for heading, body in mapping.items())


def evidence_appendix(data: dict) -> str:
    facts = data['facts']
    ratios = data['ratios']
    lines = [
        '## Source evidence appendix — machine extracted, NOT human audited',
        'Do not interpret machine-extracted facts as verified until the auditor compares them with the filing.',
        '',
        '| Concept | Current fiscal-year value | XBRL tag | Period end | Filing |',
        '|---|---:|---|---|---|',
    ]
    for name, obj in facts['fields'].items():
        item = obj['current']
        if item:
            lines.append(f'| {name} | {item["value"]:,} {item["unit"]} | `{item["tag"]}` | {item["end"]} | {item["accession"]} |')
        else:
            lines.append(f'| {name} | NOT FOUND | — | {facts["fiscal_year_end"]} | — |')
    lines += ['', '| Ratio | Output | Code arithmetic |', '|---|---:|---|']
    for name, item in ratios.items():
        value = item['value']
        displayed = ('NOT CALCULABLE' if value is None else
                     f'{value:.2%}' if item['unit'] == 'fraction' else f'{value:,.4f}')
        lines.append(f'| {name} | {displayed} | `{item["arithmetic"]}` |')
    if facts['cautions']:
        lines.extend(['', '### Data-definition cautions'])
        lines.extend('- ' + caution for caution in facts['cautions'])
    lines.extend(['', '### Release lines to audit (not verified for quarter/GAAP definition)'])
    for kind, rows in data['release_lines'].items():
        for row in rows[:12]:
            cleaned = row['text'].replace('|', '\\|')
            lines.append(f'- {kind}, EX-99.1 L{row["line"]:06d}: {cleaned}')
    if data.get('quarterly'):
        q = data['quarterly']
        lines += ['', '### Manually transcribed earnings-quarter inputs — still subject to audit',
                  f'- Total revenue current/prior ({q["unit"]}): {q["revenue_current"]} / {q["revenue_prior"]}; EX-99.1 line {q["revenue_line"]}',
                  f'- GAAP diluted EPS: {q["diluted_eps_gaap"]}; EX-99.1 line {q["eps_line"]}',
                  f'- Same-quarter growth: {q["revenue_growth"]:.2%} = `{q["arithmetic"]}`']
    lines += ['', '### Peers — same operating-income / total-revenue definition']
    for peer, result in data['peers'].items():
        margin = result['operating_margin']
        lines.append(f'- {peer}, FY end {result["facts"]["fiscal_year_end"]}: '
                     f'{margin["value"] if margin["value"] is not None else "MISSING"} '
                     f'(calculator: `{margin["arithmetic"]}`), '
                     f'10-K {result["latest_10k"]["accession"]}; independently inspect the revenue tag.')
    return '\n'.join(lines)


def build_report(data: dict, key: str, model: str, report_folder: Path) -> Path:
    if not key:
        raise ValueError('API_KEY required for Lab 03. Put the provider developer key into local .env.')
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError('Install requirements: python -m pip install -r requirements.txt') from exc
    api = OpenAI(api_key=key)
    k = data['filings']['10-K']
    q = data['filings']['10-Q']
    release = data['filings']['earnings_8-K']
    research_context = {
        'ticker': data['ticker'], 'company': data['name'],
        '10K_source': {'accession': k['accession'], 'excerpt_numbered_lines': data['excerpts']['10-K']},
        'earnings_release': {'accession': release['accession'],
                             'excerpt_numbered_lines': data['excerpts']['release_EX-99.1']},
    }
    financial_context = {
        'ticker': data['ticker'], 'company': data['name'],
        '10K_accession': k['accession'], '10Q_accession': q['accession'],
        'release_accession': release['accession'],
        'current_and_prior_facts': data['facts'], 'calculated_ratios': data['ratios'],
        'price': data['price'], 'price_date': data['price_date'],
        'candidate_release_lines': data['release_lines'],
        'human_transcribed_quarter_values_and_code_growth': data.get('quarterly'),
        'release_excerpt_numbered_lines': data['excerpts']['release_EX-99.1'],
        'peers': data['peers'],
    }
    research = call_role(api, model, 'Research Analyst', RESEARCH_SYSTEM,
                         'Draft sourced Overview, Market Positioning/Growth, Developments/Strategy.',
                         research_context, list(('overview', 'market_positioning_and_growth_outlook',
                                                 'future_developments_and_strategic_recommendations')))
    financial = call_role(api, model, 'Financial Analyst', FINANCIAL_SYSTEM,
                          'Draft statement/quarter/peers analysis and Valuation Insights using only code-calculated figures.',
                          financial_context, ['financial_analysis', 'valuation_insights'])
    advisor_context = {'research_analyst_output': research, 'financial_analyst_output': financial}
    advisor = call_role(api, model, 'Investment Advisor', INVESTMENT_SYSTEM,
                        'Make a provisional Buy/Hold/Sell thesis using one documented deciding number.',
                        advisor_context, ['investment_recommendation'])
    def sections():
        financial_analysis = financial.get('financial_analysis', '')
        overview = str(research.get('overview', ''))
        # Financial-analysis numbers appear in the Overview for core-claim visibility.
        return {**research, **financial, **advisor,
                'overview': overview + '\n\n### Financial statement and quarter analysis\n\n' + str(financial_analysis)}
    parts = sections()
    draft = compose(parts)
    manager_context = {'draft': draft, 'annual_evidence': data['facts'],
                       'calculator': data['ratios'], 'release_candidates': data['release_lines']}
    manager = call_role(api, model, 'Strategy Manager', MANAGER_SYSTEM,
                        'Check five-part template, source support and internal consistency.',
                        manager_context, {'status': 'PASS or REVISE', 'issues': []})
    corrections = []
    if str(manager.get('status', '')).upper() == 'REVISE':
        grouped: dict[str, list[str]] = {}
        for issue in manager.get('issues', []):
            if isinstance(issue, dict) and issue.get('role') in ('Research Analyst', 'Financial Analyst', 'Investment Advisor'):
                grouped.setdefault(issue['role'], []).append(str(issue.get('reason', 'Fix documented inconsistency')))
        role_defs = [
            ('Research Analyst', RESEARCH_SYSTEM, research_context,
             ['overview', 'market_positioning_and_growth_outlook', 'future_developments_and_strategic_recommendations']),
            ('Financial Analyst', FINANCIAL_SYSTEM, financial_context, ['financial_analysis', 'valuation_insights']),
            ('Investment Advisor', INVESTMENT_SYSTEM, advisor_context, ['investment_recommendation']),
        ]
        for role, instructions, context, expected in role_defs:
            if role not in grouped:
                continue
            revision = call_role(api, model, role, instructions, 'Revise only after Strategy Manager review.',
                                 context, expected, '; '.join(grouped[role]))
            corrections.append({'role': role, 'reason': grouped[role]})
            if role == 'Research Analyst':
                research = revision
            elif role == 'Financial Analyst':
                financial = revision
            else:
                advisor = revision
            advisor_context = {'research_analyst_output': research, 'financial_analyst_output': financial}
        parts = sections()
        draft = compose(parts)
    first = (f'Filings read: 10-K {k["accession"]} ({k["primary_url"]}); '
             f'10-Q {q["accession"]} ({q["primary_url"]}); '
             f'earnings 8-K {release["accession"]} ({release["primary_url"]}), '
             f'Exhibit 99.1 ({release["exhibit_url"]}); '
             f'companyfacts CIK{data["cik"]:010d}.')
    second = f'Run UTC: {data["run_utc"]} | Mode: FOUR-ROLE API | Model: {model}'
    text = '\n'.join([
        first, second, '', '# Equity research — ' + data['ticker'] + ' — ' + data['name'],
        '', '**Audit status: HUMAN VERIFICATION REQUIRED. Not investment advice.**',
        '', draft, '', evidence_appendix(data), '',
        '## Human audit and sign-off',
        'Human auditor: PENDING. Compare every source line and the eleven core claims before submission.',
        'Strategy Manager result: ' + str(manager.get('status')),
        'Revision requests: ' + json.dumps(corrections), '',
        'This is a learning exercise, not financial advice.',
        'AI assistance: ChatGPT and the OpenAI API. Human source verification and judgments are pending.',
        'Any remaining errors are my own.', ''
    ])
    report = report_folder / f'{data["ticker"]}_report.md'
    report.write_text(text, encoding='utf-8')
    (report_folder / 'role_outputs.json').write_text(
        json.dumps({'Research Analyst': research, 'Financial Analyst': financial,
                    'Investment Advisor': advisor, 'Strategy Manager': manager,
                    'revisions': corrections}, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Five-part report:', report)
    return report
