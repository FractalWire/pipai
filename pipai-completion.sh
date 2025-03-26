#!/usr/bin/env bash
# Bash completion script for pipai

_pipai_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Basic options
    opts="--models --model --prompts --create-prompt --edit-prompt --delete-prompt --start-conversation --stop-conversation --no-conversation --markdown --no-markdown --enable-mcp-tools --set-config --show-config"
    
    # Add dynamic prompts from config directory
    if [ -n "$XDG_CONFIG_HOME" ]; then
        PROMPT_DIR="$XDG_CONFIG_HOME/pipai/prompts"
    else
        PROMPT_DIR="$HOME/.config/pipai/prompts"
    fi
    
    if [ -d "$PROMPT_DIR" ]; then
        for prompt_file in "$PROMPT_DIR"/*; do
            if [ -f "$prompt_file" ]; then
                prompt_name=$(basename "$prompt_file")
                opts="$opts --$prompt_name"
            fi
        done
    fi
    
    # Handle specific options
    case "$prev" in
        --model)
            # Try to get models from litellm if possible
            if command -v pipai >/dev/null 2>&1; then
                models=$(pipai --models 2>/dev/null | grep -E '^\s*-' | sed 's/^\s*-\s*//')
                if [ -n "$models" ]; then
                    COMPREPLY=( $(compgen -W "$models" -- "$cur") )
                    return 0
                fi
            fi
            return 0
            ;;
        --models)
            # Suggest common model filters
            COMPREPLY=( $(compgen -W "gpt claude llama mistral" -- "$cur") )
            return 0
            ;;
        --edit-prompt|--delete-prompt)
            # Suggest available prompts for editing or deleting
            if [ -d "$PROMPT_DIR" ]; then
                prompts=$(find "$PROMPT_DIR" -type f -exec basename {} \; 2>/dev/null)
                COMPREPLY=( $(compgen -W "$prompts" -- "$cur") )
            fi
            return 0
            ;;
        --set-config)
            # Suggest known config keys
            COMPREPLY=( $(compgen -W "DEFAULT_LLM= MARKDOWN_FORMATTING= ENABLE_MCP_TOOLS=" -- "$cur") )
            return 0
            ;;
        *)
            ;;
    esac
    
    # Complete options if current word starts with -
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
        return 0
    fi
}

complete -F _pipai_completion pipai
