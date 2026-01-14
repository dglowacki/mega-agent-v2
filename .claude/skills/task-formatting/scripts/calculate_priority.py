#!/usr/bin/env python3
"""
Calculate task priority based on urgency, impact, and effort.

Usage:
    python calculate_priority.py --urgency 5 --impact 4 --effort 2 --format clickup
"""

import argparse
import json
from typing import Dict


def calculate_priority(urgency: int, impact: int, effort: int, format: str = 'clickup') -> Dict:
    """
    Calculate task priority score and level.

    Formula: Priority Score = (Urgency × 3) + (Impact × 2) + (Effort × -1)

    Args:
        urgency: 1-5 (how soon it needs to be done)
        impact: 1-5 (how many people/systems affected)
        effort: 1-5 (how much work required)
        format: Output format (clickup, linear, github)

    Returns:
        Dictionary with score, priority level, and recommendation
    """
    # Validate inputs
    for value, name in [(urgency, 'urgency'), (impact, 'impact'), (effort, 'effort')]:
        if not 1 <= value <= 5:
            raise ValueError(f"{name} must be between 1 and 5")

    # Calculate score
    score = (urgency * 3) + (impact * 2) + (effort * -1)

    # Map to priority level
    if score >= 15:
        priority = 1
        label = "Urgent"
        recommendation = "Address immediately - high urgency and impact"
    elif score >= 10:
        priority = 2
        label = "High"
        recommendation = "Schedule soon - significant impact or urgency"
    elif score >= 5:
        priority = 3
        label = "Normal"
        recommendation = "Include in regular sprint planning"
    else:
        priority = 4
        label = "Low"
        recommendation = "Backlog - low urgency and impact"

    # Adjust for format
    if format == 'linear':
        # Linear uses 0-4 with 0 = no priority
        if priority == 4:
            priority = 4  # Low
        elif priority == 3:
            priority = 3  # Normal
        elif priority == 2:
            priority = 2  # High
        else:
            priority = 1  # Urgent

    elif format == 'github':
        # GitHub uses labels
        label_map = {
            1: "priority: urgent",
            2: "priority: high",
            3: "priority: medium",
            4: "priority: low"
        }
        github_label = label_map[priority]
        return {
            'score': score,
            'priority': priority,
            'priority_label': github_label,
            'recommendation': recommendation,
            'factors': {
                'urgency': urgency,
                'impact': impact,
                'effort': effort
            }
        }

    return {
        'score': score,
        'priority': priority,
        'priority_label': label,
        'recommendation': recommendation,
        'factors': {
            'urgency': urgency,
            'impact': impact,
            'effort': effort
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Calculate task priority')
    parser.add_argument('--urgency', type=int, required=True, help='Urgency level (1-5)')
    parser.add_argument('--impact', type=int, required=True, help='Impact level (1-5)')
    parser.add_argument('--effort', type=int, required=True, help='Effort level (1-5)')
    parser.add_argument('--format', default='clickup', choices=['clickup', 'linear', 'github'], help='Output format')

    args = parser.parse_args()

    try:
        result = calculate_priority(args.urgency, args.impact, args.effort, args.format)
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
