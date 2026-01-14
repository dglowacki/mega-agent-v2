#!/usr/bin/env python3
"""
Calculate readability scores for content.

Usage:
    python calculate_readability.py --input post.html --format html
"""

import argparse
import json
import re
from html.parser import HTMLParser
from typing import Dict


class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML."""

    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)


def extract_text(html: str) -> str:
    """Extract text from HTML."""
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def count_syllables(word: str) -> int:
    """Count syllables in a word (approximate)."""
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            count += 1
        previous_was_vowel = is_vowel

    # Adjust for silent e
    if word.endswith('e'):
        count -= 1

    # Ensure at least 1 syllable
    return max(1, count)


def calculate_readability(text: str) -> Dict:
    """
    Calculate readability scores using multiple metrics.

    Returns:
        Dictionary with readability scores
    """
    # Clean text
    text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace

    # Count words
    words = text.split()
    total_words = len(words)

    # Count sentences (rough approximation)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_sentences = len(sentences)

    # Count syllables
    total_syllables = sum(count_syllables(word) for word in words)

    # Prevent division by zero
    if total_words == 0 or total_sentences == 0:
        return {
            'error': 'Not enough content to analyze'
        }

    # Calculate averages
    avg_words_per_sentence = total_words / total_sentences
    avg_syllables_per_word = total_syllables / total_words
    avg_chars_per_word = sum(len(word) for word in words) / total_words

    # Flesch Reading Ease
    # Formula: 206.835 - 1.015(total words/total sentences) - 84.6(total syllables/total words)
    flesch_reading_ease = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)

    # Flesch-Kincaid Grade Level
    # Formula: 0.39(total words/total sentences) + 11.8(total syllables/total words) - 15.59
    flesch_kincaid_grade = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59

    # SMOG Index (simplified)
    # Formula: 1.0430 * sqrt(30 * (complex words / sentences)) + 3.1291
    # Complex words = 3+ syllables
    complex_words = sum(1 for word in words if count_syllables(word) >= 3)
    smog_index = 1.0430 * ((30 * complex_words / total_sentences) ** 0.5) + 3.1291

    # Determine readability level
    if flesch_reading_ease >= 90:
        level = "Very Easy (5th grade)"
        recommendation = "Excellent readability for general audience"
    elif flesch_reading_ease >= 80:
        level = "Easy (6th grade)"
        recommendation = "Very good readability"
    elif flesch_reading_ease >= 70:
        level = "Fairly Easy (7th grade)"
        recommendation = "Good readability"
    elif flesch_reading_ease >= 60:
        level = "Standard (8-9th grade)"
        recommendation = "Good readability for general audience"
    elif flesch_reading_ease >= 50:
        level = "Fairly Difficult (10-12th grade)"
        recommendation = "Consider simplifying complex sentences"
    elif flesch_reading_ease >= 30:
        level = "Difficult (College)"
        recommendation = "Too complex for general audience"
    else:
        level = "Very Difficult (Graduate)"
        recommendation = "Simplify content significantly"

    return {
        'flesch_reading_ease': round(flesch_reading_ease, 1),
        'flesch_kincaid_grade': round(flesch_kincaid_grade, 1),
        'smog_index': round(smog_index, 1),
        'avg_words_per_sentence': round(avg_words_per_sentence, 1),
        'avg_syllables_per_word': round(avg_syllables_per_word, 2),
        'avg_chars_per_word': round(avg_chars_per_word, 1),
        'total_words': total_words,
        'total_sentences': total_sentences,
        'total_syllables': total_syllables,
        'complex_words': complex_words,
        'readability_level': level,
        'recommendation': recommendation
    }


def main():
    parser = argparse.ArgumentParser(description='Calculate readability scores')
    parser.add_argument('--input', required=True, help='Input file')
    parser.add_argument('--format', default='html', choices=['html', 'text'], help='Input format')

    args = parser.parse_args()

    # Load content
    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract text if HTML
    if args.format == 'html':
        content = extract_text(content)

    # Calculate readability
    scores = calculate_readability(content)

    # Output
    print(json.dumps(scores, indent=2))


if __name__ == '__main__':
    main()
