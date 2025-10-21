import asyncio
import json
import logging
import os
import shutil
import sys
from typing import Dict, List, Optional, Any
from enum import Enum

import requests
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LLM Provider imports with availability checking
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    logging.warning("Google Generative AI not available. Install with: pip install google-generativeai")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("Groq client not available. Install with: pip install groq")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LLMProvider(Enum):
    """Enumeration of available LLM providers."""
    GEMINI = "gemini"
    GROQ = "groq"


class Configuration:
    """Manages configuration and environment variables for the MCP client."""

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    @staticmethod
    def load_config(file_path: str) -> Dict[str, Any]:
        """Load server configuration from JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)

    @property
    def available_providers(self) -> List[LLMProvider]:
        """Get list of available LLM providers based on API keys and libraries."""
        providers = []
        
        if GEMINI_AVAILABLE and self.gemini_api_key:
            providers.append(LLMProvider.GEMINI)
        
        if GROQ_AVAILABLE and self.groq_api_key:
            providers.append(LLMProvider.GROQ)
        
        return providers


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: Dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM."""
        args_desc = []
        if 'properties' in self.input_schema:
            for param_name, param_info in self.input_schema['properties'].items():
                arg_desc = f"- {param_name}: {param_info.get('description', 'No description')}"
                if param_name in self.input_schema.get('required', []):
                    arg_desc += " (required)"
                # Enhanced: Note for path in screenshot tools
                if param_name == 'path' and self.name in ['browser_screenshot', 'browser_take_screenshot', 'puppeteer_screenshot', 'puppeteer_take_screenshot']:
                    arg_desc += " (use 'images/filename.png' to save in images folder)"
                args_desc.append(arg_desc)
        
        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""


class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        self.name: str = name
        self.config: Dict[str, Any] = config
        self.stdio_context: Optional[Any] = None
        self.session: Optional[ClientSession] = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.capabilities: Optional[Dict[str, Any]] = None

    async def initialize(self) -> None:
        """Initialize the server connection."""
        logging.info(f"[{self.name}] Initializing server with command: {self.config['command']}")
        logging.info(f"[{self.name}] Server args: {self.config['args']}")
        logging.info(f"[{self.name}] Server env: {self.config.get('env', {})}")
        
        command = shutil.which("npx") if self.config['command'] == "npx" else self.config['command']
        if not command:
            raise ValueError(f"Command not found: {self.config['command']}")
        
        server_params = StdioServerParameters(
            command=command,
            args=self.config['args'],
            env={**os.environ, **self.config['env']} if self.config.get('env') else None
        )
        try:
            logging.info(f"[{self.name}] Creating stdio client...")
            self.stdio_context = stdio_client(server_params)
            read, write = await self.stdio_context.__aenter__()
            logging.info(f"[{self.name}] Creating client session...")
            self.session = ClientSession(read, write)
            await self.session.__aenter__()
            logging.info(f"[{self.name}] Initializing session...")
            init_result = await self.session.initialize()
            self.capabilities = dict(init_result.capabilities) if hasattr(init_result, 'capabilities') else {}
            logging.info(f"[{self.name}] Server initialized successfully with capabilities: {self.capabilities}")
        except Exception as e:
            logging.error(f"[{self.name}] Error initializing server: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> List[Tool]:
        """List available tools from the server."""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        
        tools_response = await self.session.list_tools()
        tools = []
        
        for item in tools_response:
            if isinstance(item, tuple) and item[0] == 'tools':
                for tool in item[1]:
                    tools.append(Tool(tool.name, tool.description, tool.inputSchema))
        
        return tools

    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        retries: int = 2, 
        delay: float = 1.0
    ) -> Any:
        """Execute a tool with retry mechanism."""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        
        for attempt in range(retries + 1):
            try:
                logging.info(f"[{self.name}] Executing tool '{tool_name}' (attempt {attempt + 1})")
                result = await self.session.call_tool(tool_name, arguments)
                logging.info(f"[{self.name}] Tool '{tool_name}' executed successfully")
                return result
            except Exception as e:
                if attempt < retries:
                    logging.warning(f"[{self.name}] Tool execution failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"[{self.name}] Tool '{tool_name}' failed after {retries + 1} attempts: {e}")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            if self.session:
                try:
                    await self.session.__aexit__(None, None, None)
                except Exception as e:
                    logging.warning(f"[{self.name}] Error during session cleanup: {e}")
                finally:
                    self.session = None
            
            if self.stdio_context:
                try:
                    await self.stdio_context.__aexit__(None, None, None)
                except Exception as e:
                    logging.warning(f"[{self.name}] Error during stdio cleanup: {e}")
                finally:
                    self.stdio_context = None


class MultiLLMClient:
    """Manages communication with multiple LLM providers with fallback mechanism."""

    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.current_provider: Optional[LLMProvider] = None
        self.available_providers = config.available_providers
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE and self.config.gemini_api_key and genai:
            try:
                genai.configure(api_key=self.config.gemini_api_key)
            except Exception as e:
                logging.warning(f"Failed to configure Gemini: {e}")
        
        # Initialize Groq if available
        if GROQ_AVAILABLE and self.config.groq_api_key:
            self.groq_client = Groq(api_key=self.config.groq_api_key)

        # Auto-select a sensible default to avoid requiring /switch
        try:
            if LLMProvider.GROQ in self.available_providers:
                self.current_provider = LLMProvider.GROQ
            elif LLMProvider.GEMINI in self.available_providers:
                self.current_provider = LLMProvider.GEMINI
        except Exception:
            pass

    def get_response(self, messages: List[Dict[str, str]], provider: Optional[LLMProvider] = None) -> str:
        """Get a response from the selected LLM provider."""
        # Use the specified provider or current provider; if none, auto-select first available
        target_provider = provider or self.current_provider
        if not target_provider:
            if self.available_providers:
                self.current_provider = self.available_providers[0]
                target_provider = self.current_provider
                logging.info(f"🎯 Auto-selected LLM provider: {target_provider.value}")
            else:
                return (
                    "❌ No LLM providers available. Configure GROQ_API_KEY or GEMINI_API_KEY in environment/.env."
                )
        
        try:
            response = self._get_response_from_provider(messages, target_provider)
            if response:
                logging.info(f"✓ Response from {target_provider.value}")
                return response
        except Exception as e:
            error_msg = f"Provider {target_provider.value} error: {str(e)}"
            logging.error(error_msg)
            return f"Error: {error_msg}"

    def _get_response_from_provider(self, messages: List[Dict[str, str]], provider: LLMProvider) -> str:
        """Get response from a specific provider."""
        if provider == LLMProvider.GEMINI:
            return self._get_gemini_response(messages)
        elif provider == LLMProvider.GROQ:
            return self._get_groq_response(messages)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_gemini_response(self, messages: List[Dict[str, str]]) -> str:
        """Get response from Gemini."""
        if not GEMINI_AVAILABLE or not self.config.gemini_api_key:
            raise RuntimeError("Gemini not available")
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convert messages to Gemini format
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n\n"
            elif msg["role"] == "user":
                prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n\n"
        
        response = model.generate_content(prompt)
        return response.text if response.text else "No response generated"

    def _get_groq_response(self, messages: List[Dict[str, str]]) -> str:
        """Get response from Groq."""
        if not GROQ_AVAILABLE or not self.config.groq_api_key:
            raise RuntimeError("Groq not available")
        
        response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
        return response.choices[0].message.content if response.choices else "No response generated"

    def switch_provider(self, provider_name: str) -> bool:
        """Switch to a specific LLM provider."""
        try:
            provider = LLMProvider(provider_name)
            if provider in self.available_providers:
                self.current_provider = provider
                logging.info(f"Switched to {provider_name}")
                return True
            else:
                logging.warning(f"Provider {provider_name} not available")
                return False
        except ValueError:
            logging.warning(f"Unknown provider: {provider_name}")
            return False


class MCPToolsService:
    """Main service for handling MCP tools integration in Synapse."""

    def __init__(self):
        self.config = Configuration()
        self.servers: List[Server] = []
        self.llm_client = MultiLLMClient(self.config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize MCP servers and LLM client."""
        if self._initialized:
            return
        
        try:
            # Load servers configuration
            config_path = "/app/servers_config.json"
            if not os.path.exists(config_path):
                logging.error(f"Servers config not found at {config_path}")
                return
            
            servers_config = self.config.load_config(config_path)
            
            # Initialize servers
            for server_name, server_config in servers_config.get("mcpServers", {}).items():
                try:
                    server = Server(server_name, server_config)
                    await server.initialize()
                    self.servers.append(server)
                    logging.info(f"✅ Server {server_name} initialized successfully")
                except Exception as e:
                    logging.error(f"❌ Failed to initialize server {server_name}: {e}")
            
            # Set default LLM provider (Groq first, then Gemini)
            if LLMProvider.GROQ in self.llm_client.available_providers:
                self.llm_client.current_provider = LLMProvider.GROQ
            elif LLMProvider.GEMINI in self.llm_client.available_providers:
                self.llm_client.current_provider = LLMProvider.GEMINI
            
            self._initialized = True
            logging.info("🎉 MCP Tools Service initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize MCP Tools Service: {e}")
            raise

    async def process_tools_query(self, query: str, user_id: str) -> str:
        """Process a tools query using MCP servers and LLM."""
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return "❌ MCP Tools Service not initialized. Please check server configuration."
        
        try:
            # Get all available tools
            all_tools = []
            for server in self.servers:
                try:
                    tools = await server.list_tools()
                    all_tools.extend(tools)
                except Exception as e:
                    logging.warning(f"Error listing tools from server {server.name}: {e}")
            
            if not all_tools:
                return "❌ No tools available. Please check MCP server configuration."
            
            # Format tools for LLM
            tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
            
            # Create system message with tools
            system_message = f"""You are a helpful assistant with access to various tools. 
You can execute tools by responding with JSON in this format:
{{
    "tool": "tool_name",
    "arguments": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

Available tools:
{tools_description}

Important:
- Always respond with valid JSON when you want to execute a tool
- If you need to execute multiple tools, provide multiple JSON objects
- For screenshot tools, use 'images/filename.png' as the path
- If no tool is needed, provide a conversational response
- Be helpful and execute tools when they would be useful for the user's request"""

            # Create messages for LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ]
            
            # Get LLM response
            llm_response = self.llm_client.get_response(messages)
            
            # Process the response for tool execution
            return await self._process_llm_response(llm_response)
            
        except Exception as e:
            logging.error(f"Error processing tools query: {e}")
            return f"❌ Error processing query: {str(e)}"

    async def _process_llm_response(self, llm_response: str) -> str:
        """Process LLM response and execute tools if needed."""
        import re

        # Split response into individual JSON objects
        tool_calls = []
        try:
            # Extract JSON objects from the response
            json_strings = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', llm_response.replace('\n', ''))
            for json_str in json_strings:
                try:
                    tool_call = json.loads(json_str)
                    if "tool" in tool_call and "arguments" in tool_call:
                        tool_calls.append(tool_call)
                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse JSON block: {json_str}, error: {e}")
                    continue
        except Exception as e:
            logging.error(f"Error parsing LLM response: {e}")
            return llm_response

        # If no tool calls found, try single JSON parsing
        if not tool_calls:
            try:
                tool_call = json.loads(llm_response)
                if "tool" in tool_call and "arguments" in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                return llm_response

        # Execute tool calls sequentially
        results = []
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call["tool"]
            arguments = tool_call["arguments"]
            logging.info(f"Executing tool {i+1}/{len(tool_calls)}: {tool_name}")
            logging.info(f"With arguments: {arguments}")
            
            tool_executed = False
            for server in self.servers:
                try:
                    tools = await server.list_tools()
                    if any(tool.name == tool_name for tool in tools):
                        try:
                            result = await server.execute_tool(tool_name, arguments)
                            results.append(f"Tool {tool_name} executed successfully: {result}")
                            tool_executed = True
                            break
                        except Exception as e:
                            error_msg = f"Error executing tool {tool_name}: {str(e)}"
                            logging.error(error_msg)
                            results.append(error_msg)
                            tool_executed = True
                            break
                except Exception as e:
                    logging.warning(f"Error listing tools from server {server.name}: {e}")
                    continue
            
            if not tool_executed:
                results.append(f"No server found with tool: {tool_name}")

        if results:
            # Combine results and send back to LLM for final response
            combined_result = "\n".join(results)
            logging.info(f"All tool executions completed. Results: {combined_result}")
            
            # Create a summary message for the LLM
            summary_messages = [
                {
                    "role": "system", 
                    "content": f"Tool execution results: {combined_result}\n\nPlease provide a conversational summary of what was accomplished. If the tools executed successfully, confirm the actions were completed. If there were errors, explain what went wrong."
                },
                {
                    "role": "user", 
                    "content": "Please summarize the tool execution results in a conversational manner."
                }
            ]
            
            try:
                final_response = self.llm_client.get_response(summary_messages)
                return final_response
            except Exception as e:
                logging.error(f"Error getting final response from LLM: {e}")
                return f"Tools executed. Results: {combined_result}"
        
        return llm_response

    async def cleanup(self) -> None:
        """Clean up all servers."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))
        
        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logging.warning(f"Warning during cleanup: {e}")


# Global instance
mcp_tools_service = MCPToolsService()
