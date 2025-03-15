#!/usr/bin/env python3
"""Command-line tool for interacting with LLM models using LiteLLM.

This tool takes the output of a previous command as context and a user-defined prompt
to generate responses from LLM models.
"""

import argparse
import sys
from typing import Dict, List, Optional

import litellm

from pipai.config import (
    ensure_config_dirs,
    get_available_prompts,
    get_default_llm,
    get_prompt_summary,
    load_prompt,
    load_conversation,
    start_conversation,
    stop_conversation,
    add_message_to_conversation,
    get_conversation_messages,
    is_conversation_expired,
)


def list_models(filter_string: Optional[str] = None) -> None:
    """List available LLM models, optionally filtered by a string.

    Args:
        filter_string: Optional string to filter model names by
    """
    # Get models from litellm's model_list
    models: List[str] = litellm.model_list

    if filter_string:
        models = [model for model in models if filter_string.lower() in model.lower()]

    if not models:
        print(
            "No models found"
            + (f" matching '{filter_string}'" if filter_string else "")
        )
        return

    print("Available models:")
    for model in sorted(models):
        print(f"  - {model}")


def list_prompts() -> None:
    """List available pre-defined prompts."""
    prompts = get_available_prompts()

    if not prompts:
        print("No pre-defined prompts found")
        return

    print("Available prompts:")
    for prompt in sorted(prompts):
        print(f"  - {prompt}")


def check_conversation_expiry() -> bool:
    """Check if conversation has expired and prompt user for action.

    Returns:
        True if should continue with query, False if should abort
    """
    if is_conversation_expired():
        print("Your conversation is more than 1 hour old.")
        while True:
            choice = input(
                "Do you want to (c)ontinue, (s)top it, or (a)bort this query? [c/s/a]: "
            ).lower()
            if choice in ("c", "continue"):
                return True
            elif choice in ("s", "stop"):
                stop_conversation()
                print("Conversation stopped.")
                return True
            elif choice in ("a", "abort"):
                return False
            else:
                print("Invalid choice. Please enter 'c', 's', or 'a'.")
    return True


def process_input(
    model_name: str,
    user_prompt: str,
    predefined_prompts: Dict[str, str],
    use_conversation: bool = True,
) -> None:
    """Process stdin input as context and use provided prompt.

    Args:
        model_name: Name of the LLM model to use
        user_prompt: User prompt to send to the model
        predefined_prompts: Dictionary of pre-defined prompts to include
        use_conversation: Whether to use conversation history
    """
    # Check for expired conversation
    if use_conversation and not check_conversation_expiry():
        print("Query aborted.")
        return

    # Read from stdin if available
    if not sys.stdin.isatty():
        context = sys.stdin.read().strip()
    else:
        context = ""

    # Prepare messages for the LLM
    messages = []

    # Add predefined prompts as system prompts
    if predefined_prompts:
        system_content = ""
        for name, content in predefined_prompts.items():
            system_content += f"[{name}]\n{content}\n\n"

        messages.append({"role": "system", "content": system_content.strip()})

        # Add system message to conversation if this is a new conversation
        conversation = load_conversation()
        if use_conversation and conversation and not conversation.get("messages"):
            add_message_to_conversation("system", system_content.strip())

    # Add conversation history if available
    if use_conversation:
        history_messages = get_conversation_messages()
        if history_messages:
            messages.extend(history_messages)

    # Combine context and user prompt as user message
    user_content = ""
    if context:
        user_content += f"# Data:\n{context}\n\n"

    if user_prompt:
        user_content += f"# Prompt: {user_prompt}"

    if user_content:
        messages.append({"role": "user", "content": user_content.strip()})

        # Add user message to conversation history
        if use_conversation:
            add_message_to_conversation("user", user_content.strip())

    try:
        response = litellm.completion(model=model_name, messages=messages)
        assistant_response = response.choices[0].message.content
        print(assistant_response)

        # Add assistant response to conversation history
        if use_conversation:
            add_message_to_conversation("assistant", assistant_response)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI tool."""
    # Ensure config directories exist
    ensure_config_dirs()

    # Get available prompts for dynamic argument creation
    available_prompts = get_available_prompts()

    parser = argparse.ArgumentParser(description="LLM command-line tool using LiteLLM")

    # Create mutually exclusive group for primary commands
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--models",
        metavar="FILTER",
        nargs="?",
        const="",
        help="List available models, optionally filtered by string",
    )
    group.add_argument(
        "--model",
        metavar="MODEL_NAME",
        help="Specify the model to use for generating a response",
    )
    group.add_argument(
        "--prompts",
        action="store_true",
        help="List available pre-defined prompts",
    )

    # Add conversation management arguments
    conversation_group = parser.add_argument_group("Conversation Management")
    conversation_group.add_argument(
        "--start-conversation",
        action="store_true",
        help="Start a new conversation",
    )
    conversation_group.add_argument(
        "--stop-conversation",
        action="store_true",
        help="Stop the current conversation",
    )
    conversation_group.add_argument(
        "--no-conversation",
        action="store_true",
        help="Don't use conversation history for this query",
    )

    # Create a prompt group for predefined prompts
    prompt_group = parser.add_argument_group("Predefined Prompts")

    # Add arguments for each available prompt
    for prompt_name in available_prompts:
        summary = get_prompt_summary(prompt_name)
        prompt_group.add_argument(
            f"--{prompt_name}",
            action="store_true",
            help=summary,
        )

    # Add prompt as a positional argument
    parser.add_argument(
        "prompt", nargs="?", default=None, help="The prompt to send to the LLM model"
    )

    args = parser.parse_args()

    if args.models is not None:
        list_models(args.models)
        return

    if args.prompts:
        list_prompts()
        return

    # Handle conversation management
    if args.stop_conversation:
        stop_conversation()
        print("Conversation stopped.")
        return

    if args.start_conversation:
        stop_conversation()  # Stop any existing conversation first
        start_conversation()
        print("New conversation started.")
        if args.prompt is None:
            return  # If no prompt provided, just start the conversation and exit

    # Get model name (from args or default)
    model_name = args.model
    if not model_name:
        model_name = get_default_llm()

    if not model_name:
        parser.error("No model specified. Use --model or set DEFAULT_LLM in config.")
        return

    # Check if we have any predefined prompts
    predefined_prompts = {}
    has_predefined_prompts = False
    for prompt_name in available_prompts:
        if getattr(args, prompt_name, False):
            content = load_prompt(prompt_name)
            if content:
                predefined_prompts[prompt_name] = content
                has_predefined_prompts = True

    # Check if we need a prompt
    if args.prompt is None and not has_predefined_prompts:
        parser.error(
            "A prompt is required when using --model "
            "(either as command line argument or from predefined prompts)"
        )
        return

    # Use empty string if no command line prompt was provided
    user_prompt = args.prompt if args.prompt is not None else ""

    # Determine if we should use conversation
    conversation = load_conversation()
    use_conversation = not args.no_conversation and (
        args.start_conversation or (conversation and conversation.get("active", False))
    )

    process_input(model_name, user_prompt, predefined_prompts, use_conversation)


if __name__ == "__main__":
    main()
