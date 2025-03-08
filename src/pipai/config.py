"""Configuration handling for pipai.

This module handles loading configuration from the XDG config directory
and managing pre-defined prompts.
"""

import os
import pathlib
from typing import Dict, List, Optional


def get_config_dir() -> pathlib.Path:
    """Get the configuration directory for pipai.

    Returns:
        Path to the configuration directory
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        base_dir = pathlib.Path(xdg_config_home)
    else:
        # Default to ~/.config if XDG_CONFIG_HOME is not set
        base_dir = pathlib.Path.home() / ".config"

    return base_dir / "pipai"


def get_default_llm() -> Optional[str]:
    """Get the default LLM model from configuration.

    Returns:
        The default LLM model name or None if not configured
    """
    config_dir = get_config_dir()
    config_file = config_dir / "config"

    if not config_file.exists():
        return None

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DEFAULT_LLM="):
                return line.split("=", 1)[1].strip()

    return None


def get_prompt_dir() -> pathlib.Path:
    """Get the directory containing pre-defined prompts.

    Returns:
        Path to the prompts directory
    """
    return get_config_dir() / "prompts"


def get_available_prompts() -> List[str]:
    """Get a list of available pre-defined prompts.

    Returns:
        List of prompt names (without file extensions)
    """
    prompt_dir = get_prompt_dir()
    if not prompt_dir.exists():
        return []

    return [f.stem for f in prompt_dir.iterdir() if f.is_file()]


def load_prompt(prompt_name: str) -> Optional[str]:
    """Load a pre-defined prompt by name.

    Args:
        prompt_name: Name of the prompt to load

    Returns:
        The prompt content or None if not found
    """
    prompt_dir = get_prompt_dir()
    prompt_file = prompt_dir / prompt_name

    if not prompt_file.exists() and not prompt_file.is_file():
        return None

    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_prompts(prompt_names: List[str]) -> Dict[str, str]:
    """Load multiple pre-defined prompts.

    Args:
        prompt_names: List of prompt names to load

    Returns:
        Dictionary mapping prompt names to their content
    """
    result = {}
    for name in prompt_names:
        content = load_prompt(name)
        if content:
            result[name] = content
    return result


def ensure_config_dirs() -> None:
    """Ensure that configuration directories exist."""
    config_dir = get_config_dir()
    prompt_dir = get_prompt_dir()

    config_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    # Create default config file if it doesn't exist
    config_file = config_dir / "config"
    if not config_file.exists():
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("# pipai configuration\n")
            f.write("# Uncomment and set your default LLM model\n")
            f.write("# DEFAULT_LLM=gpt-3.5-turbo\n")
