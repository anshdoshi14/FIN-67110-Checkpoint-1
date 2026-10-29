"""Offline end-to-end structural test; does NOT certify live SEC correctness."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from sec_desk import perform_data_steps
from roles import build_report


class FakeSEC:
    def resolve(self, ticker):
        return {'TEST': (42, 'Example Holdings'), 'PEER': (99, 'Example Peer')}[ticker]

    def submissions(self, cik):
        a = '0000000042-26-000001' if cik == 42 else '0000000099-26-000001'
        records = [
            ('8-K', '0000000042-26-000003', '2026-10-20', '', 'earnings.htm', '2.02,9.01'),
            ('10-Q', '0000000042-26-000002', '2026-07-20', '2026-06-30', 'quarter.htm', ''),
            ('10-K', a, '2026-02-15', '2025-12-31', 'annual.htm', ''),
            ('10-K', '0000000042-25-000001', '2025-02-15', '2024-12-31', 'prior.htm', ''),
        ]
        if cik == 99:
            records = [('10-K', a, '2026-02-15', '2025-12-31', 'annual.htm', '')]
        return {'filings': {'recent': {
            'form': [r[0] for r in records], 'accessionNumber': [r[1] for r in records],
            'filingDate': [r[2] for r in records], 'reportDate': [r[3] for r in records],
            'primaryDocument': [r[4] for r in records], 'items': [r[5] for r in records],
            'acceptanceDateTime': ['2026-10-20T12:34:56'] * len(records),
        }}}

    def facts(self, cik):
        accn = '0000000042-26-000001' if cik == 42 else '0000000099-26-000001'
        def o(val, end, start=None):
            item = {'val': val, 'end': end, 'accn': accn, 'filed': '2026-02-15', 'form': '10-K'}
            if start:
                item['start'] = start
            return item
        def duration(v1, v2):
            return [o(v1, '2025-12-31', '2025-01-01'), o(v2, '2024-12-31', '2024-01-01')]
        def instant(v1, v2):
            return [o(v1, '2025-12-31'), o(v2, '2024-12-31')]
        tags = {
            'Revenues': duration(500, 400), 'OperatingIncomeLoss': duration(50, 40),
            'NetIncomeLoss': duration(20, 16), 'EarningsPerShareDiluted': duration(2, 1.6),
            'StockholdersEquity': instant(100, 80), 'LongTermDebtNoncurrent': instant(30, 25),
            'LongTermDebtCurrent': instant(5, 3),
            'NetCashProvidedByUsedInOperatingActivities': duration(55, 45),
            'PaymentsToAcquirePropertyPlantAndEquipment': duration(15, 12),
        }
        return {'facts': {'us-gaap': {
            tag: {'units': {'USD/shares' if tag == 'EarningsPerShareDiluted' else 'USD': values}}
            for tag, values in tags.items()
        }}}

    def fetch(self, url, json_mode=False):
        if url.endswith('-index.htm'):
            return '''<table class="tableFile"><tr><td>1</td><td>Earnings release</td>
            <td><a href="release.htm">release.htm</a></td><td>EX-99.1</td><td>10000</td></tr></table>'''
        if 'earnings.htm' in url:
            return '<html>Item 2.02 Results of Operations and Financial Condition</html>'
        if 'release.htm' in url:
            return '<html><table><tr><td>Total revenues</td><td>100</td><td>90</td></tr>' \
                   '<tr><td>Diluted earnings per share, GAAP</td><td>1.12</td><td>0.98</td></tr></table></html>'
        return '<html><h1>Item 1. Business</h1>Example operations<h1>Item 7. MD&A</h1>Margin discussion</html>'


def test_full_seven_step_pipeline_offline(tmp_path):
    data = perform_data_steps(FakeSEC(), 'TEST', ['PEER'], 40.0, tmp_path, price_date='2026-10-19')
    folder = Path(data['folder'])
    assert folder.name.startswith('Example_Holdings_TEST_')
    assert all((folder / item).exists() for item in (
        '10-K.txt', '10-Q.txt', 'earnings_8-K.txt', 'release_EX-99.1.txt',
        'facts.json', 'ratios.json', 'release_lines.json', 'peers.json'))
    assert data['ratios']['operating_margin']['value'] == 0.1
    assert data['ratios']['free_cash_flow']['value'] == 40
    assert data['ratios']['price_to_earnings']['value'] == 20
    assert len(data['release_lines']['revenue']) > 0
    assert 'PEER' in data['peers']


def test_model_calls_are_separate_and_report_has_five_sections(tmp_path, monkeypatch):
    import roles
    responses = [
        {'overview': 'Overview from 10-K', 'market_positioning_and_growth_outlook': 'Market notes',
         'future_developments_and_strategic_recommendations': 'Future notes'},
        {'financial_analysis': 'XBRL statements summary', 'valuation_insights': 'Valuation notes'},
        {'investment_recommendation': 'Hold, provisional, on sourced margin.'},
        {'status': 'PASS', 'issues': []},
    ]
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(responses.pop(0)))
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(OpenAI=lambda **kwargs:
                        SimpleNamespace(responses=SimpleNamespace(create=create))))
    data = perform_data_steps(FakeSEC(), 'TEST', ['PEER'], 40.0, tmp_path, price_date='2026-10-19')
    report = build_report(data, 'test-key-not-real', 'mock-model', Path(data['folder']))
    markdown = report.read_text()
    assert len(calls) == 4
    assert len([x for x in markdown.splitlines() if x.startswith('## ') and not x.startswith('## Source') and not x.startswith('## Human')]) == 5
    assert markdown.startswith('Filings read:')
    assert markdown.splitlines()[1].startswith('Run UTC:')
    assert 'HUMAN VERIFICATION REQUIRED' in markdown
