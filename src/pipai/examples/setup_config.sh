#!/bin/bash
# Setup script for pipai configuration

set -e

# Determine config directory
if [ -n "$XDG_CONFIG_HOME" ]; then
    CONFIG_DIR="$XDG_CONFIG_HOME/pipai"
else
    CONFIG_DIR="$HOME/.config/pipai"
fi

PROMPT_DIR="$CONFIG_DIR/prompts"

# Create directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$PROMPT_DIR"

# Create config file if it doesn't exist
if [ ! -f "$CONFIG_DIR/config" ]; then
    cat > "$CONFIG_DIR/config" << EOF
# pipai configuration

# Set your default LLM model
# DEFAULT_LLM=gpt-3.5-turbo
EOF
    echo "Created config file: $CONFIG_DIR/config"
fi

# Copy example prompts
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
if [ -f "$SCRIPT_DIR/code_explainer" ]; then
    cp "$SCRIPT_DIR/code_explainer" "$PROMPT_DIR/"
    echo "Installed example prompt: code_explainer"
fi

echo "Configuration setup complete!"
echo "Your config directory is: $CONFIG_DIR"
echo "Your prompts directory is: $PROMPT_DIR"
echo ""
echo "To set a default model, edit: $CONFIG_DIR/config"
echo "To create custom prompts, add files to: $PROMPT_DIR"
