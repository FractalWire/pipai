"""MCP client module for pipai.

This module provides functionality to interact with MCP (Model Control Protocol) servers,
allowing pipai to execute tools provided by these servers.
"""

import asyncio
import json
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self, name: str, description: str, input_schema: Dict[str, Any]
    ) -> None:
        """Initialize a tool with its metadata.

        Args:
            name: The name of the tool
            description: A description of what the tool does
            input_schema: JSON schema describing the tool's input parameters
        """
        self.name: str = name
        self.description: str = description
        self.input_schema: Dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM consumption.

        Returns:
            A formatted string describing the tool
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{'\n'.join(args_desc)}
"""


class MCPServer:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """Initialize an MCP server connection.

        Args:
            name: A name for this server instance
            config: Configuration dictionary for the server
        """
        self.name: str = name
        self.config: Dict[str, Any] = config
        self.session: Optional[ClientSession] = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection.

        Raises:
            ValueError: If the command is invalid
            RuntimeError: If server initialization fails
        """
        command = (
            shutil.which("npx")
            if self.config["command"] == "npx"
            else self.config["command"]
        )
        if command is None:
            raise ValueError("The command must be a valid string and cannot be None.")

        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env={**os.environ, **self.config["env"]}
            if self.config.get("env")
            else None,
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> List[Tool]:
        """List available tools from the server.

        Returns:
            A list of available tools

        Raises:
            RuntimeError: If the server is not initialized
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools.append(Tool(tool.name, tool.description, tool.inputSchema))

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            retries: Number of retry attempts
            delay: Delay between retries in seconds

        Returns:
            Tool execution result

        Raises:
            RuntimeError: If server is not initialized
            Exception: If tool execution fails after all retries
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                logging.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)
                return result

            except Exception as e:
                attempt += 1
                logging.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}")


class MCPClient:
    """Client for managing multiple MCP servers and their tools."""

    def __init__(self) -> None:
        """Initialize the MCP client."""
        self.servers: List[MCPServer] = []
        self._initialized = False

    async def load_servers(self, config_path: str) -> None:
        """Load server configurations from a JSON file.

        Args:
            config_path: Path to the server configuration JSON file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the configuration file is invalid JSON
            RuntimeError: If server initialization fails
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading server configuration: {e}")
            raise

        # Clean up any existing servers
        await self.cleanup_servers()
        self.servers = []

        # Create new server instances
        for name, srv_config in config.get("mcpServers", {}).items():
            self.servers.append(MCPServer(name, srv_config))

        # Initialize all servers
        init_tasks = []
        for server in self.servers:
            init_tasks.append(asyncio.create_task(server.initialize()))

        if init_tasks:
            try:
                await asyncio.gather(*init_tasks)
                self._initialized = True
            except Exception as e:
                logging.error(f"Error initializing servers: {e}")
                await self.cleanup_servers()
                raise RuntimeError(f"Failed to initialize MCP servers: {e}")

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))

        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")
        
        self._initialized = False

    async def get_all_tools(self) -> List[Tool]:
        """Get all available tools from all servers.

        Returns:
            A list of all available tools

        Raises:
            RuntimeError: If servers are not initialized
        """
        if not self._initialized:
            raise RuntimeError("MCP servers not initialized")

        all_tools = []
        for server in self.servers:
            try:
                tools = await server.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                logging.error(f"Error getting tools from server {server.name}: {e}")

        return all_tools

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Execute a tool on the appropriate server.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            A tuple of (success, result)
            - success: True if tool execution succeeded, False otherwise
            - result: Tool execution result or error message

        Raises:
            RuntimeError: If servers are not initialized
        """
        if not self._initialized:
            raise RuntimeError("MCP servers not initialized")

        for server in self.servers:
            try:
                tools = await server.list_tools()
                if any(tool.name == tool_name for tool in tools):
                    result = await server.execute_tool(tool_name, arguments)
                    return True, result
            except Exception as e:
                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                logging.error(error_msg)
                return False, error_msg

        return False, f"No server found with tool: {tool_name}"

    def get_tools_description(self) -> str:
        """Get a formatted description of all available tools.

        Returns:
            A string containing descriptions of all tools

        Raises:
            RuntimeError: If servers are not initialized
        """
        if not self._initialized:
            raise RuntimeError("MCP servers not initialized")

        async def _get_descriptions():
            all_tools = await self.get_all_tools()
            return "\n".join([tool.format_for_llm() for tool in all_tools])

        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_get_descriptions())
        finally:
            loop.close()
