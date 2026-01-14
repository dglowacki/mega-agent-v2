"""
Pytest configuration and shared fixtures.
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'integrations'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_appstore_response():
    """Mock App Store Connect API response."""
    return {
        "data": [
            {
                "id": "app-123",
                "type": "apps",
                "attributes": {
                    "name": "Test App",
                    "bundleId": "com.example.testapp",
                    "sku": "TESTAPP001"
                }
            }
        ]
    }


@pytest.fixture
def mock_wordpress_post():
    """Mock WordPress post data."""
    return {
        "id": 123,
        "title": {"rendered": "Test Post"},
        "content": {"rendered": "<p>Test content</p>"},
        "status": "publish",
        "date": "2026-01-14T10:00:00"
    }


@pytest.fixture
def mock_github_commit():
    """Mock GitHub commit data."""
    return {
        "sha": "abc123",
        "commit": {
            "author": {
                "name": "John Doe",
                "email": "john@example.com",
                "date": "2026-01-14T10:00:00Z"
            },
            "message": "Add feature X"
        },
        "stats": {
            "additions": 125,
            "deletions": 45,
            "total": 170
        }
    }


@pytest.fixture
def mock_calendar_event():
    """Mock Google Calendar event."""
    return {
        "id": "event-123",
        "summary": "Test Meeting",
        "start": {
            "dateTime": "2026-01-20T14:00:00-08:00",
            "timeZone": "America/Los_Angeles"
        },
        "end": {
            "dateTime": "2026-01-20T15:00:00-08:00",
            "timeZone": "America/Los_Angeles"
        },
        "attendees": [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"}
        ]
    }


@pytest.fixture
def sample_sales_data():
    """Sample App Store sales data for aggregation tests."""
    return [
        {
            "Begin Date": "01/14/2026",
            "SKU": "APP001",
            "Title": "Test App",
            "Units": "10",
            "Developer Proceeds": "5.99",
            "Country Code": "US",
            "Product Type Identifier": "IA1"
        },
        {
            "Begin Date": "01/14/2026",
            "SKU": "APP001",
            "Title": "Test App",
            "Units": "5",
            "Developer Proceeds": "2.99",
            "Country Code": "CA",
            "Product Type Identifier": "IA1"
        }
    ]


@pytest.fixture
def sample_commits_data():
    """Sample GitHub commits for aggregation tests."""
    return [
        {
            "sha": "abc123",
            "commit": {
                "author": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "date": "2026-01-14T10:00:00Z"
                },
                "message": "Add feature"
            },
            "stats": {"additions": 100, "deletions": 20}
        },
        {
            "sha": "def456",
            "commit": {
                "author": {
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "date": "2026-01-14T11:00:00Z"
                },
                "message": "Fix bug"
            },
            "stats": {"additions": 50, "deletions": 30}
        }
    ]


@pytest.fixture
def temp_test_file(tmp_path):
    """Create a temporary test file."""
    def _create_file(filename, content):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path
    return _create_file


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run tests against live APIs (requires credentials)"
    )


def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "live: mark test to run against live APIs"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    if not config.getoption("--live"):
        skip_live = pytest.mark.skip(reason="need --live option to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
