# pipai - Python LLM CLI Tool

A command-line tool that uses LiteLLM to interact with various LLM models. It takes the output of a previous command as context and a user-defined prompt to generate responses.

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Project Structure

The project follows the standard Python packaging structure:

```
pipai/
├── src/
│   └── pipai/
│       ├── __init__.py
│       └── main.py
├── pyproject.toml
└── README.md
```

## Usage

### List available models

```bash
# List all available models
pipai --models

# List models containing "gpt" in their name
pipai --models gpt
```

### Generate a response

```bash
# Use a specific model with manual prompt input
pipai --model gpt-3.5-turbo

# Pipe output from another command as context
cat file.txt | pipai --model gpt-3.5-turbo
```

When using the `--model` option, the tool will:
1. Take any piped input as context
2. Prompt you to enter your question/prompt
3. Send both the context and prompt to the specified LLM model
4. Display the response

## Examples

```bash
# Summarize a log file
cat logs.txt | llm-cli --model gpt-3.5-turbo
# Then enter prompt: "Summarize these logs and identify any errors"

# Explain code
cat main.py | llm-cli --model claude-3-sonnet-20240229
# Then enter prompt: "Explain what this code does"
```

## Requirements

- Python 3.8+
- LiteLLM
