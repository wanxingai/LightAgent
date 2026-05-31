## Tools

LightAgent provides a flexible tool system that lets agents call Python
functions, dynamically load tools from the filesystem, and integrate external
services through the Model Context Protocol (MCP). Tools are registered through
a central `ToolRegistry` and executed by an `AsyncToolDispatcher` that handles
synchronous, async, and streaming tools uniformly.

### Overview

Every tool in LightAgent exposes its metadata through a `tool_info` attribute
attached directly to the function. The `tool_info` dictionary describes the
tool's name, description, and parameter schema. The framework converts this
schema into the OpenAI-compatible format expected by the model, so you only
need to declare the metadata once.

The core classes involved are:

| Class | Role |
| --- | --- |
| `ToolRegistry` | Stores registered tools, their metadata, and exposes OpenAI-format schemas. |
| `ToolLoader` | Dynamically loads tool modules from a directory at runtime. |
| `AsyncToolDispatcher` | Dispatches tool calls from the model, validates arguments, executes the function, and serializes results. |
| `MCPClientManager` | Connects to MCP servers and registers their tools into the registry. |

### Quick Start

The simplest way to use a tool is to define a function, attach `tool_info`, and
pass it when creating the agent:

```python
from LightAgent import LightAgent

def get_weather(city_name: str) -> str:
    """
    Get the current weather for `city_name`
    """
    return f"Query result: {city_name} is sunny."

get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get current weather information for the specified city.",
    "tool_params": [
        {
            "name": "city_name",
            "description": "The name of the city to query",
            "type": "string",
            "required": True,
        },
    ],
}

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    tools=[get_weather],
)

response = agent.run("Please check the weather in Shanghai.")
print(response)
```

When the model decides it needs weather data, it calls the registered tool, and
the result is returned to the model for final response generation.

### Tool Metadata (tool_info)

Every tool function must carry a `tool_info` attribute. This is a dictionary
with the following structure:

```python
my_function.tool_info = {
    "tool_name": "my_tool",                          # Required: unique tool identifier
    "tool_title": "My Tool",                          # Optional: human-readable title
    "tool_description": "What this tool does.",       # Required: description for the model
    "tool_params": [                                  # Required: list of parameter definitions
        {
            "name": "param1",                         # Parameter name
            "description": "Description of param1",  # Description for the model
            "type": "string",                         # Type hint (string, integer, number, boolean, array, object)
            "required": True,                         # Whether the parameter is mandatory
        },
    ],
}
```

The `type` field in each parameter accepts the following values, which are
checked at dispatch time:

| Type value | Python type |
| --- | --- |
| `string` / `str` | `str` |
| `integer` / `int` | `int` (not `bool`) |
| `number` / `float` | `int` or `float` |
| `boolean` / `bool` | `bool` |
| `array` / `list` | `list` |
| `object` / `dict` | `dict` |

### ToolRegistry

The `ToolRegistry` class is the central store for all registered tools. It
manages three collections internally:

- `function_mappings` -- maps tool name to the callable Python function.
- `function_info` -- maps tool name to its `tool_info` dictionary.
- `openai_function_schemas` -- list of tool descriptions in OpenAI-compatible
  format, ready to pass to the model API.

```python
from LightAgent.tools import ToolRegistry

registry = ToolRegistry()

# Register a single tool
registry.register_tool(get_weather)

# Register multiple tools at once
registry.register_tools([get_weather, get_news])

# Get tool schemas in OpenAI format (returns a deep copy)
schemas = registry.get_tools()

# Get tools as a formatted JSON string
print(registry.get_tools_str())

# Filter tools by name after a reflection step
filtered = registry.filter_tools('{"tools": [{"name": "get_weather"}]}')
```

The agent exposes a convenience accessor:

```python
schemas = agent.get_tools()          # same as agent.tool_registry.get_tools()
tool_func = agent.get_tool("get_weather")  # retrieve a loaded tool function
```

#### Tool Filtering

When `filter_tools=True` (the default) and Tree-of-Thought is enabled, the
agent can reduce the set of tools visible to the model after an initial
planning step. The `filter_tools()` method accepts a JSON string listing the
tools the planner selected and returns only the matching schemas.

### Creating Custom Tools

#### Basic Custom Tool

Create a Python function with type hints and a `tool_info` attribute:

```python
def search_database(query: str, limit: int = 10) -> str:
    """Search the local database."""
    # ... implementation ...
    return f"Found {limit} results for '{query}'."

search_database.tool_info = {
    "tool_name": "search_database",
    "tool_title": "Database Search",
    "tool_description": "Search the local database for matching records.",
    "tool_params": [
        {
            "name": "query",
            "description": "The search query string",
            "type": "string",
            "required": True,
        },
        {
            "name": "limit",
            "description": "Maximum number of results to return",
            "type": "integer",
            "required": False,
        },
    ],
}
```

Pass it to the agent at initialization or at runtime:

```python
# At initialization
agent = LightAgent(model="gpt-4.1", api_key="...", base_url="...", tools=[search_database])

# Or at runtime
response = agent.run("Search for recent orders", tools=[search_database])
```

#### Tools with Return Value Handling

The `AsyncToolDispatcher` serializes all tool return values before passing them
back to the model:

- `None` returns `"Tool executed successfully (no output)"`.
- `dict` or `list` is serialized as JSON.
- Other types are returned as their string representation.

This ensures compatibility with the OpenAI API requirement that tool content be
a string.

#### AI-Generated Tools

LightAgent can generate tool code automatically from a natural language
description using `agent.create_tool()`:

```python
from LightAgent import LightAgent

agent = LightAgent(
    name="Tool Generator",
    instructions="You are a helpful agent.",
    role="Your task is to automatically generate tool code from text descriptions.",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

text = """
### Weather Query Tool

Function to get real-time weather for a city using the wttr.in API.
Parameters:
- city_name (str): The city to query.
Returns a JSON string with temperature, humidity, and weather description.
"""

agent.create_tool(text, tools_directory="tools")
```

The method sends the description to the model, receives generated Python code
with `tool_info`, saves it as a `.py` file in the `tools/` directory, and
automatically loads it into the registry. See `example/09.create_tools.py` for
a complete working example.

### Async Tools

Tools can be asynchronous. The `AsyncToolDispatcher` automatically detects
coroutine functions and awaits them:

```python
import httpx
import json

async def fetch_news(topic: str) -> str:
    """Fetch latest news articles for a topic."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.example.com/news?q={topic}")
        resp.raise_for_status()
        data = resp.json()
    return json.dumps(data[:3], ensure_ascii=False)

fetch_news.tool_info = {
    "tool_name": "fetch_news",
    "tool_description": "Fetch the latest news for a given topic.",
    "tool_params": [
        {
            "name": "topic",
            "description": "News topic to search for",
            "type": "string",
            "required": True,
        },
    ],
}
```

### Streaming Tools

Tools that return Python generators (synchronous) or async generators work with
the streaming execution path. When the model calls a streaming tool in
streaming mode, chunks are yielded as they are produced:

```python
from typing import Generator

def stream_results(query: str) -> Generator[str, None, None]:
    """Stream search results incrementally."""
    for i in range(5):
        yield f"Result {i + 1} for '{query}'\n"

stream_results.tool_info = {
    "tool_name": "stream_results",
    "tool_description": "Stream search results incrementally.",
    "tool_params": [
        {
            "name": "query",
            "description": "Search query",
            "type": "string",
            "required": True,
        },
    ],
}
```

For async generators, the dispatcher returns the generator object directly
without consuming it, allowing the caller to iterate at its own pace.

### Dynamic Tool Loading

The `ToolLoader` class loads tools from Python files on disk at runtime. Each
tool file must be placed in the configured `tools/` directory and contain a
function with the same name as the file, decorated with `tool_info`:

```python
# tools/get_weather.py
def get_weather(city_name: str) -> str:
    """Get the current weather for `city_name`"""
    return f"Weather in {city_name}: 22 C, sunny."

get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get current weather information for the specified city.",
    "tool_params": [
        {
            "name": "city_name",
            "description": "The name of the city to query",
            "type": "string",
            "required": True,
        },
    ],
}
```

Load it by name:

```python
from LightAgent.tools import ToolLoader

loader = ToolLoader(tools_directory="tools")
loader.load_tool("get_weather")
all_tools = loader.load_tools(["get_weather", "search_database"])
```

When passed as a string in the agent's `tools` list, the agent automatically
uses `ToolLoader` to resolve it:

```python
agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    tools=["get_weather"],         # loaded from tools/get_weather.py
)
```

Tool names are validated against a strict pattern (`[A-Za-z_][A-Za-z0-9_]*`)
and path traversal is prevented to ensure only files within the tools directory
are loaded.

### Built-in Tools

LightAgent automatically registers a set of built-in tools at startup:

| Tool Name | Description |
| --- | --- |
| `execute_python_code` | Execute a Python code snippet in a sandboxed subprocess. |
| `execute_python_file` | Execute a Python script file and return the output. |
| `execute_python_code_stream` | Execute Python code and stream the output line by line. |
| `upload_file_to_oss` | Upload a file to object storage (OSS). |

These are always available unless the agent's tool registry is explicitly
overridden.

### MCP Integration

LightAgent supports the Model Context Protocol (MCP) for connecting to external
tool servers. MCP servers can provide tools over stdio or SSE (Server-Sent
Events) transports.

#### Configuration

Configure MCP server settings and call `setup_mcp()` before running the agent:

```python
import asyncio
from LightAgent import LightAgent

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

mcp_config = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            "disabled": False,
        },
        "weather-api": {
            "url": "https://mcp.example.com/sse",
            "headers": {"Authorization": "Bearer token"},
            "disabled": False,
        },
    }
}

# Setup MCP tools (async)
async def setup():
    await agent.setup_mcp(mcp_setting=mcp_config)
    response = agent.run("What files are in /tmp?")
    print(response)

asyncio.run(setup())
```

#### How MCP Tool Registration Works

The `MCPClientManager` connects to each configured server, lists available
tools via the MCP `list_tools` request, and registers them into the agent's
`ToolRegistry`:

1. For each enabled server, a session is created (stdio or SSE).
2. Tools are fetched using `session.list_tools()`.
3. Each tool's name, description, and parameter schema are converted to the
   `tool_info` format and registered.
4. A wrapper function is registered that forwards the call back to the MCP
   server via `session.call_tool()`.
5. Sessions are cleaned up after registration.

At runtime, when the model calls an MCP-registered tool, the dispatcher routes
the call through the wrapper, which connects to the appropriate server,
executes the tool, and returns the result.

#### Runtime Tool MCP Loading

MCP tools can also be provided at individual run time through the `tools`
parameter by passing already-registered callables.

### Runtime Constraints

#### Parameter Validation

The `AsyncToolDispatcher` validates tool parameters before execution:

- **Required parameters**: If a required parameter is missing, the tool returns
  an `LA-TOOL` error code.
- **Type checking**: Parameter values are checked against the declared type.
  Mismatches return an `LA-TOOL` error with the expected and actual types.
- **Serialization**: All results are converted to strings, ensuring the model
  API receives valid tool content.

#### Argument Parsing Robustness

For streaming mode, the agent includes a multi-strategy argument parser
(`_parse_tool_arguments`) that handles common JSON formatting issues from model
output:

1. Direct `json.loads()` attempt.
2. JSON object extraction via regex for embedded JSON.
3. Manual key-value pair parsing as a fallback.

This ensures tool calls succeed even when the model produces slightly
malformed JSON.

#### Path Safety

`ToolLoader` enforces two safety checks:

- Tool names must match `[A-Za-z_][A-Za-z0-9_]*` (no path separators or
  special characters).
- Resolved file paths are verified to stay within the configured tools
  directory, preventing directory traversal.

#### Error Codes

Tool-related errors use the `LA-TOOL` error code:

| Scenario | Error |
| --- | --- |
| Tool not found in registry | `[LA-TOOL] Tool 'name' not found.` |
| Missing required parameter | `[LA-TOOL] Tool 'name' missing required parameter 'param'.` |
| Type mismatch | `[LA-TOOL] Tool 'name' parameter 'param' expected 'string', got 'int'.` |
| Execution exception | `[LA-TOOL] ...` with exception traceback |

Refer to the [Error Handling](error_handling.md) document for the full error
code reference.

### API Reference

#### ToolRegistry

```python
class ToolRegistry:
    def __init__(self) -> None
    def register_tool(self, func: Callable) -> bool
    def register_tools(self, tools: List[Callable]) -> bool
    def get_tools(self) -> List[Dict[str, Any]]
    def get_tools_str(self) -> str
    def filter_tools(self, tool_reflection_result: str) -> List[Dict]
```

| Method | Description |
| --- | --- |
| `register_tool(func)` | Register a single tool. Returns `False` if the function lacks `tool_info`. |
| `register_tools(tools)` | Register multiple tools. Returns `True` only if all succeed. |
| `get_tools()` | Return a deep copy of all OpenAI-format tool schemas. |
| `get_tools_str()` | Return a formatted JSON string of all tool schemas. |
| `filter_tools(json_str)` | Return only the schemas matching tool names in the JSON string. Raises `ValueError` on parse failure. |

#### ToolLoader

```python
class ToolLoader:
    def __init__(self, tools_directory: str = "tools") -> None
    def load_tool(self, tool_name: str) -> Callable
    def load_tools(self, tool_names: List[str]) -> Dict[str, Callable]
```

| Method | Description |
| --- | --- |
| `load_tool(tool_name)` | Load a single tool from a `.py` file. Caches loaded tools. Raises `FileNotFoundError` or `AttributeError`. |
| `load_tools(tool_names)` | Load multiple tools. Returns the dict of all loaded tools. |

#### AsyncToolDispatcher

```python
class AsyncToolDispatcher:
    def __init__(
        self,
        function_mappings: Dict[str, Callable] = None,
        function_info: Dict[str, Dict[str, Any]] = None,
    ) -> None
    async def dispatch(self, tool_name: str, tool_params: Dict[str, Any]) -> Union[str, Generator, AsyncGenerator]
    def _serialize_result(self, result: Any) -> str
    def _validate_tool_params(self, tool_name: str, tool_params: Dict[str, Any]) -> str | None
```

| Method | Description |
| --- | --- |
| `dispatch(tool_name, tool_params)` | Execute a tool by name with the given parameters. Handles sync, async, generator, and async-generator functions. |
| `_serialize_result(result)` | Convert a tool's return value to a string for the model API. |
| `_validate_tool_params(tool_name, tool_params)` | Check required parameters and type conformance. Returns an error string or `None`. |

#### LightAgent Tool Methods

```python
agent.load_tools(tool_names: List[Union[str, Callable]], tools_directory: str = "tools") -> None
agent.get_tools() -> List[Dict[str, Any]]
agent.get_tool(tool_name: str) -> Callable
agent.create_tool(user_input: str, tools_directory: str = "tools") -> None
async agent.setup_mcp(mcp_setting: dict) -> None
```

| Method | Description |
| --- | --- |
| `load_tools(tool_names, tools_directory)` | Load and register tools by name (string) or pass callables directly. |
| `get_tools()` | Return all registered tool schemas in OpenAI format. |
| `get_tool(tool_name)` | Return the loaded function for a named tool. Raises `ValueError` if not found. |
| `create_tool(user_input, tools_directory)` | Generate a tool from a natural language description using the model, save it, and load it. |
| `setup_mcp(mcp_setting)` | Initialize MCP connections and register remote tools (async). |
