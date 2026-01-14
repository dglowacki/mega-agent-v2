#!/usr/bin/env python3
"""
Aggregate and transform data for reporting.

Usage:
    python aggregate_data.py input.json --group-by date --metrics count,sum --output aggregated.json
"""

import json
import sys
from datetime import datetime
from collections import defaultdict
from typing import Any, Dict, List


def parse_filter(filter_expr: str) -> callable:
    """Parse filter expression and return filter function."""
    if not filter_expr:
        return lambda x: True

    # Simple field=value filter
    if '=' in filter_expr:
        field, value = filter_expr.split('=', 1)
        return lambda item: str(item.get(field, '')) == value

    # Greater than filter (field>value)
    if '>' in filter_expr:
        field, value = filter_expr.split('>', 1)
        return lambda item: float(item.get(field, 0)) > float(value)

    # Less than filter (field<value)
    if '<' in filter_expr:
        field, value = filter_expr.split('<', 1)
        return lambda item: float(item.get(field, 0)) < float(value)

    # Default: always true
    return lambda x: True


def aggregate_by_field(data: List[Dict], group_by: str, metrics: List[str]) -> List[Dict]:
    """Aggregate data by a field."""
    groups = defaultdict(list)

    # Group items
    for item in data:
        key = item.get(group_by, 'unknown')
        groups[key].append(item)

    # Calculate metrics for each group
    results = []
    for key, items in groups.items():
        result = {
            group_by: key,
            'count': len(items)
        }

        # Calculate requested metrics
        for metric in metrics:
            if metric == 'count':
                continue  # Already added

            elif metric == 'sum':
                # Sum all numeric fields
                numeric_sums = defaultdict(float)
                for item in items:
                    for field, value in item.items():
                        if isinstance(value, (int, float)):
                            numeric_sums[field] += value
                for field, total in numeric_sums.items():
                    result[f'{field}_sum'] = total

            elif metric == 'avg':
                # Average all numeric fields
                numeric_avgs = defaultdict(list)
                for item in items:
                    for field, value in item.items():
                        if isinstance(value, (int, float)):
                            numeric_avgs[field].append(value)
                for field, values in numeric_avgs.items():
                    if values:
                        result[f'{field}_avg'] = sum(values) / len(values)

            elif metric == 'min':
                # Minimum of numeric fields
                numeric_mins = defaultdict(list)
                for item in items:
                    for field, value in item.items():
                        if isinstance(value, (int, float)):
                            numeric_mins[field].append(value)
                for field, values in numeric_mins.items():
                    if values:
                        result[f'{field}_min'] = min(values)

            elif metric == 'max':
                # Maximum of numeric fields
                numeric_maxs = defaultdict(list)
                for item in items:
                    for field, value in item.items():
                        if isinstance(value, (int, float)):
                            numeric_maxs[field].append(value)
                for field, values in numeric_maxs.items():
                    if values:
                        result[f'{field}_max'] = max(values)

        results.append(result)

    return results


def calculate_trends(current_data: List[Dict], previous_data: List[Dict], key_field: str) -> List[Dict]:
    """Calculate trends by comparing current to previous data."""
    # Create lookup for previous data
    previous_lookup = {item[key_field]: item for item in previous_data if key_field in item}

    results = []
    for current in current_data:
        key = current.get(key_field)
        result = current.copy()

        if key in previous_lookup:
            previous = previous_lookup[key]

            # Calculate changes for numeric fields
            for field, value in current.items():
                if isinstance(value, (int, float)) and field in previous:
                    prev_value = previous[field]
                    if isinstance(prev_value, (int, float)):
                        delta = value - prev_value
                        percent_change = (delta / prev_value * 100) if prev_value != 0 else 0

                        result[f'{field}_delta'] = delta
                        result[f'{field}_percent'] = round(percent_change, 1)
                        result[f'{field}_trend'] = 'up' if delta > 0 else 'down' if delta < 0 else 'neutral'

        results.append(result)

    return results


def pivot_data(data: List[Dict], row_field: str, col_field: str, value_field: str, agg: str = 'sum') -> Dict:
    """Pivot data table."""
    # Get unique values for rows and columns
    rows = sorted(set(item[row_field] for item in data if row_field in item))
    cols = sorted(set(item[col_field] for item in data if col_field in item))

    # Create pivot table
    pivot = {
        'rows': rows,
        'columns': cols,
        'data': {}
    }

    for row in rows:
        pivot['data'][row] = {}
        for col in cols:
            # Filter items for this row/col combination
            items = [item for item in data
                    if item.get(row_field) == row and item.get(col_field) == col]

            # Calculate aggregate
            if not items:
                value = 0
            elif agg == 'sum':
                value = sum(item.get(value_field, 0) for item in items)
            elif agg == 'avg':
                values = [item.get(value_field, 0) for item in items]
                value = sum(values) / len(values) if values else 0
            elif agg == 'count':
                value = len(items)
            elif agg == 'min':
                values = [item.get(value_field, 0) for item in items]
                value = min(values) if values else 0
            elif agg == 'max':
                values = [item.get(value_field, 0) for item in items]
                value = max(values) if values else 0
            else:
                value = 0

            pivot['data'][row][col] = value

    return pivot


def format_for_report(data: List[Dict], title: str = "Data Report") -> Dict:
    """Format aggregated data for report generation."""
    if not data:
        return {
            'title': title,
            'subtitle': datetime.now().strftime("%B %d, %Y"),
            'metrics': [],
            'sections': []
        }

    # Calculate summary metrics
    metrics = []

    # Count metric
    metrics.append({
        'label': 'Total Items',
        'value': str(len(data))
    })

    # Numeric field metrics
    numeric_fields = {}
    for item in data:
        for field, value in item.items():
            if isinstance(value, (int, float)) and not field.endswith(('_delta', '_percent', '_avg', '_sum', '_min', '_max')):
                if field not in numeric_fields:
                    numeric_fields[field] = []
                numeric_fields[field].append(value)

    for field, values in list(numeric_fields.items())[:3]:  # Top 3 numeric fields
        if values:
            metrics.append({
                'label': f'Total {field.replace("_", " ").title()}',
                'value': f'{sum(values):,.0f}'
            })

    # Create data table section
    sections = [{
        'title': 'Data',
        'type': 'table',
        'data': {
            'columns': list(data[0].keys()) if data else [],
            'rows': data
        }
    }]

    return {
        'title': title,
        'subtitle': datetime.now().strftime("%B %d, %Y"),
        'metrics': metrics,
        'sections': sections
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Aggregate and transform data')
    parser.add_argument('input', help='Input JSON data file')
    parser.add_argument('--group-by', help='Field to group by')
    parser.add_argument('--metrics', default='count',
                       help='Comma-separated metrics (count,sum,avg,min,max)')
    parser.add_argument('--filter', help='Filter expression (e.g., status=active)')
    parser.add_argument('--sort', help='Field to sort by')
    parser.add_argument('--sort-desc', action='store_true', help='Sort descending')
    parser.add_argument('--pivot', help='Pivot table: row_field,col_field,value_field,agg')
    parser.add_argument('--format-report', action='store_true',
                       help='Format output for report generation')
    parser.add_argument('--title', default='Data Report', help='Report title (with --format-report)')
    parser.add_argument('--output', default='aggregated.json', help='Output file')
    args = parser.parse_args()

    # Load input data
    with open(args.input) as f:
        input_data = json.load(f)

    # Ensure data is a list
    if isinstance(input_data, dict):
        if 'data' in input_data:
            data = input_data['data']
        elif 'items' in input_data:
            data = input_data['items']
        else:
            # Convert dict to list of items
            data = [input_data]
    else:
        data = input_data

    # Apply filter
    if args.filter:
        filter_fn = parse_filter(args.filter)
        data = [item for item in data if filter_fn(item)]
        print(f"✓ Filtered to {len(data)} items")

    # Perform aggregation
    result = data

    if args.group_by:
        metrics = args.metrics.split(',')
        result = aggregate_by_field(data, args.group_by, metrics)
        print(f"✓ Grouped by {args.group_by}, {len(result)} groups")

    if args.pivot:
        parts = args.pivot.split(',')
        if len(parts) < 3:
            print("Error: --pivot requires row_field,col_field,value_field[,agg]")
            return 1
        row_field, col_field, value_field = parts[:3]
        agg = parts[3] if len(parts) > 3 else 'sum'
        result = pivot_data(data, row_field, col_field, value_field, agg)
        print(f"✓ Pivoted data: {len(result.get('rows', []))} rows × {len(result.get('columns', []))} cols")

    # Sort
    if args.sort and isinstance(result, list):
        result.sort(key=lambda x: x.get(args.sort, 0), reverse=args.sort_desc)
        print(f"✓ Sorted by {args.sort}")

    # Format for report
    if args.format_report and isinstance(result, list):
        result = format_for_report(result, args.title)
        print(f"✓ Formatted for report generation")

    # Save output
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"✓ Saved to {args.output}")


if __name__ == '__main__':
    main()
