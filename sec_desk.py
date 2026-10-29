"""FIN 67110 Week 2: generic seven-step EDGAR data desk.

Usage:
    python desk.py TICKER --peers PEER1,PEER2 --price 123.45 --price-date YYYY-MM-DD

Nothing in the production data pipeline is company-specific. Missing SEC tags and
unverifiable release rows are reported as missing rather than guessed.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SEC_MAIN = 'https://www.sec.gov'
SEC_DATA = 'https://data.sec.gov'
HEADERS_BASE = {'Accept-Encoding': 'gzip, deflate', 'Accept': 'application/json, text/html, */*'}

# Ordered for comparable broad revenue first; see README definition warning.
TAGS: dict[str, list[str]] = {
    'revenue': ['Revenues', 'RevenueAndOtherIncome', 'SalesRevenueNet',
                'RevenueFromContractWithCustomerExcludingAssessedTax',
                'SalesRevenueGoodsNet'],
    'operating_income': ['OperatingIncomeLoss'],
    'net_income': ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'ProfitLoss'],
    'diluted_eps': ['EarningsPerShareDiluted'],
    'equity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
    'long_term_debt_noncurrent': ['LongTermDebtNoncurrent', 'LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations'],
    'long_term_debt_current': ['LongTermDebtCurrent', 'LongTermDebtAndCapitalLeaseObligationsCurrent',
                               'LongTermDebtAndFinanceLeaseObligationsCurrent'],
    'cash_from_operations': ['NetCashProvidedByUsedInOperatingActivities'],
    'capex': ['PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireProductiveAssets'],
}
INSTANT_FIELDS = {'equity', 'long_term_debt_noncurrent', 'long_term_debt_current'}


class DeskError(RuntimeError):
    pass


@dataclass
class Filing:
    form: str
    accession: str
    filing_date: str
    report_date: str
    accepted: str
    primary_document: str
    items: str
    cik: int
    index_url: str
    primary_url: str
    exhibit_url: str = ''


class SECClient:
    def __init__(self, user_agent: str, delay: float = 0.25):
        if not user_agent or '@' not in user_agent or 'Your Full Name' in user_agent:
            raise DeskError('Set SEC_USER_AGENT in .env to your real name and email.')
        self.session = requests.Session()
        self.session.headers.update({**HEADERS_BASE, 'User-Agent': user_agent})
        self.delay = delay
        self.last_request = 0.0

    def fetch(self, url: str, json_mode: bool = False):
        for attempt in range(4):
            delay = max(0, self.delay - (time.monotonic() - self.last_request))
            if delay:
                time.sleep(delay)
            self.last_request = time.monotonic()
            try:
                response = self.session.get(url, timeout=35)
                if response.status_code in (403, 429, 500, 502, 503, 504):
                    raise requests.HTTPError(f'HTTP {response.status_code} at {url}', response=response)
                response.raise_for_status()
                return response.json() if json_mode else response.text
            except (requests.RequestException, ValueError) as exc:
                if attempt == 3:
                    raise DeskError(f'SEC request failed: {url} ({exc}). Check User-Agent, network and SEC access.') from exc
                time.sleep(2 ** attempt)
        raise DeskError(f'Unexpected SEC request failure at {url}')

    def resolve(self, ticker: str):
        data = self.fetch(f'{SEC_MAIN}/files/company_tickers.json', True)
        target = ticker.upper().strip()
        for item in data.values():
            if item.get('ticker', '').upper() == target:
                return int(item['cik_str']), item['title']
        raise DeskError(f'Ticker {ticker} not found in SEC company_tickers.json.')

    def submissions(self, cik: int):
        return self.fetch(f'{SEC_DATA}/submissions/CIK{cik:010d}.json', True)

    def facts(self, cik: int):
        return self.fetch(f'{SEC_DATA}/api/xbrl/companyfacts/CIK{cik:010d}.json', True)


def filing_records(submissions: dict, cik: int) -> list[Filing]:
    recent = submissions.get('filings', {}).get('recent', {})
    n = len(recent.get('accessionNumber', []))
    records = []
    for i in range(n):
        def field(key):
            arr = recent.get(key, [])
            return str(arr[i]) if i < len(arr) and arr[i] is not None else ''
        accession = field('accessionNumber')
        primary = field('primaryDocument')
        folder = f'{SEC_MAIN}/Archives/edgar/data/{cik}/{accession.replace("-", "")}/'
        records.append(Filing(
            form=field('form'), accession=accession, filing_date=field('filingDate'),
            report_date=field('reportDate'), accepted=field('acceptanceDateTime'),
            primary_document=primary, items=field('items'), cik=cik,
            index_url=folder + accession + '-index.htm', primary_url=urljoin(folder, primary)
        ))
    return records


def is_item_202(items: str, text: str = '') -> bool:
    return bool(re.search(r'(?<!\d)2\.02(?!\d)', items)) or bool(
        re.search(r'Item\s*2\.02\b', text[:250000], re.IGNORECASE))


def select_filings(client: SECClient, records: list[Filing]) -> tuple[Filing, Filing, Filing, str]:
    k = next((r for r in records if r.form in ('10-K', '10-K/A') and r.form == '10-K'), None)
    q = next((r for r in records if r.form == '10-Q'), None)
    if not k or not q:
        raise DeskError('A latest 10-K or 10-Q was not present in EDGAR recent filings.')
    for record in records:
        if record.form != '8-K':
            continue
        # Verify the actual document instead of blindly taking the most recent 8-K.
        if record.items and not is_item_202(record.items):
            continue
        primary_text = client.fetch(record.primary_url)
        if is_item_202(record.items, primary_text):
            return k, q, record, primary_text
    raise DeskError('No earnings 8-K with Item 2.02 found in recent filings.')


def plain_text(document: str) -> str:
    """Preserve table rows, making release figures and quotes findable by line."""
    soup = BeautifulSoup(document, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    for table in list(soup.find_all('table')):
        rows = []
        for tr in table.find_all('tr'):
            cells = [' '.join(td.stripped_strings) for td in tr.find_all(['td', 'th'], recursive=False)]
            if any(cells):
                rows.append(' | '.join(cells))
        table.replace_with(soup.new_string('\n' + '\n'.join(rows) + '\n'))
    text = soup.get_text('\n')
    text = text.replace('\xa0', ' ')
    return '\n'.join(line.strip() for line in text.splitlines() if line.strip())


def exhibit_991(client: SECClient, filing: Filing) -> str:
    """Read the index's Documents table, which identifies EX-99.1 explicitly."""
    index_html = client.fetch(filing.index_url)
    soup = BeautifulSoup(index_html, 'html.parser')
    root = filing.primary_url.rsplit('/', 1)[0] + '/'
    for tr in soup.select('table.tableFile tr'):
        cells = tr.find_all('td')
        if len(cells) < 4:
            continue
        kind = cells[-2].get_text(' ', strip=True).upper().replace(' ', '')
        if re.fullmatch(r'EX-99(?:\.0?1)?', kind):
            anchor = cells[2].find('a', href=True)
            if anchor:
                href = anchor['href']
                if '/ixviewer/' in href:
                    href = href.split('doc=', 1)[-1]
                return urljoin(root, href) if not href.startswith('/') else SEC_MAIN + href
    # SEC document table variations. Do not silently treat the 8-K itself as a release.
    for a in soup.select('table.tableFile a[href]'):
        row = a.find_parent('tr')
        if row and re.search(r'EX[- ]?99[. ]?0?1', row.get_text(' ', strip=True), re.I):
            return urljoin(f'{SEC_MAIN}/', a.get('href'))
    return ''


def lines_of_interest(text: str) -> dict[str, list[dict]]:
    lines = text.splitlines()
    patterns = {
        'revenue': re.compile(r'(total\s+revenues?|net\s+revenue|net\s+sales|total\s+net\s+revenue)', re.I),
        # Releases vary between "diluted earnings per share", "per diluted
        # share", and a table row simply labeled "Diluted".  These are
        # candidate lines only; the human audit still determines GAAP status
        # and the correct quarter column.
        'diluted_eps': re.compile(
            r'(diluted\s+(?:net\s+)?(?:earnings|income|eps)'
            r'|(?:earnings|income)\s+per\s+(?:diluted\s+)?share'
            r'|per\s+diluted\s+share'
            r'|^\s*diluted\s*(?:\||$))', re.I),
    }
    out = {key: [] for key in patterns}
    for i, line in enumerate(lines, 1):
        for key, pattern in patterns.items():
            if pattern.search(line):
                out[key].append({'line': i, 'text': line[:1500]})
    return {k: v[:35] for k, v in out.items()}


def _records_for_tag(companyfacts: dict, tag: str, unit: str) -> list[dict]:
    item = companyfacts.get('facts', {}).get('us-gaap', {}).get(tag, {})
    return item.get('units', {}).get(unit, [])


def _annual(obs: dict, instant: bool) -> bool:
    if instant:
        return 'start' not in obs
    try:
        days = (datetime.fromisoformat(obs['end']) - datetime.fromisoformat(obs['start'])).days
        return 345 <= days <= 380
    except (ValueError, KeyError):
        return False


def _pick(companyfacts: dict, name: str, end: str, accession: str, strict_accession: bool = True) -> dict | None:
    """Same fiscal period end and, where possible, same 10-K as revenue.

    Candidate tag's latest *annual* fiscal end is used to rank viable tags;
    definition preference breaks ties (broad revenue beats net sales).
    """
    instant = name in INSTANT_FIELDS
    unit = 'USD/shares' if name == 'diluted_eps' else 'USD'
    candidates = []
    for preference, tag in enumerate(TAGS[name]):
        raw = [o for o in _records_for_tag(companyfacts, tag, unit) if o.get('form') == '10-K' and _annual(o, instant)]
        if not raw:
            continue
        latest = max(o['end'] for o in raw)
        matches = [o for o in raw if o.get('end') == end and (not strict_accession or o.get('accn') == accession)]
        if not matches:
            continue
        # tie-break: first broad definition when equally current, then latest filed observation
        matches.sort(key=lambda o: (o.get('accn') == accession, o.get('filed', '')), reverse=True)
        candidates.append((latest, -preference, matches[0], tag))
    if not candidates:
        return None
    _, _, row, tag = max(candidates, key=lambda item: (item[0], item[1]))
    return {'tag': tag, 'value': row['val'], 'unit': unit, 'start': row.get('start'),
            'end': row.get('end'), 'accession': row.get('accn'), 'filed': row.get('filed'),
            'form': row.get('form'), 'frame': row.get('frame')}


def extract_facts(companyfacts: dict, latest_k: Filing, k_records: list[Filing]) -> dict:
    end = latest_k.report_date
    if not end:
        raise DeskError('10-K has no fiscal year end (reportDate). Check EDGAR record.')
    prev_k = next((r for r in k_records if r.form == '10-K' and r.report_date and r.report_date < end), None)
    if prev_k:
        previous_end = prev_k.report_date
    else:
        # Choose a year-earlier annual revenue observation only if present, not a guessed date.
        possible = []
        for tag in TAGS['revenue']:
            possible.extend(o.get('end') for o in _records_for_tag(companyfacts, tag, 'USD')
                            if o.get('end', '') < end and o.get('form') == '10-K' and _annual(o, False))
        previous_end = max(possible) if possible else None
    output = {'fiscal_year_end': end, 'prior_fiscal_year_end': previous_end,
              'ten_k_accession': latest_k.accession, 'fields': {}, 'cautions': []}
    for name in TAGS:
        current = _pick(companyfacts, name, end, latest_k.accession)
        # 10-K normally provides comparable prior values. If not, fall back to a prior filing, disclosed.
        prior = _pick(companyfacts, name, previous_end, latest_k.accession) if previous_end else None
        if prior is None and previous_end:
            prior = _pick(companyfacts, name, previous_end, latest_k.accession, strict_accession=False)
        output['fields'][name] = {'current': current, 'prior': prior}
        if current is None:
            output['cautions'].append(f'{name}: no matching annual us-gaap XBRL value in latest 10-K; inspect company extension tags and filing.')
        if prior and prior['accession'] != latest_k.accession:
            output['cautions'].append(f'{name} prior year: drawn from a different 10-K accession {prior["accession"]}.')
    debt_tag = (output['fields']['long_term_debt_noncurrent']['current'] or {}).get('tag')
    if debt_tag in ('LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations'):
        output['cautions'].append('Debt tag can include current portion; check 10-K balance sheet before adding current debt to avoid double count.')
    if (output['fields']['revenue']['current'] or {}).get('tag') == 'RevenueFromContractWithCustomerExcludingAssessedTax':
        output['cautions'].append('Revenue uses contract-sales tag; verify it includes total revenue (e.g. membership/other income), not net sales only.')
    return output


def supplement_current_debt_from_10k_note(facts: dict, filing_text: str, line_number: int, scale: int) -> dict:
    """Add an explicitly selected 10-K current-maturities row when XBRL lacks it.

    The caller must provide the exact 1-based text line and its filing-table
    USD scale. The result remains flagged as filing-note evidence, not XBRL.
    """
    if scale not in (1, 1000, 1_000_000):
        raise DeskError('Debt-note scale must be 1, 1000, or 1000000 USD per table unit.')
    if facts['fields']['long_term_debt_current']['current'] is not None:
        raise DeskError('Current portion already came from XBRL. Do not apply a duplicate override.')
    lines = filing_text.splitlines()
    if line_number < 1 or line_number > len(lines):
        raise DeskError(f'10-K debt-note line {line_number} is outside the saved filing.')
    raw = lines[line_number - 1]
    label = raw.split('|', 1)[0].strip()
    if not re.search(r'(current maturities|current portion)\s+of\s+long[ -]term\s+debt', label, re.I):
        raise DeskError('Debt-note line must explicitly say current maturities/portion of long-term debt.')
    numbers = []
    for part in raw.split('|')[1:]:
        value = part.strip().replace(',', '')
        if re.fullmatch(r'\d+(?:\.\d+)?', value):
            numbers.append(float(value))
    if not numbers:
        raise DeskError('No labeled amount found in specified debt-note table line.')
    current = numbers[0] * scale
    facts['fields']['long_term_debt_current']['current'] = {
        'value': int(current) if current.is_integer() else current,
        'tag': '10K_NOTE_CURRENT_MATURITIES_NOT_XBRL',
        'unit': 'USD', 'start': None, 'end': facts['fiscal_year_end'],
        'accession': facts['ten_k_accession'], 'filed': None,
        'form': '10-K', 'frame': None, 'evidence_type': 'filing_note',
        'evidence_line': line_number, 'evidence_quote': raw, 'table_usd_scale': scale,
    }
    facts['cautions'] = [x for x in facts['cautions'] if not x.startswith('long_term_debt_current:')]
    facts['cautions'].append(
        f'Current debt portion sourced from saved 10-K note L{line_number:06d} '
        f'with USD scale {scale:,}, NOT an SEC XBRL concept; human must verify table units and definition.')
    return facts


def calculate(facts: dict, price: float | None = None) -> dict:
    fields = facts['fields']
    def v(name, which='current'):
        obj = fields[name][which]
        return None if obj is None else obj['value']
    result: dict[str, dict] = {}
    def add(name: str, answer, arithmetic: str, unit: str):
        result[name] = {'value': answer, 'arithmetic': arithmetic, 'unit': unit}
    def safe_div(a, b):
        return None if a is None or b in (None, 0) else a / b
    rev, prev_rev = v('revenue'), v('revenue', 'prior')
    op = v('operating_income')
    ni = v('net_income')
    eq, eq_prior = v('equity'), v('equity', 'prior')
    long_debt, current_debt = v('long_term_debt_noncurrent'), v('long_term_debt_current')
    cfo, capex, eps = v('cash_from_operations'), v('capex'), v('diluted_eps')
    grow = safe_div(rev - prev_rev, prev_rev) if rev is not None and prev_rev is not None else None
    add('revenue_growth', grow, f'({rev} - {prev_rev}) / {prev_rev}', 'fraction')
    add('operating_margin', safe_div(op, rev), f'{op} / {rev}', 'fraction')
    avg_equity = (eq + eq_prior) / 2 if eq is not None and eq_prior is not None else None
    add('return_on_average_equity', safe_div(ni, avg_equity), f'{ni} / (({eq} + {eq_prior}) / 2)', 'fraction')
    total_debt = (long_debt + current_debt) if long_debt is not None and current_debt is not None else None
    add('debt_to_equity', safe_div(total_debt, eq), f'({long_debt} + {current_debt}) / {eq}', 'ratio')
    add('free_cash_flow', cfo - capex if cfo is not None and capex is not None else None,
        f'{cfo} - {capex}', 'USD')
    add('price_to_earnings', safe_div(price, eps), f'{price} / {eps}', 'ratio')
    return result


def numbered_excerpt(text: str, markers: tuple[str, ...], char_budget: int = 18500) -> str:
    lines = text.splitlines()
    selected = set(range(min(160, len(lines))))
    for marker in markers:
        indexes = [i for i, line in enumerate(lines) if marker.casefold() in line.casefold()]
        # Prefer last match to avoid table of contents; cap contexts.
        for index in indexes[-3:]:
            selected.update(range(max(0, index - 3), min(len(lines), index + 85)))
    result = []
    length = 0
    for i in sorted(selected):
        row = f'L{i + 1:06d} | {lines[i][:500]}'
        if length + len(row) > char_budget:
            break
        result.append(row)
        length += len(row) + 1
    return '\n'.join(result)


def show_facts(facts: dict):
    print(f' Fiscal year end {facts["fiscal_year_end"]}; previous {facts["prior_fiscal_year_end"]}')
    for name, obj in facts['fields'].items():
        curr, prior = obj['current'], obj['prior']
        def one(value):
            if not value:
                return 'MISSING'
            return f'{value["value"]:,} [{value["unit"]}, {value["tag"]}, {value["end"]}, {value["accession"]}]'
        print(f'  {name}: FY {one(curr)}; PRIOR {one(prior)}')
    for caution in facts['cautions']:
        print('  CAUTION:', caution)


def show_ratios(ratios: dict):
    for k, v in ratios.items():
        answer = v['value']
        if answer is None:
            formatted = 'MISSING (source inputs not available)'
        elif v['unit'] == 'fraction':
            formatted = f'{answer:.2%}'
        else:
            formatted = f'{answer:,.4f}'
        print(f'  {k}: {formatted}  =  {v["arithmetic"]}')


def store_json(folder: Path, filename: str, value: Any):
    (folder / filename).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def perform_data_steps(client: SECClient, ticker: str, peers: list[str], price: float | None,
                       root: Path, single_step: int | None = None, price_date: str = '',
                       quarter_review_path: str = '', debt_note_line: int | None = None,
                       debt_note_scale: int | None = None) -> dict:
    """Run all data steps or stop after the selected step's prerequisites."""
    now = datetime.now(timezone.utc)
    def step(n: int, name: str):
        if single_step is None or single_step == n:
            print(f'\nSTEP {n} — {name}', flush=True)
    step(1, 'Resolve ticker to CIK')
    cik, name = client.resolve(ticker)
    slug = re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')[:55] or ticker.upper()
    results = root / f'{slug}_{ticker.upper()}_{now:%Y-%m-%d_%H%M%S}_UTC'
    results.mkdir(parents=True, exist_ok=False)
    if single_step in (None, 1):
        print(f'{ticker.upper()}: {name} / CIK {cik:010d}')
    if single_step == 1:
        store_json(results, 'ticker.json', {'ticker': ticker.upper(), 'name': name, 'cik': cik})
        print('Saved step 1:', results)
        return {'folder': str(results), 'ticker': ticker.upper(), 'name': name, 'cik': cik}
    step(2, 'Locate latest 10-K, 10-Q, and last Item 2.02 earnings 8-K')
    subs = client.submissions(cik)
    records = filing_records(subs, cik)
    k, q, release_8k, existing_8k_html = select_filings(client, records)
    filings = {'10-K': k, '10-Q': q, 'earnings_8-K': release_8k}
    for key, filing in filings.items():
        if single_step in (None, 2):
            print(f'{key}: {filing.accession} | EDGAR Accepted: {filing.accepted} | {filing.index_url}')
    store_json(results, 'filings.json', {key: asdict(value) for key, value in filings.items()})
    if single_step == 2:
        print('Saved step 2:', results)
        return {'folder': str(results), 'filings': {key: asdict(value) for key, value in filings.items()}}
    step(3, 'Download filing documents and 8-K Exhibit 99.1')
    documents = {}
    for key, filing in filings.items():
        raw = existing_8k_html if key == 'earnings_8-K' else client.fetch(filing.primary_url)
        documents[key] = plain_text(raw)
        (results / f'{key}.txt').write_text(documents[key], encoding='utf-8')
    url = exhibit_991(client, release_8k)
    if not url:
        raise DeskError(f'Cannot locate EX-99.1 via {release_8k.index_url}. Investigate manually; saved partial files in {results}.')
    release_8k.exhibit_url = url
    documents['release_EX-99.1'] = plain_text(client.fetch(url))
    (results / 'release_EX-99.1.txt').write_text(documents['release_EX-99.1'], encoding='utf-8')
    store_json(results, 'filings.json', {key: asdict(value) for key, value in filings.items()})
    if single_step in (None, 3):
        for key in documents:
            print(f'{key}: {len(documents[key]):,} characters saved')
        print('Exhibit 99.1 URL:', url)
    if single_step == 3:
        print('Saved step 3:', results)
        return {'folder': str(results), 'filings': {key: asdict(value) for key, value in filings.items()}}
    step(4, 'Companyfacts: current and prior comparable fiscal-year figures')
    companyfacts = client.facts(cik)
    facts = extract_facts(companyfacts, k, records)
    if debt_note_line is not None:
        if debt_note_scale is None:
            raise DeskError('--debt-note-scale must be supplied with --debt-note-line.')
        supplement_current_debt_from_10k_note(facts, documents['10-K'], debt_note_line, debt_note_scale)
    store_json(results, 'facts.json', facts)
    if single_step in (None, 4):
        show_facts(facts)
    if single_step == 4:
        print('Saved step 4:', results)
        return {'folder': str(results), 'facts': facts}
    step(5, 'Calculator (arithmetic printed, no LLM calculations)')
    ratios = calculate(facts, price)
    store_json(results, 'ratios.json', ratios)
    if single_step in (None, 5):
        show_ratios(ratios)
    if single_step == 5:
        print('Saved step 5:', results)
        return {'folder': str(results), 'facts': facts, 'ratios': ratios}
    step(6, 'Locate earnings release lines: quarter revenue and GAAP diluted EPS')
    release_lines = lines_of_interest(documents['release_EX-99.1'])
    store_json(results, 'release_lines.json', release_lines)
    quarterly = None
    if quarter_review_path:
        review = json.loads(Path(quarter_review_path).read_text(encoding='utf-8'))
        if review.get('ticker', '').upper() != ticker.upper():
            raise DeskError('Quarter review ticker does not match this run.')
        required = ('revenue_current', 'revenue_prior', 'diluted_eps_gaap', 'unit', 'revenue_line', 'eps_line')
        if any(review.get(key) is None for key in required):
            raise DeskError(f'Quarter review needs: {required}')
        if float(review['revenue_prior']) == 0:
            raise DeskError('Prior-quarter revenue cannot be zero for growth calculation.')
        release_text_lines = documents['release_EX-99.1'].splitlines()
        for evidence_key in ('revenue_line', 'eps_line'):
            n = int(review[evidence_key])
            if not 1 <= n <= len(release_text_lines):
                raise DeskError(f'{evidence_key} L{n} not present in saved EX-99.1 text.')
        quarterly = {**review, 'revenue_growth':
                     (float(review['revenue_current']) - float(review['revenue_prior'])) / float(review['revenue_prior']),
                     'arithmetic': f"({review['revenue_current']} - {review['revenue_prior']}) / {review['revenue_prior']}",
                     'source': release_8k.exhibit_url, 'release_accession': release_8k.accession,
                     'status': 'human-transcribed; independently audit periods and GAAP designation'}
        store_json(results, 'quarter_review.json', quarterly)
    if single_step in (None, 6):
        if quarterly:
            print('  Human transcribed quarter values and arithmetic:', quarterly)
        for kind, rows in release_lines.items():
            print(' ', kind)
            for row in rows[:12]:
                print(f'   L{row["line"]}: {row["text"]}')
        print('  NOTE: Potential lines are evidence candidates; verify quarter columns and GAAP definition manually.')
    if single_step == 6:
        print('Saved step 6:', results)
        return {'folder': str(results), 'release_lines': release_lines, 'quarterly': quarterly}
    step(7, 'Repeat same current-year data and operating-margin definitions for peers')
    peer_results = {}
    for peer in peers:
        peer_cik, peer_name = client.resolve(peer)
        peer_records = filing_records(client.submissions(peer_cik), peer_cik)
        peer_k = next((r for r in peer_records if r.form == '10-K'), None)
        if not peer_k:
            raise DeskError(f'Missing 10-K for peer {peer}.')
        peer_facts = extract_facts(client.facts(peer_cik), peer_k, peer_records)
        peer_ratios = calculate(peer_facts)
        peer_results[peer] = {'ticker': peer, 'name': peer_name,
                              'latest_10k': asdict(peer_k), 'facts': peer_facts,
                              'operating_margin': peer_ratios['operating_margin']}
        if single_step in (None, 7):
            print(f' {peer} ({peer_name}), FY {peer_facts["fiscal_year_end"]}:')
            for f in ['revenue', 'operating_income']:
                print(f'    {f}: {peer_facts["fields"][f]["current"]}')
            print('    margin:', peer_ratios['operating_margin'])
    store_json(results, 'peers.json', peer_results)
    data = {
        'ticker': ticker.upper(), 'name': name, 'cik': cik, 'run_utc': now.isoformat(),
        'price': price, 'price_date': price_date, 'folder': str(results), 'quarterly': quarterly,
        'filings': {key: asdict(value) for key, value in filings.items()},
        'facts': facts, 'ratios': ratios, 'release_lines': release_lines,
        'peers': peer_results,
        'excerpts': {
            '10-K': numbered_excerpt(documents['10-K'], ('item 1. business', 'item 7.', 'management\'s discussion')),
            '10-Q': numbered_excerpt(documents['10-Q'], ('item 2.', 'management\'s discussion'), 5000),
            'release_EX-99.1': numbered_excerpt(documents['release_EX-99.1'],
                ('total revenue', 'net sales', 'diluted', 'quarter', 'three months ended'), 26000),
        },
    }
    # Include the bounded source excerpts so a failed model call can be retried
    # from this manifest without repeating the SEC retrieval steps.
    store_json(results, 'run_manifest.json', data)
    print('\nSaved data folder:', results)
    return data
