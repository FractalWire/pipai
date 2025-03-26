# pipai - Python LLM CLI Tool

A command-line tool that uses LiteLLM to interact with various LLM models. It takes the output of a previous command as context and a user-defined prompt to generate responses.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
  - [Default Model](#default-model)
  - [LiteLLM Configuration](#litellm-configuration)
  - [Pre-defined Prompts](#pre-defined-prompts)
  - [MCP Tools Configuration](#mcp-tools-configuration)
- [Usage](#usage)
  - [Basic Commands](#basic-commands)
  - [Working with Models](#working-with-models)
  - [Working with Prompts](#working-with-prompts)
  - [Managing Conversations](#managing-conversations)
  - [Using MCP Tools](#using-mcp-tools)
  - [Setting Configuration](#setting-configuration)
  - [Viewing Configuration](#viewing-configuration)
- [Examples](#examples)
- [Bash Auto-completion](#bash-auto-completion)
- [Requirements](#requirements)

## Installation

```bash
# Using uv
uv venv
uv pip install git+https://github.com/fractalwire/pipai.git
ln -s $(PWD)/.venv/bin/pipai /usr/local/bin/pipai
```

## Configuration

pipai uses the XDG configuration directory structure. Configuration files are stored in:

```
$XDG_CONFIG_HOME/pipai/
```

If `XDG_CONFIG_HOME` is not set, it defaults to `~/.config/pipai/`.

### Default Model

You can set a default LLM model in the config file:

```
# In $XDG_CONFIG_HOME/pipai/config
DEFAULT_LLM=gpt-3.5-turbo
```

### LiteLLM Configuration

pipai uses the LiteLLM SDK to connect to various LLM providers. To configure your API keys:

Set environment variables for your LLM providers:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-...

# Azure OpenAI
export AZURE_API_KEY=...
export AZURE_API_BASE=...
export AZURE_API_VERSION=...
```

For detailed configuration options, refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/completion/supported_models).

### Pre-defined Prompts

You can create pre-defined prompts in the `prompts` directory:

```
$XDG_CONFIG_HOME/pipai/prompts/
```

Each file in this directory becomes a command-line option. Prompts are defined in TOML format with two sections:
- `summary`: A brief description shown in the help menu
- `prompt`: The actual prompt text sent to the LLM

Example prompt file (`$XDG_CONFIG_HOME/pipai/prompts/summarize_csv`):

```toml
summary = "Analyze CSV data and provide key insights"

prompt = """
Analyze this CSV data and provide a summary of the key trends and insights.
Focus on patterns, outliers, and actionable recommendations.
"""
```

#### Managing Prompts

pipai provides commands to create, edit, and delete pre-defined prompts:

```bash
# Create a new prompt
pipai --create-prompt summarize_csv

# Edit an existing prompt using your default editor ($EDITOR)
pipai --edit-prompt summarize_csv

# Delete an existing prompt
pipai --delete-prompt summarize_csv
```

When creating a prompt, you'll be prompted to enter a summary and the prompt text.

### Managing Conversations

pipai supports multi-turn conversations with LLMs, allowing you to maintain context across multiple queries:

```bash
# Start a new conversation
pipai --start-conversation "Tell me about quantum computing"

# Continue the conversation (automatically uses previous context)
pipai "What are the practical applications?"

# Make a one-off query without affecting the conversation
pipai --no-conversation "What's the weather today?"

# Continue the conversation
pipai "Which companies are leaders in quantum computing?"

# Stop the conversation when you're done
pipai --stop-conversation
```

### Output Formatting

pipai can render responses in Markdown format for better readability in the terminal:

```bash
# Enable markdown formatting for a specific query
pipai --markdown "Explain neural networks with code examples"

# Disable markdown formatting for a specific query
pipai --no-markdown "Give me a simple text response"
```

You can also set the default behavior in your config file:

```
# In $XDG_CONFIG_HOME/pipai/config
MARKDOWN_FORMATTING=true
ENABLE_MCP_TOOLS=false
```

If you try to continue a conversation that's been inactive for more than 1 hour, pipai will ask if you want to:
- Continue the existing conversation
- Stop the old conversation and start fresh
- Abort the current query

### MCP Tools Configuration

pipai supports the Model Control Protocol (MCP) for enabling LLMs to use external tools. To configure MCP tools:

1. Create an MCP server configuration file:

```
$XDG_CONFIG_HOME/pipai/mcp_servers.json
```

Example configuration:

```json
{
  "mcpServers": {
    "git": {
      "command": "mcp-server-git",
      "args": [],
      "env": {}
    },
    "browser": {
      "command": "mcp-server-fetch",
      "args": [],
      "env": {}
    }
  }
}
```

2. Enable MCP tools in your config file:

```
# In $XDG_CONFIG_HOME/pipai/config
ENABLE_MCP_TOOLS=true
```

You can also enable MCP tools for a single session using the `--enable-mcp-tools` flag.

## Usage

### Basic Commands

```bash
# Show help
pipai --help

# Use with a simple prompt
pipai "What is the capital of France?"

# Pipe output from another command as context
cat file.txt | pipai "Summarize this text"
```

### Working with Models

```bash
# List all available models
pipai --models

# List models containing "gpt" in their name
pipai --models gpt

# Use a specific model
pipai --model gpt-3.5-turbo "What is the capital of France?"
```

### Working with Prompts

```bash
# List available pre-defined prompts
pipai --prompts

# Use a pre-defined prompt
pipai --code_explainer "Explain this function"

# Combine multiple pre-defined prompts
pipai --markdown_output --code_explainer "Document this code"

# Use pre-defined prompts with piped input
cat main.py | pipai --code_explainer "Focus on the main function"

# Create a new prompt
pipai --create-prompt my_custom_prompt

# Edit an existing prompt
pipai --edit-prompt code_explainer

# Delete a prompt you no longer need
pipai --delete-prompt old_prompt
```

### Managing Conversations

```bash
# Start a new conversation
pipai --start-conversation "Tell me about quantum computing"

# Continue the conversation with follow-up questions
pipai "What are the practical applications?"

# Make a one-off query without affecting the conversation
pipai --no-conversation "What's the weather today?"

# End the conversation
pipai --stop-conversation
```

### Using MCP Tools

MCP (Model Control Protocol) allows LLMs to use external tools to perform tasks like fetching web content, interacting with git repositories, and more.

```bash
# Enable MCP tools for a single session
pipai --enable-mcp-tools "Clone the repository at https://github.com/example/repo.git"

# Ask questions that might require tools
pipai --enable-mcp-tools "What are the latest commits in the current git repository?"

# Fetch and summarize web content
pipai --enable-mcp-tools "Summarize the content from https://example.com"
```

When MCP tools are enabled, the LLM will automatically decide when to use tools based on your query. You don't need to explicitly specify which tool to use.

## Examples

```bash
# Summarize a log file
cat logs.txt | pipai "Summarize these logs and identify any errors"

# Explain code with a pre-defined prompt
cat main.py | pipai --code_explainer "Focus on the main function"

# Analyze data with multiple prompts
cat data.json | pipai --json_output --data_scientist "Highlight growth opportunities"

# Use fun personality prompts
cat bird_sighting.txt | pipai --bird_enthusiast "Identify this bird species"

# Have a multi-turn conversation
pipai --start-conversation "Tell me about quantum computing"
pipai "What are the practical applications?"
pipai "Which companies are leaders in this field?"
pipai --stop-conversation

# Use MCP tools to interact with git repositories
pipai --enable-mcp-tools "What files changed in the last commit?"

# Use MCP tools to fetch and analyze web content
pipai --enable-mcp-tools "Summarize the main points from https://example.com/article"

# Combine MCP tools with other features
pipai --markdown --enable-mcp-tools "Create a table of the top 5 contributors to this git repository"

### Setting Configuration

You can modify configuration settings directly from the command line:

```bash
# Set the default LLM model
pipai --set-config DEFAULT_LLM=claude-3-opus-20240229

# Enable markdown formatting by default
pipai --set-config MARKDOWN_FORMATTING=true

# Disable MCP tools by default
pipai --set-config ENABLE_MCP_TOOLS=false
```

### Viewing Configuration

You can view the currently active configuration settings:

```bash
pipai --show-config
```

This will display the values loaded from your configuration file, including defaults.

```

## Bash Auto-completion

To enable bash auto-completion for pipai commands:

```bash
# Create the directory if it doesn't exist
mkdir -p ~/.local/share/pipai

# Copy the completion script
cp pipai-completion.sh ~/.local/share/pipai/bash_completion

# Add to your .bashrc or .bash_profile
echo 'source ~/.local/share/pipai/bash_completion' >> ~/.bashrc

# Apply changes to current session
source ~/.bashrc
```

This will enable tab completion for pipai commands, options, and available models.

## Requirements

- Python 3.12+
- LiteLLM
