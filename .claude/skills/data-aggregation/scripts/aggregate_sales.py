#!/usr/bin/env python3
"""
Aggregate App Store sales data.

Usage:
    python aggregate_sales.py --input sales_reports/ --period week --output aggregated.json
"""

import argparse
import csv
import gzip
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


def parse_tsv_report(file_path: Path) -> List[Dict[str, Any]]:
    """Parse App Store Connect TSV sales report."""
    records = []

    # Check if gzipped
    if file_path.suffix == '.gz':
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            records = list(reader)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            records = list(reader)

    return records


def aggregate_by_time(records: List[Dict], period: str = 'day') -> Dict:
    """Aggregate records by time period."""
    aggregated = defaultdict(lambda: {
        'downloads': 0,
        'revenue': 0.0,
        'updates': 0
    })

    for record in records:
        # Parse date
        date_str = record.get('Begin Date', '')
        if not date_str:
            continue

        date = datetime.strptime(date_str, '%m/%d/%Y')

        # Determine period key
        if period == 'day':
            key = date.strftime('%Y-%m-%d')
        elif period == 'week':
            # Start of week
            start = date - timedelta(days=date.weekday())
            key = start.strftime('%Y-%m-%d')
        elif period == 'month':
            key = date.strftime('%Y-%m')
        else:
            key = date_str

        # Aggregate metrics
        units = int(record.get('Units', 0))
        proceeds = float(record.get('Developer Proceeds', 0))

        aggregated[key]['downloads'] += units
        aggregated[key]['revenue'] += proceeds

        # Count updates vs new downloads
        product_type = record.get('Product Type Identifier', '')
        if 'Update' in product_type:
            aggregated[key]['updates'] += units

    return dict(aggregated)


def aggregate_by_app(records: List[Dict]) -> Dict:
    """Aggregate records by app."""
    aggregated = defaultdict(lambda: {
        'name': '',
        'sku': '',
        'downloads': 0,
        'revenue': 0.0,
        'updates': 0,
        'countries': set()
    })

    for record in records:
        sku = record.get('SKU', 'unknown')
        title = record.get('Title', 'Unknown App')
        country = record.get('Country Code', '')

        units = int(record.get('Units', 0))
        proceeds = float(record.get('Developer Proceeds', 0))

        aggregated[sku]['name'] = title
        aggregated[sku]['sku'] = sku
        aggregated[sku]['downloads'] += units
        aggregated[sku]['revenue'] += proceeds

        if country:
            aggregated[sku]['countries'].add(country)

        product_type = record.get('Product Type Identifier', '')
        if 'Update' in product_type:
            aggregated[sku]['updates'] += units

    # Convert sets to lists
    result = {}
    for sku, data in aggregated.items():
        data['countries'] = sorted(list(data['countries']))
        result[sku] = data

    return result


def aggregate_sales(input_path: str, period: str = 'day', group_by: str = 'time') -> Dict:
    """
    Aggregate sales data from TSV files.

    Args:
        input_path: Path to file or directory
        period: Time period (day, week, month)
        group_by: Grouping method (time, app, country)

    Returns:
        Aggregated data dictionary
    """
    path = Path(input_path)
    records = []

    # Load records
    if path.is_file():
        records = parse_tsv_report(path)
    elif path.is_dir():
        # Load all TSV/gz files in directory
        for file_path in path.glob('*.txt*'):
            if file_path.suffix in ['.txt', '.gz']:
                records.extend(parse_tsv_report(file_path))

    if not records:
        return {'error': 'No records found'}

    # Aggregate based on grouping
    if group_by == 'time':
        data = aggregate_by_time(records, period)
        return {
            'period': period,
            'data': data,
            'total_records': len(records)
        }
    elif group_by == 'app':
        data = aggregate_by_app(records)
        totals = {
            'total_downloads': sum(app['downloads'] for app in data.values()),
            'total_revenue': sum(app['revenue'] for app in data.values()),
            'total_apps': len(data)
        }
        return {
            'apps': data,
            'totals': totals,
            'total_records': len(records)
        }
    else:
        return {'error': f'Unknown grouping: {group_by}'}


def main():
    parser = argparse.ArgumentParser(description='Aggregate App Store sales data')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--period', default='day', choices=['day', 'week', 'month'], help='Time period')
    parser.add_argument('--group-by', default='time', choices=['time', 'app', 'country'], help='Grouping method')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Aggregate
    result = aggregate_sales(args.input, args.period, args.group_by)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Aggregated data saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
