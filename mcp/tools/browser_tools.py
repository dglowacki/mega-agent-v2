"""
Browser Tools - Agent Browser automation integration.

Provides browser automation via agent-browser CLI:
- Navigation: open, back, forward, reload, close
- Snapshot: get page elements with refs
- Interactions: click, fill, type, press, scroll
- Information: get text, html, value, attributes
- Screenshots: capture page or elements
- Wait: wait for elements, text, URL patterns
- State: check visibility, enabled, checked
"""

import subprocess
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)


def _run_browser_cmd(args: list, timeout: int = 30) -> dict:
    """Run agent-browser command and return result."""
    try:
        cmd = ["agent-browser"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip() or f"Command failed with code {result.returncode}"
            }

        output = result.stdout.strip()

        # Try to parse as JSON if --json flag was used
        if "--json" in args:
            try:
                return {"success": True, "data": json.loads(output)}
            except json.JSONDecodeError:
                pass

        return {"success": True, "output": output}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": "agent-browser not found. Install with: npm install -g agent-browser"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Navigation Tools

def browser_open(url: str, headed: bool = False) -> str:
    """Navigate browser to URL."""
    args = ["open", url]
    if headed:
        args.append("--headed")
    result = _run_browser_cmd(args)
    if result["success"]:
        return f"Opened {url}"
    return f"Error: {result['error']}"


def browser_back() -> str:
    """Go back in browser history."""
    result = _run_browser_cmd(["back"])
    return "Navigated back" if result["success"] else f"Error: {result['error']}"


def browser_forward() -> str:
    """Go forward in browser history."""
    result = _run_browser_cmd(["forward"])
    return "Navigated forward" if result["success"] else f"Error: {result['error']}"


def browser_reload() -> str:
    """Reload current page."""
    result = _run_browser_cmd(["reload"])
    return "Page reloaded" if result["success"] else f"Error: {result['error']}"


def browser_close() -> str:
    """Close browser."""
    result = _run_browser_cmd(["close"])
    return "Browser closed" if result["success"] else f"Error: {result['error']}"


# Snapshot Tool

def browser_snapshot(interactive_only: bool = True, compact: bool = False, selector: str = None) -> str:
    """Get page elements. Returns refs like @e1, @e2 for interactions."""
    args = ["snapshot"]
    if interactive_only:
        args.append("-i")
    if compact:
        args.append("-c")
    if selector:
        args.extend(["-s", selector])

    result = _run_browser_cmd(args, timeout=60)
    if result["success"]:
        return result.get("output", "Snapshot complete")
    return f"Error: {result['error']}"


# Interaction Tools

def browser_click(ref: str) -> str:
    """Click element by ref (e.g., @e1)."""
    result = _run_browser_cmd(["click", ref])
    return f"Clicked {ref}" if result["success"] else f"Error: {result['error']}"


def browser_fill(ref: str, text: str) -> str:
    """Clear and type text into input element."""
    result = _run_browser_cmd(["fill", ref, text])
    return f"Filled {ref} with text" if result["success"] else f"Error: {result['error']}"


def browser_type(ref: str, text: str) -> str:
    """Type text into element without clearing."""
    result = _run_browser_cmd(["type", ref, text])
    return f"Typed into {ref}" if result["success"] else f"Error: {result['error']}"


def browser_press(key: str) -> str:
    """Press key or key combination (e.g., Enter, Control+a)."""
    result = _run_browser_cmd(["press", key])
    return f"Pressed {key}" if result["success"] else f"Error: {result['error']}"


def browser_hover(ref: str) -> str:
    """Hover over element."""
    result = _run_browser_cmd(["hover", ref])
    return f"Hovering over {ref}" if result["success"] else f"Error: {result['error']}"


def browser_check(ref: str) -> str:
    """Check a checkbox."""
    result = _run_browser_cmd(["check", ref])
    return f"Checked {ref}" if result["success"] else f"Error: {result['error']}"


def browser_uncheck(ref: str) -> str:
    """Uncheck a checkbox."""
    result = _run_browser_cmd(["uncheck", ref])
    return f"Unchecked {ref}" if result["success"] else f"Error: {result['error']}"


def browser_select(ref: str, value: str) -> str:
    """Select dropdown option by value."""
    result = _run_browser_cmd(["select", ref, value])
    return f"Selected {value} in {ref}" if result["success"] else f"Error: {result['error']}"


def browser_scroll(direction: str = "down", amount: int = 500) -> str:
    """Scroll page. Direction: up, down, left, right."""
    result = _run_browser_cmd(["scroll", direction, str(amount)])
    return f"Scrolled {direction} {amount}px" if result["success"] else f"Error: {result['error']}"


def browser_scroll_into_view(ref: str) -> str:
    """Scroll element into view."""
    result = _run_browser_cmd(["scrollintoview", ref])
    return f"Scrolled {ref} into view" if result["success"] else f"Error: {result['error']}"


# Information Tools

def browser_get_text(ref: str) -> str:
    """Get text content of element."""
    result = _run_browser_cmd(["get", "text", ref])
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


def browser_get_html(ref: str) -> str:
    """Get innerHTML of element."""
    result = _run_browser_cmd(["get", "html", ref])
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


def browser_get_value(ref: str) -> str:
    """Get value of input element."""
    result = _run_browser_cmd(["get", "value", ref])
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


def browser_get_attribute(ref: str, attr: str) -> str:
    """Get attribute value from element."""
    result = _run_browser_cmd(["get", "attr", ref, attr])
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


def browser_get_title() -> str:
    """Get page title."""
    result = _run_browser_cmd(["get", "title"])
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


def browser_get_url() -> str:
    """Get current URL."""
    result = _run_browser_cmd(["get", "url"])
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


# Screenshot Tools

def browser_screenshot(path: str = None, full_page: bool = False) -> str:
    """Take screenshot. Returns base64 if no path specified."""
    args = ["screenshot"]
    if path:
        args.append(path)
    if full_page:
        args.append("--full")

    result = _run_browser_cmd(args, timeout=60)
    if result["success"]:
        if path:
            return f"Screenshot saved to {path}"
        return result.get("output", "Screenshot captured")
    return f"Error: {result['error']}"


def browser_pdf(path: str) -> str:
    """Save page as PDF."""
    result = _run_browser_cmd(["pdf", path], timeout=60)
    return f"PDF saved to {path}" if result["success"] else f"Error: {result['error']}"


# Wait Tools

def browser_wait(target: str = None, timeout_ms: int = None, wait_type: str = None) -> str:
    """
    Wait for various conditions.

    Examples:
    - wait("@e1") - wait for element
    - wait("2000") - wait milliseconds
    - wait("Success", wait_type="text") - wait for text
    - wait("**/dashboard", wait_type="url") - wait for URL pattern
    - wait("networkidle", wait_type="load") - wait for network idle
    """
    args = ["wait"]

    if wait_type == "text":
        args.extend(["--text", target])
    elif wait_type == "url":
        args.extend(["--url", target])
    elif wait_type == "load":
        args.extend(["--load", target])
    elif target:
        args.append(target)

    result = _run_browser_cmd(args, timeout=timeout_ms // 1000 + 10 if timeout_ms else 60)
    return "Wait complete" if result["success"] else f"Error: {result['error']}"


# State Check Tools

def browser_is_visible(ref: str) -> str:
    """Check if element is visible."""
    result = _run_browser_cmd(["is", "visible", ref])
    if result["success"]:
        return result.get("output", "").lower()
    return f"Error: {result['error']}"


def browser_is_enabled(ref: str) -> str:
    """Check if element is enabled."""
    result = _run_browser_cmd(["is", "enabled", ref])
    if result["success"]:
        return result.get("output", "").lower()
    return f"Error: {result['error']}"


def browser_is_checked(ref: str) -> str:
    """Check if checkbox/radio is checked."""
    result = _run_browser_cmd(["is", "checked", ref])
    if result["success"]:
        return result.get("output", "").lower()
    return f"Error: {result['error']}"


# JavaScript Execution

def browser_eval(script: str) -> str:
    """Execute JavaScript in page context."""
    result = _run_browser_cmd(["eval", script], timeout=30)
    if result["success"]:
        return result.get("output", "")
    return f"Error: {result['error']}"


# Cookie/Storage Tools

def browser_cookies_get() -> str:
    """Get all cookies."""
    result = _run_browser_cmd(["cookies", "--json"])
    if result["success"]:
        data = result.get("data") or result.get("output", "")
        if isinstance(data, list):
            return json.dumps(data, indent=2)
        return str(data)
    return f"Error: {result['error']}"


def browser_cookies_set(name: str, value: str) -> str:
    """Set a cookie."""
    result = _run_browser_cmd(["cookies", "set", name, value])
    return f"Cookie {name} set" if result["success"] else f"Error: {result['error']}"


def browser_cookies_clear() -> str:
    """Clear all cookies."""
    result = _run_browser_cmd(["cookies", "clear"])
    return "Cookies cleared" if result["success"] else f"Error: {result['error']}"


# Settings Tools

def browser_set_viewport(width: int, height: int) -> str:
    """Set viewport size."""
    result = _run_browser_cmd(["set", "viewport", str(width), str(height)])
    return f"Viewport set to {width}x{height}" if result["success"] else f"Error: {result['error']}"


def browser_set_device(device: str) -> str:
    """Emulate device (e.g., 'iPhone 14')."""
    result = _run_browser_cmd(["set", "device", device])
    return f"Emulating {device}" if result["success"] else f"Error: {result['error']}"


# Tab Management

def browser_tab_list() -> str:
    """List open tabs."""
    result = _run_browser_cmd(["tab"])
    if result["success"]:
        return result.get("output", "No tabs")
    return f"Error: {result['error']}"


def browser_tab_new(url: str = None) -> str:
    """Open new tab."""
    args = ["tab", "new"]
    if url:
        args.append(url)
    result = _run_browser_cmd(args)
    return "New tab opened" if result["success"] else f"Error: {result['error']}"


def browser_tab_switch(index: int) -> str:
    """Switch to tab by index."""
    result = _run_browser_cmd(["tab", str(index)])
    return f"Switched to tab {index}" if result["success"] else f"Error: {result['error']}"


def browser_tab_close() -> str:
    """Close current tab."""
    result = _run_browser_cmd(["tab", "close"])
    return "Tab closed" if result["success"] else f"Error: {result['error']}"


def register_browser_tools(server) -> int:
    """Register all browser tools with MCP server."""
    tools = [
        # Navigation
        ("browser_open", "Navigate browser to URL", {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to"},
                "headed": {"type": "boolean", "description": "Show browser window", "default": False}
            },
            "required": ["url"]
        }, browser_open, False),

        ("browser_back", "Go back in browser history", {
            "type": "object", "properties": {}
        }, browser_back, False),

        ("browser_forward", "Go forward in browser history", {
            "type": "object", "properties": {}
        }, browser_forward, False),

        ("browser_reload", "Reload current page", {
            "type": "object", "properties": {}
        }, browser_reload, False),

        ("browser_close", "Close browser", {
            "type": "object", "properties": {}
        }, browser_close, False),

        # Snapshot
        ("browser_snapshot", "Get page elements with refs (@e1, @e2) for interactions", {
            "type": "object",
            "properties": {
                "interactive_only": {"type": "boolean", "description": "Only interactive elements", "default": True},
                "compact": {"type": "boolean", "description": "Compact output", "default": False},
                "selector": {"type": "string", "description": "CSS selector to scope snapshot"}
            }
        }, browser_snapshot, False),

        # Interactions
        ("browser_click", "Click element by ref", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref (e.g., @e1)"}},
            "required": ["ref"]
        }, browser_click, False),

        ("browser_fill", "Clear and type text into input", {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Element ref"},
                "text": {"type": "string", "description": "Text to enter"}
            },
            "required": ["ref", "text"]
        }, browser_fill, False),

        ("browser_type", "Type text without clearing", {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Element ref"},
                "text": {"type": "string", "description": "Text to type"}
            },
            "required": ["ref", "text"]
        }, browser_type, False),

        ("browser_press", "Press key or combination", {
            "type": "object",
            "properties": {"key": {"type": "string", "description": "Key name (Enter, Control+a, etc.)"}},
            "required": ["key"]
        }, browser_press, False),

        ("browser_hover", "Hover over element", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_hover, False),

        ("browser_check", "Check checkbox", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_check, False),

        ("browser_uncheck", "Uncheck checkbox", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_uncheck, False),

        ("browser_select", "Select dropdown option", {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Element ref"},
                "value": {"type": "string", "description": "Option value"}
            },
            "required": ["ref", "value"]
        }, browser_select, False),

        ("browser_scroll", "Scroll page", {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"], "default": "down"},
                "amount": {"type": "integer", "description": "Pixels to scroll", "default": 500}
            }
        }, browser_scroll, False),

        ("browser_scroll_into_view", "Scroll element into view", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_scroll_into_view, False),

        # Information
        ("browser_get_text", "Get element text content", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_get_text, False),

        ("browser_get_html", "Get element innerHTML", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_get_html, False),

        ("browser_get_value", "Get input value", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_get_value, False),

        ("browser_get_attribute", "Get element attribute", {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Element ref"},
                "attr": {"type": "string", "description": "Attribute name"}
            },
            "required": ["ref", "attr"]
        }, browser_get_attribute, False),

        ("browser_get_title", "Get page title", {
            "type": "object", "properties": {}
        }, browser_get_title, False),

        ("browser_get_url", "Get current URL", {
            "type": "object", "properties": {}
        }, browser_get_url, False),

        # Screenshots
        ("browser_screenshot", "Take screenshot", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to save (optional)"},
                "full_page": {"type": "boolean", "description": "Capture full page", "default": False}
            }
        }, browser_screenshot, False),

        ("browser_pdf", "Save page as PDF", {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"]
        }, browser_pdf, False),

        # Wait
        ("browser_wait", "Wait for condition", {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Element ref, milliseconds, or pattern"},
                "wait_type": {"type": "string", "enum": ["element", "text", "url", "load"], "description": "Type of wait"},
                "timeout_ms": {"type": "integer", "description": "Timeout in milliseconds"}
            }
        }, browser_wait, False),

        # State
        ("browser_is_visible", "Check if element is visible", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_is_visible, False),

        ("browser_is_enabled", "Check if element is enabled", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_is_enabled, False),

        ("browser_is_checked", "Check if checkbox is checked", {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "Element ref"}},
            "required": ["ref"]
        }, browser_is_checked, False),

        # JavaScript
        ("browser_eval", "Execute JavaScript in page", {
            "type": "object",
            "properties": {"script": {"type": "string", "description": "JavaScript code"}},
            "required": ["script"]
        }, browser_eval, False),

        # Cookies
        ("browser_cookies_get", "Get all cookies", {
            "type": "object", "properties": {}
        }, browser_cookies_get, False),

        ("browser_cookies_set", "Set a cookie", {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Cookie name"},
                "value": {"type": "string", "description": "Cookie value"}
            },
            "required": ["name", "value"]
        }, browser_cookies_set, False),

        ("browser_cookies_clear", "Clear all cookies", {
            "type": "object", "properties": {}
        }, browser_cookies_clear, False),

        # Settings
        ("browser_set_viewport", "Set viewport size", {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "description": "Width in pixels"},
                "height": {"type": "integer", "description": "Height in pixels"}
            },
            "required": ["width", "height"]
        }, browser_set_viewport, False),

        ("browser_set_device", "Emulate device", {
            "type": "object",
            "properties": {"device": {"type": "string", "description": "Device name (e.g., 'iPhone 14')"}},
            "required": ["device"]
        }, browser_set_device, False),

        # Tabs
        ("browser_tab_list", "List open tabs", {
            "type": "object", "properties": {}
        }, browser_tab_list, False),

        ("browser_tab_new", "Open new tab", {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL to open (optional)"}}
        }, browser_tab_new, False),

        ("browser_tab_switch", "Switch to tab", {
            "type": "object",
            "properties": {"index": {"type": "integer", "description": "Tab index"}},
            "required": ["index"]
        }, browser_tab_switch, False),

        ("browser_tab_close", "Close current tab", {
            "type": "object", "properties": {}
        }, browser_tab_close, False),
    ]

    count = 0
    for name, desc, schema, handler, requires_approval in tools:
        server.register_tool(
            name=name,
            description=desc,
            input_schema=schema,
            handler=handler,
            requires_approval=requires_approval,
            category="browser"
        )
        count += 1

    logger.info(f"Registered {count} browser tools")
    return count
