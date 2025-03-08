# pipai - Python LLM CLI Tool

A command-line tool that uses LiteLLM to interact with various LLM models. It takes the output of a previous command as context and a user-defined prompt to generate responses.

## Installation

```bash
# Using uv
uv venv
uv pip install git+https://github.com/fractalwire/pipai.git
ln -s $(PWD)/.venv/bin/pipai /usr/bin/pipai
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

Each file in this directory becomes a command-line option. For example, if you create:

```
$XDG_CONFIG_HOME/pipai/prompts/summarize_csv
```

With content:

```
Analyze this CSV data and provide a summary of the key trends and insights.
```

You can use it with:

```bash
pipai --summarize_csv --model gpt-3.5-turbo "Focus on the financial aspects"
```

## Usage

### List available models

```bash
# List all available models
pipai --models

# List models containing "gpt" in their name
pipai --models gpt
```

### List available prompts

```bash
pipai --prompts
```

### Generate a response

```bash
# Use a specific model with prompt as command line argument
pipai --model gpt-3.5-turbo "What is the capital of France?"

# Use the default model (if configured)
pipai "What is the capital of France?"

# Pipe output from another command as context
cat file.txt | pipai --model gpt-3.5-turbo "Summarize this text"

# Use pre-defined prompts with additional command line prompt
cat data.csv | pipai --summarize_csv --financial_advisor "Focus on Q3 results"

# Use pre-defined prompts without command line prompt
cat data.csv | pipai --summarize_csv --financial_advisor
```

When using the tool, it will:
1. Take any piped input as context
2. Combine any pre-defined prompts you specified
3. Add your command-line prompt
4. Send everything to the specified LLM model
5. Display the response

## Examples

```bash
# Summarize a log file
cat logs.txt | pipai --model gpt-3.5-turbo "Summarize these logs and identify any errors"

# Explain code with a pre-defined prompt
cat main.py | pipai --code_explainer "Focus on the main function"

# Analyze data with multiple prompts
cat data.json | pipai --json_analyzer --data_scientist --financial_advisor "Highlight growth opportunities"
```

## Requirements

- Python 3.12+
- LiteLLM
