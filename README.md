# pipai - Python LLM CLI Tool

A command-line tool that uses LiteLLM to interact with various LLM models. It takes the output of a previous command as context and a user-defined prompt to generate responses.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
  - [Default Model](#default-model)
  - [Pre-defined Prompts](#pre-defined-prompts)
  - [Conversation History](#conversation-history)
- [Usage](#usage)
  - [Basic Commands](#basic-commands)
  - [Working with Models](#working-with-models)
  - [Working with Prompts](#working-with-prompts)
  - [Managing Conversation History](#managing-conversation-history)
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
```

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
