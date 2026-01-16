"""
AWS Tools - Lambda, S3, DynamoDB, and cost operations.

Provides AWS service access for the voice assistant.
Uses AWS CLI with configured credentials.
"""

import subprocess
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Default AWS region
DEFAULT_REGION = "us-west-2"


def _run_aws(args: list, region: str = None) -> str:
    """
    Run an AWS CLI command.

    Args:
        args: AWS CLI arguments
        region: AWS region

    Returns:
        Command output or error
    """
    cmd = ["aws"] + args

    if region:
        cmd.extend(["--region", region])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        # Try to format JSON output
        output = result.stdout.strip()
        if output:
            try:
                parsed = json.loads(output)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                pass

        return output if output else "[No output]"

    except subprocess.TimeoutExpired:
        return "Error: AWS command timed out"
    except FileNotFoundError:
        return "Error: AWS CLI not installed"
    except Exception as e:
        return f"Error running AWS CLI: {str(e)}"


# Lambda functions

def aws_lambda_list(region: str = None) -> str:
    """
    List Lambda functions.

    Args:
        region: AWS region

    Returns:
        List of functions
    """
    return _run_aws(["lambda", "list-functions"], region or DEFAULT_REGION)


def aws_lambda_invoke(
    function_name: str,
    payload: str = "{}",
    region: str = None
) -> str:
    """
    Invoke a Lambda function.

    Args:
        function_name: Function name or ARN
        payload: JSON payload
        region: AWS region

    Returns:
        Function response
    """
    import tempfile
    import os

    # Create temp file for output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name

    try:
        result = _run_aws([
            "lambda", "invoke",
            "--function-name", function_name,
            "--payload", payload,
            "--cli-binary-format", "raw-in-base64-out",
            output_file
        ], region or DEFAULT_REGION)

        # Read response
        with open(output_file, 'r') as f:
            response = f.read()

        os.unlink(output_file)

        return f"Invocation result:\n{result}\n\nResponse:\n{response}"

    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        return f"Error: {str(e)}"


def aws_lambda_logs(
    function_name: str,
    limit: int = 20,
    region: str = None
) -> str:
    """
    Get recent Lambda logs.

    Args:
        function_name: Function name
        limit: Number of log events
        region: AWS region

    Returns:
        Log entries
    """
    log_group = f"/aws/lambda/{function_name}"
    return _run_aws([
        "logs", "filter-log-events",
        "--log-group-name", log_group,
        "--limit", str(limit)
    ], region or DEFAULT_REGION)


# S3 operations

def aws_s3_list(
    bucket: str = None,
    prefix: str = "",
    region: str = None
) -> str:
    """
    List S3 buckets or objects.

    Args:
        bucket: Bucket name (optional, lists buckets if not provided)
        prefix: Object prefix filter
        region: AWS region

    Returns:
        List of buckets or objects
    """
    if bucket:
        path = f"s3://{bucket}/{prefix}" if prefix else f"s3://{bucket}"
        return _run_aws(["s3", "ls", path], region)
    else:
        return _run_aws(["s3", "ls"], region)


def aws_s3_get(
    bucket: str,
    key: str,
    region: str = None
) -> str:
    """
    Get S3 object content.

    Args:
        bucket: Bucket name
        key: Object key
        region: AWS region

    Returns:
        Object content
    """
    return _run_aws([
        "s3", "cp",
        f"s3://{bucket}/{key}",
        "-"
    ], region or DEFAULT_REGION)


def aws_s3_put(
    bucket: str,
    key: str,
    content: str,
    region: str = None
) -> str:
    """
    Put content to S3.

    Args:
        bucket: Bucket name
        key: Object key
        content: Content to upload
        region: AWS region

    Returns:
        Upload result
    """
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        temp_file = f.name

    try:
        result = _run_aws([
            "s3", "cp",
            temp_file,
            f"s3://{bucket}/{key}"
        ], region or DEFAULT_REGION)

        os.unlink(temp_file)
        return result

    except Exception as e:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        return f"Error: {str(e)}"


# DynamoDB operations

def aws_dynamodb_list_tables(region: str = None) -> str:
    """
    List DynamoDB tables.

    Args:
        region: AWS region

    Returns:
        List of tables
    """
    return _run_aws(["dynamodb", "list-tables"], region or DEFAULT_REGION)


def aws_dynamodb_scan(
    table_name: str,
    limit: int = 20,
    region: str = None
) -> str:
    """
    Scan a DynamoDB table.

    Args:
        table_name: Table name
        limit: Maximum items
        region: AWS region

    Returns:
        Table items
    """
    return _run_aws([
        "dynamodb", "scan",
        "--table-name", table_name,
        "--limit", str(limit)
    ], region or DEFAULT_REGION)


def aws_dynamodb_query(
    table_name: str,
    key_condition: str,
    region: str = None
) -> str:
    """
    Query a DynamoDB table.

    Args:
        table_name: Table name
        key_condition: Key condition expression
        region: AWS region

    Returns:
        Query results
    """
    return _run_aws([
        "dynamodb", "query",
        "--table-name", table_name,
        "--key-condition-expression", key_condition
    ], region or DEFAULT_REGION)


# Cost operations

def aws_cost_get_usage(
    start_date: str,
    end_date: str,
    granularity: str = "DAILY"
) -> str:
    """
    Get AWS cost and usage.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        granularity: DAILY, MONTHLY, or HOURLY

    Returns:
        Cost breakdown
    """
    return _run_aws([
        "ce", "get-cost-and-usage",
        "--time-period", f"Start={start_date},End={end_date}",
        "--granularity", granularity,
        "--metrics", "BlendedCost"
    ])


def aws_cost_get_forecast(
    start_date: str,
    end_date: str,
    metric: str = "BLENDED_COST"
) -> str:
    """
    Get AWS cost forecast.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metric: Cost metric

    Returns:
        Cost forecast
    """
    return _run_aws([
        "ce", "get-cost-forecast",
        "--time-period", f"Start={start_date},End={end_date}",
        "--metric", metric,
        "--granularity", "MONTHLY"
    ])


def register_aws_tools(server) -> int:
    """Register all AWS tools with the MCP server."""

    # Lambda tools
    server.register_tool(
        name="aws_lambda_list",
        description="List AWS Lambda functions.",
        input_schema={
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "AWS region"}
            }
        },
        handler=aws_lambda_list,
        requires_approval=False,
        category="aws"
    )

    server.register_tool(
        name="aws_lambda_invoke",
        description="Invoke a Lambda function with a payload.",
        input_schema={
            "type": "object",
            "properties": {
                "function_name": {"type": "string", "description": "Function name or ARN"},
                "payload": {"type": "string", "description": "JSON payload", "default": "{}"},
                "region": {"type": "string", "description": "AWS region"}
            },
            "required": ["function_name"]
        },
        handler=aws_lambda_invoke,
        requires_approval=True,
        category="aws"
    )

    server.register_tool(
        name="aws_lambda_logs",
        description="Get recent logs from a Lambda function.",
        input_schema={
            "type": "object",
            "properties": {
                "function_name": {"type": "string", "description": "Function name"},
                "limit": {"type": "integer", "description": "Number of log events", "default": 20},
                "region": {"type": "string", "description": "AWS region"}
            },
            "required": ["function_name"]
        },
        handler=aws_lambda_logs,
        requires_approval=False,
        category="aws"
    )

    # S3 tools
    server.register_tool(
        name="aws_s3_list",
        description="List S3 buckets or objects in a bucket.",
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name (optional)"},
                "prefix": {"type": "string", "description": "Object prefix filter"},
                "region": {"type": "string", "description": "AWS region"}
            }
        },
        handler=aws_s3_list,
        requires_approval=False,
        category="aws"
    )

    server.register_tool(
        name="aws_s3_get",
        description="Get content of an S3 object.",
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name"},
                "key": {"type": "string", "description": "Object key"},
                "region": {"type": "string", "description": "AWS region"}
            },
            "required": ["bucket", "key"]
        },
        handler=aws_s3_get,
        requires_approval=False,
        category="aws"
    )

    server.register_tool(
        name="aws_s3_put",
        description="Upload content to S3.",
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name"},
                "key": {"type": "string", "description": "Object key"},
                "content": {"type": "string", "description": "Content to upload"},
                "region": {"type": "string", "description": "AWS region"}
            },
            "required": ["bucket", "key", "content"]
        },
        handler=aws_s3_put,
        requires_approval=True,
        category="aws"
    )

    # DynamoDB tools
    server.register_tool(
        name="aws_dynamodb_list_tables",
        description="List DynamoDB tables.",
        input_schema={
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "AWS region"}
            }
        },
        handler=aws_dynamodb_list_tables,
        requires_approval=False,
        category="aws"
    )

    server.register_tool(
        name="aws_dynamodb_scan",
        description="Scan a DynamoDB table.",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "limit": {"type": "integer", "description": "Max items", "default": 20},
                "region": {"type": "string", "description": "AWS region"}
            },
            "required": ["table_name"]
        },
        handler=aws_dynamodb_scan,
        requires_approval=False,
        category="aws"
    )

    server.register_tool(
        name="aws_dynamodb_query",
        description="Query a DynamoDB table with a key condition.",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "key_condition": {"type": "string", "description": "Key condition expression"},
                "region": {"type": "string", "description": "AWS region"}
            },
            "required": ["table_name", "key_condition"]
        },
        handler=aws_dynamodb_query,
        requires_approval=False,
        category="aws"
    )

    # Cost tools
    server.register_tool(
        name="aws_cost_get_usage",
        description="Get AWS cost and usage for a date range.",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "granularity": {"type": "string", "description": "DAILY, MONTHLY, or HOURLY", "default": "DAILY"}
            },
            "required": ["start_date", "end_date"]
        },
        handler=aws_cost_get_usage,
        requires_approval=False,
        category="aws"
    )

    server.register_tool(
        name="aws_cost_get_forecast",
        description="Get AWS cost forecast.",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "metric": {"type": "string", "description": "Cost metric", "default": "BLENDED_COST"}
            },
            "required": ["start_date", "end_date"]
        },
        handler=aws_cost_get_forecast,
        requires_approval=False,
        category="aws"
    )

    return 11  # Number of tools registered
