#!/usr/bin/env python3
"""
Merge data from multiple sources.

Usage:
    python merge_sources.py --sources app_store.json github.json skillz.json --strategy combine --output combined.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def load_source(file_path: str) -> Dict:
    """Load JSON data from file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def merge_combine(sources: List[Dict]) -> Dict:
    """
    Combine all sources into a single dictionary.

    Preserves all data from all sources.
    """
    combined = {
        'sources': [],
        'merged_at': datetime.now().isoformat(),
        'total_sources': len(sources)
    }

    for i, source in enumerate(sources):
        source_name = source.get('name', f'source_{i}')
        combined['sources'].append({
            'name': source_name,
            'data': source
        })

    return combined


def merge_average(sources: List[Dict]) -> Dict:
    """
    Average numeric fields across sources.

    Useful for calculating average metrics.
    """
    if not sources:
        return {}

    # Collect all numeric fields
    numeric_fields = {}
    counts = {}

    for source in sources:
        for key, value in source.items():
            if isinstance(value, (int, float)):
                if key not in numeric_fields:
                    numeric_fields[key] = 0
                    counts[key] = 0
                numeric_fields[key] += value
                counts[key] += 1

    # Calculate averages
    averaged = {}
    for key, total in numeric_fields.items():
        count = counts[key]
        averaged[key] = round(total / count, 2) if count > 0 else 0

    averaged['merged_at'] = datetime.now().isoformat()
    averaged['total_sources'] = len(sources)

    return averaged


def merge_latest(sources: List[Dict]) -> Dict:
    """
    Keep latest values based on timestamp.

    Requires each source to have a 'timestamp' or 'date' field.
    """
    if not sources:
        return {}

    # Sort by timestamp (newest first)
    def get_timestamp(source):
        timestamp = source.get('timestamp') or source.get('date') or source.get('created_at')
        if not timestamp:
            return datetime.min

        try:
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return timestamp
        except:
            return datetime.min

    sorted_sources = sorted(sources, key=get_timestamp, reverse=True)

    # Start with latest
    merged = sorted_sources[0].copy()
    merged['merged_at'] = datetime.now().isoformat()
    merged['total_sources'] = len(sources)

    return merged


def merge_sources(source_files: List[str], strategy: str = 'combine') -> Dict:
    """
    Merge data from multiple JSON sources.

    Args:
        source_files: List of JSON file paths
        strategy: Merge strategy (combine, average, latest)

    Returns:
        Merged data dictionary
    """
    # Load all sources
    sources = []
    for file_path in source_files:
        try:
            data = load_source(file_path)
            data['_source_file'] = Path(file_path).name
            sources.append(data)
        except Exception as e:
            print(f"⚠ Warning: Failed to load {file_path}: {str(e)}")

    if not sources:
        return {'error': 'No sources loaded'}

    # Merge based on strategy
    if strategy == 'combine':
        return merge_combine(sources)
    elif strategy == 'average':
        return merge_average(sources)
    elif strategy == 'latest':
        return merge_latest(sources)
    else:
        return {'error': f'Unknown strategy: {strategy}'}


def main():
    parser = argparse.ArgumentParser(description='Merge data from multiple sources')
    parser.add_argument('--sources', nargs='+', required=True, help='JSON source files')
    parser.add_argument('--strategy', default='combine', choices=['combine', 'average', 'latest'], help='Merge strategy')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Merge sources
    result = merge_sources(args.sources, args.strategy)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Merged data saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
