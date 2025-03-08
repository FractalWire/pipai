#!/usr/bin/env python3
"""
A command-line tool that uses LiteLLM to interact with various LLM models.
It takes the output of a previous command as context and a user-defined prompt
to generate responses from LLM models.
"""

import sys
import argparse
import litellm

def list_models(filter_string=None):
    """List available LLM models, optionally filtered by a string."""
    # Get models from litellm's model_list
    models = litellm.model_list
    
    if filter_string:
        models = [model for model in models if filter_string.lower() in model.lower()]
    
    if not models:
        print("No models found" + (f" matching '{filter_string}'" if filter_string else ""))
        return
    
    print("Available models:")
    for model in sorted(models):
        print(f"  - {model}")

def process_input(model_name, prompt):
    """Process stdin input as context and use provided prompt."""
    # Read from stdin if available
    if not sys.stdin.isatty():
        context = sys.stdin.read().strip()
    else:
        context = ""
    
    # Combine context and prompt
    full_prompt = f"Context:\n{context}\n\nPrompt: {prompt}"
    
    try:
        response = litellm.completion(
            model=model_name,
            messages=[{"role": "user", "content": full_prompt}]
        )
        print("\nResponse:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="LLM command-line tool using LiteLLM")
    
    # Create mutually exclusive group for --models and --model
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--models", metavar="FILTER", nargs="?", const="", 
                      help="List available models, optionally filtered by string")
    group.add_argument("--model", metavar="MODEL_NAME", 
                      help="Specify the model to use for generating a response")
    
    # Add prompt as a positional argument
    parser.add_argument("prompt", nargs="?", default=None,
                      help="The prompt to send to the LLM model")
    
    args = parser.parse_args()
    
    if args.models is not None:
        list_models(args.models)
    elif args.model:
        if args.prompt is None:
            parser.error("A prompt is required when using --model")
        process_input(args.model, args.prompt)

if __name__ == "__main__":
    main()
