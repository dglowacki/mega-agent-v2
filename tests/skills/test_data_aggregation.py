"""
Tests for data-aggregation skill.
"""

import pytest
import json
from pathlib import Path
import sys

# Add skills to path
SKILLS_PATH = Path(__file__).parent.parent.parent / '.claude' / 'skills' / 'data-aggregation' / 'scripts'
sys.path.insert(0, str(SKILLS_PATH))


class TestDataAggregation:
    """Test data aggregation skill scripts."""

    def test_aggregate_commits(self, sample_commits_data, tmp_path):
        """Test aggregate_commits.py script."""
        from aggregate_commits import aggregate_commits

        result = aggregate_commits(sample_commits_data, period='day')

        assert 'summary' in result
        assert result['summary']['total_commits'] == 2
        assert result['summary']['total_contributors'] == 2

        assert 'by_author' in result
        assert 'John Doe' in result['by_author']
        assert result['by_author']['John Doe']['commits'] == 1

    def test_aggregate_commits_by_time(self, sample_commits_data):
        """Test time-based aggregation."""
        from aggregate_commits import aggregate_by_time

        result = aggregate_by_time(sample_commits_data, period='day')

        assert '2026-01-14' in result
        assert result['2026-01-14']['commits'] == 2

    def test_aggregate_commits_by_author(self, sample_commits_data):
        """Test author-based aggregation."""
        from aggregate_commits import aggregate_by_author

        result = aggregate_by_author(sample_commits_data)

        assert 'John Doe' in result
        assert 'Jane Smith' in result
        assert result['John Doe']['commits'] == 1
        assert result['Jane Smith']['commits'] == 1

    def test_merge_sources(self, tmp_path):
        """Test merge_sources.py script."""
        from merge_sources import merge_combine, merge_average

        # Create sample sources
        source1 = {'name': 'source1', 'value': 100}
        source2 = {'name': 'source2', 'value': 200}
        sources = [source1, source2]

        # Test combine strategy
        result = merge_combine(sources)
        assert result['total_sources'] == 2
        assert len(result['sources']) == 2

        # Test average strategy
        result = merge_average(sources)
        assert result['value'] == 150.0

    def test_sales_aggregation_by_app(self, sample_sales_data):
        """Test sales aggregation by app."""
        from aggregate_sales import aggregate_by_app

        result = aggregate_by_app(sample_sales_data)

        assert 'APP001' in result
        assert result['APP001']['name'] == 'Test App'
        assert result['APP001']['downloads'] == 15  # 10 + 5
        assert result['APP001']['revenue'] == pytest.approx(8.98)  # 5.99 + 2.99

    def test_sales_aggregation_by_time(self, sample_sales_data):
        """Test sales aggregation by time."""
        from aggregate_sales import aggregate_by_time

        result = aggregate_by_time(sample_sales_data, period='day')

        assert '2026-01-14' in result
        assert result['2026-01-14']['downloads'] == 15
