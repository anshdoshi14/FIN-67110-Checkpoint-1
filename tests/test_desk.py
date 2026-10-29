from datetime import datetime
from sec_desk import (
    TAGS, calculate, extract_facts, filing_records, is_item_202, lines_of_interest,
    plain_text, _pick, supplement_current_debt_from_10k_note,
)
from sec_desk import Filing
from roles import FIVE_HEADINGS, compose, parse_json


def specimen(tag, values, unit='USD'):
    return {'units': {unit: values}}


def row(val, start=None, end='2026-08-30', accn='0000000001-26-000001', filed='2026-10-01'):
    record = {'val': val, 'end': end, 'accn': accn, 'filed': filed, 'form': '10-K'}
    if start:
        record['start'] = start
    return record


def test_latest_tag_and_fiscal_year_defeats_old_first_tag():
    # First candidate has stale revenue, second candidate matches newest 10-K.
    facts = {'facts': {'us-gaap': {
        'Revenues': specimen('Revenues', [row(500, '2024-09-01', end='2025-08-31')]),
        'RevenueFromContractWithCustomerExcludingAssessedTax': specimen('RevenueFromContractWithCustomerExcludingAssessedTax',
            [row(650, '2025-09-01')]),
    }}}
    chosen = _pick(facts, 'revenue', '2026-08-30', '0000000001-26-000001')
    assert chosen['value'] == 650
    assert chosen['tag'] == 'RevenueFromContractWithCustomerExcludingAssessedTax'


def test_broad_revenue_wins_tie_with_net_sales():
    facts = {'facts': {'us-gaap': {
        'Revenues': specimen('Revenues', [row(800, '2025-09-01')]),
        'RevenueFromContractWithCustomerExcludingAssessedTax': specimen('RevenueFromContractWithCustomerExcludingAssessedTax',
            [row(700, '2025-09-01')]),
    }}}
    assert _pick(facts, 'revenue', '2026-08-30', '0000000001-26-000001')['value'] == 800


def test_ratio_arithmetic_and_no_guess_missing_current_debt():
    cur = {'revenue': 200, 'operating_income': 30, 'net_income': 12,
           'equity': 100, 'long_term_debt_noncurrent': 50, 'long_term_debt_current': 10,
           'cash_from_operations': 45, 'capex': 18, 'diluted_eps': 4}
    prior = {'revenue': 160, 'equity': 80}
    facts = {'fields': {key: {'current': {'value': value},
                             'prior': {'value': prior[key]} if key in prior else None}
                        for key, value in cur.items()}}
    x = calculate(facts, 80)
    assert x['revenue_growth']['value'] == .25
    assert x['operating_margin']['value'] == .15
    assert abs(x['return_on_average_equity']['value'] - 12 / 90) < 1e-10
    assert x['debt_to_equity']['value'] == .6
    assert x['free_cash_flow']['value'] == 27
    assert x['price_to_earnings']['value'] == 20
    facts['fields']['long_term_debt_current']['current'] = None
    assert calculate(facts)['debt_to_equity']['value'] is None


def test_8k_requires_item_202():
    assert not is_item_202('1.01, 5.02', '<h1>item 5.02</h1>')
    assert is_item_202('2.02,9.01')
    assert is_item_202('', 'Item 2.02 Results of Operations')
    assert not is_item_202('12.02')


def test_document_table_rows_remain_line_readable():
    html = '<html><table><tr><td>Total revenue</td><td>1,234</td><td>1,111</td></tr>' \
           '<tr><td>Diluted earnings per share</td><td>$2.13</td></tr></table></html>'
    lines = plain_text(html)
    assert 'Total revenue | 1,234 | 1,111' in lines
    found = lines_of_interest(lines)
    assert found['revenue'][0]['line'] == 1
    assert '2.13' in found['diluted_eps'][0]['text']


def test_release_line_matcher_accepts_per_diluted_share_wording():
    found = lines_of_interest('Net income was $2.998 billion, $6.75 per diluted share.')
    assert found['diluted_eps'][0]['line'] == 1


def test_release_line_matcher_accepts_net_revenue_wording():
    found = lines_of_interest('Net revenue was $25,274 million this quarter.')
    assert found['revenue'][0]['line'] == 1


def test_filing_note_current_maturity_fallback_uses_explicit_line_and_scale():
    from sec_desk import DeskError
    import pytest
    data = {'fiscal_year_end': '2025-12-27', 'ten_k_accession': '0000077476-26-000007',
            'fields': {'long_term_debt_current': {'current': None, 'prior': None}},
            'cautions': ['long_term_debt_current: no matching annual us-gaap XBRL value in latest 10-K; inspect company extension tags and filing.']}
    source = 'Other line\nCurrent maturities of long-term debt | $ | 4,030 | | $ | 4,004 |'
    supplement_current_debt_from_10k_note(data, source, 2, 1_000_000)
    value = data['fields']['long_term_debt_current']['current']
    assert value['value'] == 4_030_000_000
    assert value['evidence_type'] == 'filing_note' and value['evidence_line'] == 2
    assert 'NOT an SEC XBRL' in data['cautions'][-1]
    with pytest.raises(DeskError):
        supplement_current_debt_from_10k_note(data, source, 2, 1_000_000)
    data['fields']['long_term_debt_current']['current'] = None
    with pytest.raises(DeskError):
        supplement_current_debt_from_10k_note(data, 'Other value | 123', 1, 1_000_000)


def test_five_part_report_and_json():
    assert compose({'overview': 'Test'}).count('## ') == len(FIVE_HEADINGS)
    assert parse_json('```json\n{"status":"PASS","issues":[]}\n```')['status'] == 'PASS'
