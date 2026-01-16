"""
MCP Protocol Handler - SSE transport implementation.

Implements Model Context Protocol 2024-11-05 specification:
- JSON-RPC 2.0 message format
- SSE (Server-Sent Events) transport
- Tool registration and execution
- Prompt registration
- Resource management
"""

import json
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """MCP protocol error."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class ErrorCode(Enum):
    """JSON-RPC 2.0 error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@dataclass
class MCPMessage:
    """MCP JSON-RPC message."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        d = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            d["id"] = self.id
        if self.method:
            d["method"] = self.method
        if self.params is not None:
            d["params"] = self.params
        if self.result is not None:
            d["result"] = self.result
        if self.error is not None:
            d["error"] = self.error
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "MCPMessage":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )

    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    requires_approval: bool = False
    category: str = "general"


@dataclass
class PromptDefinition:
    """Definition of an MCP prompt."""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    content: str = ""


@dataclass
class ResourceDefinition:
    """Definition of an MCP resource."""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


class MCPServer:
    """
    MCP Server with SSE transport.

    Handles:
    - Tool registration and execution
    - Prompt management
    - Resource serving
    - SSE message streaming
    """

    PROTOCOL_VERSION = "2024-11-05"
    SERVER_NAME = "mega-agent-v2"
    SERVER_VERSION = "2.0.0"

    def __init__(self, security_manager=None):
        """
        Initialize MCP Server.

        Args:
            security_manager: SecurityManager instance for approval handling
        """
        self.security_manager = security_manager

        self._tools: Dict[str, ToolDefinition] = {}
        self._prompts: Dict[str, PromptDefinition] = {}
        self._resources: Dict[str, ResourceDefinition] = {}

        self._message_handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "ping": self._handle_ping,
        }

        self._initialized = False
        self._client_info: Dict[str, Any] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
        requires_approval: bool = False,
        category: str = "general"
    ):
        """Register a tool with the server."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            requires_approval=requires_approval,
            category=category
        )
        logger.debug(f"Registered tool: {name}")

    def register_prompt(
        self,
        name: str,
        description: str,
        arguments: List[Dict[str, Any]] = None,
        content: str = ""
    ):
        """Register a prompt with the server."""
        self._prompts[name] = PromptDefinition(
            name=name,
            description=description,
            arguments=arguments or [],
            content=content
        )
        logger.debug(f"Registered prompt: {name}")

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str = "text/plain"
    ):
        """Register a resource with the server."""
        self._resources[uri] = ResourceDefinition(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type
        )
        logger.debug(f"Registered resource: {uri}")

    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """
        Handle an incoming MCP message.

        Args:
            message: Incoming MCPMessage

        Returns:
            Response MCPMessage
        """
        if not message.method:
            return self._error_response(
                message.id,
                ErrorCode.INVALID_REQUEST.value,
                "Missing method"
            )

        handler = self._message_handlers.get(message.method)
        if not handler:
            return self._error_response(
                message.id,
                ErrorCode.METHOD_NOT_FOUND.value,
                f"Unknown method: {message.method}"
            )

        try:
            result = await handler(message.params or {})
            return MCPMessage(id=message.id, result=result)
        except MCPError as e:
            return self._error_response(message.id, e.code, e.message, e.data)
        except Exception as e:
            logger.exception(f"Error handling {message.method}")
            return self._error_response(
                message.id,
                ErrorCode.INTERNAL_ERROR.value,
                str(e)
            )

    def _error_response(
        self,
        msg_id: Optional[Union[str, int]],
        code: int,
        message: str,
        data: Any = None
    ) -> MCPMessage:
        """Create an error response message."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return MCPMessage(id=msg_id, error=error)

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        self._client_info = params.get("clientInfo", {})

        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": True},
                "prompts": {"listChanged": True},
                "resources": {"subscribe": False, "listChanged": True},
            },
            "serverInfo": {
                "name": self.SERVER_NAME,
                "version": self.SERVER_VERSION
            }
        }

    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification."""
        self._initialized = True
        logger.info("MCP connection initialized")
        return None

    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise MCPError(
                ErrorCode.INVALID_PARAMS.value,
                "Missing tool name"
            )

        tool = self._tools.get(tool_name)
        if not tool:
            raise MCPError(
                ErrorCode.METHOD_NOT_FOUND.value,
                f"Unknown tool: {tool_name}"
            )

        # Check approval if required
        if tool.requires_approval and self.security_manager:
            approved = await self.security_manager.request_approval(
                tool_name=tool_name,
                arguments=arguments
            )
            if not approved:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Tool '{tool_name}' execution was not approved by user."
                    }],
                    "isError": True
                }

        # Execute tool
        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            # Normalize result to content array
            if isinstance(result, str):
                content = [{"type": "text", "text": result}]
            elif isinstance(result, dict):
                if "content" in result:
                    content = result["content"]
                else:
                    content = [{"type": "text", "text": json.dumps(result)}]
            elif isinstance(result, list):
                content = result
            else:
                content = [{"type": "text", "text": str(result)}]

            return {"content": content, "isError": False}

        except Exception as e:
            logger.exception(f"Tool execution error: {tool_name}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }

    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        prompts = []
        for prompt in self._prompts.values():
            prompts.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments
            })
        return {"prompts": prompts}

    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if not prompt_name:
            raise MCPError(
                ErrorCode.INVALID_PARAMS.value,
                "Missing prompt name"
            )

        prompt = self._prompts.get(prompt_name)
        if not prompt:
            raise MCPError(
                ErrorCode.METHOD_NOT_FOUND.value,
                f"Unknown prompt: {prompt_name}"
            )

        # Substitute arguments into content
        content = prompt.content
        for arg_name, arg_value in arguments.items():
            content = content.replace(f"{{{arg_name}}}", str(arg_value))

        return {
            "description": prompt.description,
            "messages": [{
                "role": "user",
                "content": {"type": "text", "text": content}
            }]
        }

    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources = []
        for resource in self._resources.values():
            resources.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type
            })
        return {"resources": resources}

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")

        if not uri:
            raise MCPError(
                ErrorCode.INVALID_PARAMS.value,
                "Missing resource URI"
            )

        resource = self._resources.get(uri)
        if not resource:
            raise MCPError(
                ErrorCode.METHOD_NOT_FOUND.value,
                f"Unknown resource: {uri}"
            )

        # For now, return empty content - override for actual resources
        return {
            "contents": [{
                "uri": uri,
                "mimeType": resource.mime_type,
                "text": ""
            }]
        }

    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "tools_count": len(self._tools),
            "prompts_count": len(self._prompts),
            "resources_count": len(self._resources),
            "initialized": self._initialized,
            "client_info": self._client_info
        }
