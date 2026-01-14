# Mega-Agent2 Test Suite

Comprehensive testing for integration clients, MCP servers, skills, and agents.

## Test Structure

```
tests/
├── integrations/       # Integration client tests
│   ├── test_appstore_client.py
│   ├── test_wordpress_client.py
│   ├── test_google_calendar_client.py
│   └── ...
├── mcp/               # MCP server tests
│   ├── test_appstore_server.py
│   ├── test_wordpress_server.py
│   └── ...
├── skills/            # Skills tests
│   ├── test_email_templates.py
│   ├── test_data_aggregation.py
│   └── ...
├── agents/            # End-to-end agent tests
│   ├── test_reporting_agent.py
│   ├── test_wordpress_agent.py
│   └── ...
└── README.md          # This file
```

## Running Tests

### All Tests
```bash
python -m pytest tests/
```

### Specific Test Category
```bash
python -m pytest tests/integrations/
python -m pytest tests/mcp/
python -m pytest tests/skills/
python -m pytest tests/agents/
```

### Specific Test File
```bash
python -m pytest tests/integrations/test_appstore_client.py
```

### With Coverage
```bash
python -m pytest tests/ --cov=integrations --cov=.claude/skills --cov-report=html
```

## Test Types

### 1. Integration Client Tests

Test that clients can connect to APIs and perform basic operations.

**Mock Mode** (default):
- Uses mocked responses
- No actual API calls
- Fast execution

**Live Mode** (with `--live` flag):
- Real API calls
- Requires valid credentials
- Slower execution

Example:
```bash
# Mock mode
python -m pytest tests/integrations/test_appstore_client.py

# Live mode
python -m pytest tests/integrations/test_appstore_client.py --live
```

### 2. MCP Server Tests

Test that MCP tools are properly defined and can be invoked.

```bash
python -m pytest tests/mcp/test_appstore_server.py
```

### 3. Skills Tests

Test that skill scripts work correctly with sample data.

```bash
python -m pytest tests/skills/test_data_aggregation.py
```

### 4. End-to-End Agent Tests

Test complete workflows using agents, clients, and skills together.

```bash
python -m pytest tests/agents/test_reporting_agent.py
```

## Test Configuration

### Environment Variables

Required for live testing:

**App Store:**
- `APPSTORE_KEY_ID`
- `APPSTORE_ISSUER_ID`
- `APPSTORE_PRIVATE_KEY_PATH`

**WordPress:**
- `WORDPRESS_SITES_CONFIG_PATH`

**Google (Calendar, Tasks):**
- `GOOGLE_SERVICE_ACCOUNT_PATH`
- `GOOGLE_ADMIN_EMAIL`

**ClickUp:**
- `CLICKUP_API_TOKEN`

**Linear:**
- `LINEAR_API_KEY`

**Supabase:**
- `SUPABASE_ACCESS_TOKEN`

**Firebase:**
- `FIREBASE_SERVICE_ACCOUNT_PATH`

**Google Ads:**
- `GOOGLE_ADS_CONFIG_PATH`

### Pytest Configuration

See `pytest.ini` for test configuration.

## Writing Tests

### Integration Client Test Template

```python
import pytest
from integrations.example_client import ExampleClient

class TestExampleClient:
    @pytest.fixture
    def client(self):
        return ExampleClient()

    def test_initialization(self, client):
        assert client is not None

    @pytest.mark.asyncio
    async def test_basic_operation(self, client):
        result = await client.get_data()
        assert result['status'] == 'success'

    @pytest.mark.asyncio
    @pytest.mark.live
    async def test_live_operation(self, client):
        # Only runs with --live flag
        result = await client.get_real_data()
        assert result is not None
```

### MCP Server Test Template

```python
import pytest
from integrations.mcp_servers.example_server import example_mcp_server

class TestExampleMCPServer:
    def test_server_creation(self):
        assert example_mcp_server is not None

    def test_tool_definitions(self):
        # Verify tools are defined
        assert len(example_mcp_server.tools) > 0

    @pytest.mark.asyncio
    async def test_tool_invocation(self):
        # Test tool can be invoked
        tool = example_mcp_server.tools[0]
        result = await tool.handler({'param': 'value'})
        assert result is not None
```

### Skill Test Template

```python
import pytest
from pathlib import Path

class TestExampleSkill:
    def test_script_exists(self):
        script = Path('.claude/skills/example/scripts/script.py')
        assert script.exists()

    def test_script_execution(self):
        # Test script with sample data
        result = run_script('script.py', 'sample_data.json')
        assert result['status'] == 'success'
```

## Best Practices

1. **Use fixtures** for common setup/teardown
2. **Mock external APIs** in unit tests
3. **Use pytest.mark.asyncio** for async tests
4. **Use pytest.mark.live** for tests requiring real APIs
5. **Test both success and error cases**
6. **Keep tests independent** (no shared state)
7. **Use descriptive test names**
8. **Add docstrings** to explain complex tests

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main
- Pull requests
- Scheduled daily runs

### Test Reports

- Coverage reports: `htmlcov/index.html`
- Test results: `test-results.xml`
- Performance metrics: `performance.json`

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Add project to PYTHONPATH
export PYTHONPATH=/home/ec2-user/mega-agent2:$PYTHONPATH
```

**Async test failures:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Mock data not found:**
```bash
# Ensure mock data files exist in tests/fixtures/
```

## Performance Testing

Run performance benchmarks:
```bash
python -m pytest tests/ --benchmark-only
```

## Security Testing

Run security checks:
```bash
bandit -r integrations/
safety check
```
