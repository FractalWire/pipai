"""Configuration handling for pipai.

This module handles loading configuration from the XDG config directory
and managing pre-defined prompts.
"""

import json
import os
import pathlib
import shutil
import subprocess
import time
from datetime import datetime, timedelta
import tomllib
from typing import Dict, List, Optional, Tuple, Any, Union


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


def get_config() -> Dict[str, Any]:
    """Get all configuration settings from the config file.

    Returns:
        Dictionary containing all configuration settings with their default values
    """
    # Define default configuration values
    config = {
        "DEFAULT_LLM": None,
        "MARKDOWN_FORMATTING": True,
    }

    config_dir = get_config_dir()
    config_file = config_dir / "config"

    if not config_file.exists():
        return config

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Process specific config types
                if key == "DEFAULT_LLM":
                    config[key] = value
                elif key == "MARKDOWN_FORMATTING":
                    config[key] = value.lower() in ("true", "yes", "1", "on")

    return config


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

    try:
        with open(prompt_file, "rb") as f:
            data = tomllib.load(f)
            return data.get("prompt", "").strip()
    except (tomllib.TOMLDecodeError, KeyError):
        # Fallback to reading the file as plain text for backward compatibility
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip()


def get_prompt_summary(prompt_name: str) -> Optional[str]:
    """Get the summary of a pre-defined prompt.

    Args:
        prompt_name: Name of the prompt to get summary for

    Returns:
        The prompt summary or None if not found
    """
    prompt_dir = get_prompt_dir()
    prompt_file = prompt_dir / prompt_name

    if not prompt_file.exists() and not prompt_file.is_file():
        return None

    try:
        with open(prompt_file, "rb") as f:
            data = tomllib.load(f)
            return data.get(
                "summary", f"Use the pre-defined '{prompt_name}' prompt"
            ).strip()
    except (tomllib.TOMLDecodeError, KeyError):
        return f"Use the pre-defined '{prompt_name}' prompt"


def create_prompt(name: str, summary: str, prompt_text: str) -> bool:
    """Create a new pre-defined prompt.

    Args:
        name: Name of the prompt to create
        summary: Summary description of the prompt
        prompt_text: The actual prompt text

    Returns:
        True if prompt was created successfully, False otherwise
    """
    prompt_dir = get_prompt_dir()
    prompt_file = prompt_dir / name

    # Check if prompt already exists
    if prompt_file.exists():
        return False

    # Create the prompt file
    prompt_content = f'summary = "{summary}"\n\nprompt = """\n{prompt_text}\n"""'

    try:
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)
        return True
    except Exception:
        return False


def delete_prompt(name: str) -> bool:
    """Delete a pre-defined prompt.

    Args:
        name: Name of the prompt to delete

    Returns:
        True if prompt was deleted successfully, False otherwise
    """
    prompt_dir = get_prompt_dir()
    prompt_file = prompt_dir / name

    # Check if prompt exists
    if not prompt_file.exists():
        return False

    try:
        prompt_file.unlink()
        return True
    except Exception:
        return False


def edit_prompt(name: str) -> bool:
    """Edit a pre-defined prompt using the default editor.

    Args:
        name: Name of the prompt to edit

    Returns:
        True if prompt was edited successfully, False otherwise
    """
    prompt_dir = get_prompt_dir()
    prompt_file = prompt_dir / name

    # Check if prompt exists
    if not prompt_file.exists():
        return False

    # Get the editor from environment or use a default
    editor = os.environ.get("EDITOR", "vim")

    try:
        # Open the file in the editor
        result = subprocess.run([editor, str(prompt_file)], check=True)

        if result.returncode != 0:
            return False

        # Validate the edited file
        try:
            with open(prompt_file, "rb") as f:
                tomllib.load(f)
            return True
        except tomllib.TOMLDecodeError:
            return False
    except Exception:
        return False


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


def get_conversation_file() -> pathlib.Path:
    """Get the file path for storing active conversation.

    Returns:
        Path to the conversation file
    """
    return get_config_dir() / "conversation.json"


def load_conversation() -> Dict[str, Any]:
    """Load the active conversation from the conversation file.

    Returns:
        Dictionary containing conversation data or empty dict if none exists
    """
    conversation_file = get_conversation_file()
    if not conversation_file.exists():
        return {}

    try:
        with open(conversation_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_conversation(conversation: Dict[str, Any]) -> None:
    """Save the conversation to the conversation file.

    Args:
        conversation: Dictionary containing conversation data
    """
    conversation_file = get_conversation_file()

    with open(conversation_file, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=2)


def start_conversation() -> None:
    """Start a new conversation."""
    conversation = {
        "active": True,
        "messages": [],
        "started_at": time.time(),
        "last_message_at": time.time(),
    }
    save_conversation(conversation)


def stop_conversation() -> None:
    """Stop the active conversation."""
    conversation_file = get_conversation_file()
    if conversation_file.exists():
        conversation_file.unlink()


def add_message_to_conversation(role: str, content: str) -> None:
    """Add a new message to the active conversation.

    Args:
        role: The role of the message sender (user, assistant, system)
        content: The content of the message
    """
    conversation = load_conversation()

    if not conversation or not conversation.get("active", False):
        # No active conversation
        return

    if "messages" not in conversation:
        conversation["messages"] = []

    # Add the new message
    conversation["messages"].append(
        {"role": role, "content": content, "timestamp": time.time()}
    )

    # Update last message timestamp
    conversation["last_message_at"] = time.time()

    save_conversation(conversation)


def get_conversation_messages() -> List[Dict[str, str]]:
    """Get messages from the active conversation formatted for LLM.

    Returns:
        List of message dictionaries with role and content keys
    """
    conversation = load_conversation()

    if not conversation or not conversation.get("active", False):
        return []

    # Format messages for LLM (remove timestamps)
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation.get("messages", [])
    ]


def is_conversation_expired(timeout_hours: float = 1.0) -> bool:
    """Check if the conversation has expired based on timeout.

    Args:
        timeout_hours: Number of hours after which a conversation is considered expired

    Returns:
        True if conversation has expired, False otherwise
    """
    conversation = load_conversation()

    if not conversation or not conversation.get("active", False):
        return False

    last_message_at = conversation.get("last_message_at", 0)
    expiration_time = last_message_at + (
        timeout_hours * 3600
    )  # Convert hours to seconds

    return time.time() > expiration_time


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
            f.write("\n# Enable or disable markdown formatting for responses\n")
            f.write("# MARKDOWN_FORMATTING=true\n")
