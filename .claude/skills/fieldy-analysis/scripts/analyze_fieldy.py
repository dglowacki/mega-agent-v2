#!/usr/bin/env python3
"""
Analyze Fieldy transcription data and calculate metrics.

Usage:
    python analyze_fieldy.py fieldy_2026-01-04.json --output analysis.json
"""

import json
import sys
from datetime import datetime
from collections import Counter


def parse_timestamp(ts_str):
    """Parse ISO timestamp string to datetime."""
    try:
        # Handle format with timezone
        if '+' in ts_str:
            ts_str = ts_str.split('+')[0]
        if '.' in ts_str:
            return datetime.fromisoformat(ts_str)
        return datetime.fromisoformat(ts_str)
    except:
        return None


def calculate_session_duration(transcription_segments):
    """Calculate total duration from transcription segments."""
    if not transcription_segments:
        return 0.0

    try:
        # Find earliest start and latest end
        starts = [seg.get('start', 0) for seg in transcription_segments if 'start' in seg]
        ends = [seg.get('end', 0) for seg in transcription_segments if 'end' in seg]

        if starts and ends:
            duration_seconds = max(ends) - min(starts)
            return duration_seconds / 60.0  # Convert to minutes
        return 0.0
    except:
        return 0.0


def count_words(text):
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())


def extract_keywords(text, top_n=10):
    """Extract top keywords from text."""
    if not text:
        return []

    # Simple keyword extraction (lowercase, split, filter short words)
    words = text.lower().split()
    words = [w.strip('.,!?;:()[]{}') for w in words]
    words = [w for w in words if len(w) > 4]  # Filter short words

    # Count frequency
    counter = Counter(words)
    return counter.most_common(top_n)


def analyze_fieldy_data(data):
    """Analyze Fieldy transcription data."""
    date = data.get('date', 'Unknown')
    transcriptions = data.get('transcriptions', [])

    # Initialize metrics
    total_sessions = len(transcriptions)
    total_duration = 0.0
    total_words = 0
    sessions = []
    all_text = ""
    timestamps = []

    # Process each session
    for trans in transcriptions:
        timestamp = trans.get('timestamp')
        full_text = trans.get('transcription', '')
        segments = trans.get('transcriptions', [])

        # Calculate duration
        duration = calculate_session_duration(segments)
        if duration == 0 and full_text:
            # Estimate from word count (150 words per minute)
            word_count = count_words(full_text)
            duration = word_count / 150.0

        # Count words
        word_count = count_words(full_text)

        # Track session
        session_info = {
            'timestamp': timestamp,
            'duration_minutes': round(duration, 2),
            'word_count': word_count,
            'segment_count': len(segments)
        }
        sessions.append(session_info)

        # Accumulate totals
        total_duration += duration
        total_words += word_count
        all_text += " " + full_text

        # Track timestamps
        dt = parse_timestamp(timestamp) if timestamp else None
        if dt:
            timestamps.append(dt)

    # Calculate averages
    avg_session_minutes = total_duration / total_sessions if total_sessions > 0 else 0
    avg_words_per_session = total_words / total_sessions if total_sessions > 0 else 0

    # Get first and last session times
    first_session = min(timestamps).isoformat() if timestamps else None
    last_session = max(timestamps).isoformat() if timestamps else None

    # Extract keywords
    keywords = extract_keywords(all_text, top_n=10)

    # Build analysis result
    result = {
        'date': date,
        'summary': {
            'total_sessions': total_sessions,
            'total_duration_minutes': round(total_duration, 1),
            'avg_session_minutes': round(avg_session_minutes, 1),
            'total_words': total_words,
            'avg_words_per_session': int(avg_words_per_session),
            'first_session': first_session,
            'last_session': last_session
        },
        'sessions': sessions,
        'keywords': [{'word': word, 'count': count} for word, count in keywords],
        'generated_at': datetime.now().isoformat()
    }

    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze Fieldy transcription data')
    parser.add_argument('input', help='Input Fieldy JSON file')
    parser.add_argument('--output', default='analysis.json', help='Output analysis file')
    args = parser.parse_args()

    # Load data
    with open(args.input) as f:
        data = json.load(f)

    # Analyze
    analysis = analyze_fieldy_data(data)

    # Save
    with open(args.output, 'w') as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    summary = analysis['summary']
    print(f"✓ Analyzed Fieldy data for {analysis['date']}")
    print(f"✓ Total sessions: {summary['total_sessions']}")
    print(f"✓ Total duration: {summary['total_duration_minutes']} minutes")
    print(f"✓ Average session: {summary['avg_session_minutes']} minutes")
    print(f"✓ Total words: {summary['total_words']:,}")
    print(f"✓ Saved to {args.output}")


if __name__ == '__main__':
    main()
