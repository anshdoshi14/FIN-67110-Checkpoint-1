"""Entry point for Week 2 desk and model reporting."""
import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sec_desk import DeskError, SECClient, numbered_excerpt, perform_data_steps


def main(argv=None):
    load_dotenv()
    parser = argparse.ArgumentParser(description='FIN 67110 Week 2 seven-step EDGAR + four-role desk')
    parser.add_argument('ticker', help='Any SEC-listed company ticker')
    parser.add_argument('--peers', default='', help='Comma-separated tickers, e.g. WMT,TGT,BJ')
    parser.add_argument('--price', type=float, help='Official share price before release, supplied by user')
    parser.add_argument('--price-date', default='', help='YYYY-MM-DD date of official share price')
    parser.add_argument('--step', type=int, choices=range(1, 8), metavar='1..7',
                        help='Print one selected step; prerequisites still run and artifacts are saved')
    parser.add_argument('--quarter-review', default='',
                        help='Optional manually transcribed EX-99.1 quarter values JSON for calculator')
    parser.add_argument('--debt-note-line', type=int,
                        help='Optional 10-K line for current maturities when no SEC XBRL tag exists')
    parser.add_argument('--debt-note-scale', type=int, choices=(1, 1000, 1000000),
                        help='USD per debt-note table unit; required with --debt-note-line')
    parser.add_argument('--data-only', action='store_true', help='Lab 02: do not call model API')
    parser.add_argument('--output', default='runs', help='Where to save run folders')
    parser.add_argument('--report-from', default='', metavar='RUN_FOLDER',
                        help='Retry Lab 03 roles from a saved run_manifest.json without re-fetching SEC data')
    args = parser.parse_args(argv)
    if args.price is not None and args.price <= 0:
        parser.error('--price must be positive')
    if (args.debt_note_line is None) != (args.debt_note_scale is None):
        parser.error('--debt-note-line and --debt-note-scale must be supplied together')
    if args.debt_note_line is not None and args.debt_note_line < 1:
        parser.error('--debt-note-line must be a positive 1-based line number')
    if args.price is not None and not args.price_date:
        print('CAUTION: --price-date is absent. Record the official close date before auditing P/E.')
    peers = [s.strip().upper() for s in args.peers.split(',') if s.strip()]
    if args.report_from:
        manifest = Path(args.report_from) / 'run_manifest.json'
        if not manifest.is_file():
            parser.error(f'--report-from must name a run folder containing run_manifest.json: {args.report_from}')
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if data.get('ticker') != args.ticker.upper():
            parser.error(f'Ticker {args.ticker.upper()} does not match saved run ticker {data.get("ticker")}.')
        if args.data_only or args.step is not None:
            parser.error('--report-from is for a full Lab 03 report retry, not --data-only or --step mode.')
        # Older manifests omitted excerpts to keep their JSON small. Rebuild
        # them from the saved source texts so a failed model run is retryable
        # without another SEC download.
        if 'excerpts' not in data:
            run_folder = Path(args.report_from)
            data['excerpts'] = {
                '10-K': numbered_excerpt((run_folder / '10-K.txt').read_text(encoding='utf-8'),
                                         ('item 1. business', 'item 7.', "management's discussion")),
                '10-Q': numbered_excerpt((run_folder / '10-Q.txt').read_text(encoding='utf-8'),
                                         ('item 2.', "management's discussion"), 5000),
                'release_EX-99.1': numbered_excerpt(
                    (run_folder / 'release_EX-99.1.txt').read_text(encoding='utf-8'),
                    ('total revenue', 'net sales', 'diluted', 'quarter', 'three months ended'), 26000),
            }
            manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        from roles import build_report
        build_report(data, os.getenv('API_KEY', ''), os.getenv('MODEL_NAME', 'gpt-4.1-mini'),
                     Path(args.report_from))
        return data
    client = SECClient(os.getenv('SEC_USER_AGENT', ''))
    data = perform_data_steps(client, args.ticker.upper(), peers, args.price,
                              Path(args.output), args.step, args.price_date, args.quarter_review,
                              args.debt_note_line, args.debt_note_scale)
    if args.data_only or args.step is not None:
        print('Data-only / single-step mode; report not generated.')
    else:
        from roles import build_report
        build_report(data, os.getenv('API_KEY', ''), os.getenv('MODEL_NAME', 'gpt-4.1-mini'),
                     Path(data['folder']))
    return data


if __name__ == '__main__':
    try:
        main()
    except (DeskError, RuntimeError, ValueError) as exc:
        raise SystemExit(f'ERROR: {exc}')
