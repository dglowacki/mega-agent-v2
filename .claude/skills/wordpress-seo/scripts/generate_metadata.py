#!/usr/bin/env python3
"""
Generate SEO metadata for WordPress posts.

Usage:
    python generate_metadata.py --title "My Post" --content post.html --keywords "react,javascript" --output metadata.json
"""

import argparse
import json
import re
from html.parser import HTMLParser


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


def generate_title_tag(title: str, primary_keyword: str = None) -> str:
    """
    Generate optimized title tag (50-60 characters).

    Pattern: Primary Keyword | Brand/Benefit | Year
    """
    # Clean title
    title = title.strip()

    # Add year if not present
    current_year = "2026"
    if current_year not in title:
        title = f"{title} | {current_year} Guide"

    # Ensure keyword is in title
    if primary_keyword and primary_keyword.lower() not in title.lower():
        title = f"{primary_keyword.title()} - {title}"

    # Truncate to 60 characters
    if len(title) > 60:
        title = title[:57] + "..."

    return title


def generate_meta_description(content: str, keywords: list, max_length: int = 160) -> str:
    """
    Generate meta description (150-160 characters).

    Includes:
    - Primary keyword
    - Secondary keywords
    - Call-to-action or benefit
    """
    # Extract first few sentences
    text = extract_text(content) if '<' in content else content
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Start with first sentence
    description = sentences[0] if sentences else ''

    # Add second sentence if room
    if len(sentences) > 1 and len(description) + len(sentences[1]) < max_length - 20:
        description += '. ' + sentences[1]

    # Ensure keywords are present
    for keyword in keywords[:2]:  # Primary + one secondary
        if keyword.lower() not in description.lower():
            # Try to naturally integrate
            if len(description) + len(keyword) < max_length - 10:
                description += f'. {keyword.title()} explained.'

    # Truncate to max length
    if len(description) > max_length:
        description = description[:max_length - 3] + "..."

    return description


def generate_slug(title: str) -> str:
    """
    Generate URL slug from title.

    Rules:
    - Lowercase
    - Replace spaces with hyphens
    - Remove special characters
    - Maximum 5-7 words
    """
    # Convert to lowercase
    slug = title.lower()

    # Remove special characters
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)

    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)

    # Remove duplicate hyphens
    slug = re.sub(r'-+', '-', slug)

    # Limit to 5-7 words
    words = slug.split('-')[:7]
    slug = '-'.join(words)

    return slug.strip('-')


def extract_keywords(content: str, primary_keywords: list) -> list:
    """
    Extract and suggest keywords from content.
    """
    # Extract text
    text = extract_text(content) if '<' in content else content
    text = text.lower()

    # Add primary keywords
    keywords = list(primary_keywords)

    # Common keyword suffixes/variations
    variations = ['tutorial', 'guide', 'tips', 'examples', 'beginners', 'how to']

    for keyword in primary_keywords:
        for variation in variations:
            combined = f"{keyword} {variation}"
            if combined not in keywords and combined in text:
                keywords.append(combined)

    # Limit to 5 keywords
    return keywords[:5]


def generate_metadata(title: str, content: str, keywords: list) -> dict:
    """
    Generate complete SEO metadata for WordPress post.

    Args:
        title: Post title
        content: Post content (HTML or text)
        keywords: List of target keywords

    Returns:
        Dictionary with metadata fields
    """
    primary_keyword = keywords[0] if keywords else None

    # Generate title tag
    title_tag = generate_title_tag(title, primary_keyword)

    # Generate meta description
    meta_description = generate_meta_description(content, keywords)

    # Generate slug
    slug = generate_slug(title)

    # Extract all keywords
    all_keywords = extract_keywords(content, keywords)

    # Generate Open Graph metadata
    og_title = title if len(title) <= 60 else title[:57] + "..."
    og_description = meta_description

    return {
        'title_tag': title_tag,
        'meta_description': meta_description,
        'keywords': all_keywords,
        'slug': slug,
        'og_title': og_title,
        'og_description': og_description,
        'og_type': 'article',
        'twitter_card': 'summary_large_image'
    }


def main():
    parser = argparse.ArgumentParser(description='Generate SEO metadata')
    parser.add_argument('--title', required=True, help='Post title')
    parser.add_argument('--content', required=True, help='Post content file')
    parser.add_argument('--keywords', required=True, help='Comma-separated keywords')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Load content
    with open(args.content, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')]

    # Generate metadata
    metadata = generate_metadata(args.title, content, keywords)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Metadata saved to {args.output}")
    else:
        print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
