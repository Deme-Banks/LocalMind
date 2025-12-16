#!/usr/bin/env python3
"""
API Configuration Wizard for LocalMind
Helps configure API keys for all AI providers
"""

import os
import sys
from pathlib import Path
from src.utils.config import ConfigManager

def print_header():
    print("=" * 60)
    print("  LocalMind API Configuration Wizard")
    print("=" * 60)
    print()

def get_api_key(provider_name, env_var, setup_url):
    """Get API key from user"""
    print(f"\n{provider_name} Configuration")
    print("-" * 60)
    print(f"Get your API key from: {setup_url}")
    print(f"Current value: {os.getenv(env_var, 'Not set')}")
    print()
    
    choice = input("Enter API key (or press Enter to skip): ").strip()
    if choice:
        return choice
    return None

def configure_backend(config_manager, backend_name, backend_type, api_key_env, setup_url, display_name):
    """Configure a backend"""
    config = config_manager.get_config()
    
    if backend_name not in config.backends:
        print(f"\n{display_name} is not in config. Adding...")
        from src.utils.config import BackendConfig
        config.backends[backend_name] = BackendConfig(
            type=backend_type,
            enabled=False,
            settings={}
        )
    
    backend_config = config.backends[backend_name]
    
    # Check current API key
    current_key = os.getenv(api_key_env) or backend_config.settings.get("api_key", "")
    
    print(f"\n{display_name} Configuration")
    print("-" * 60)
    print(f"Status: {'Enabled' if backend_config.enabled else 'Disabled'}")
    print(f"API Key: {'Set' if current_key else 'Not set'}")
    print(f"Get API key: {setup_url}")
    print()
    
    print("Options:")
    print("  1. Set API key")
    print("  2. Enable backend")
    print("  3. Disable backend")
    print("  4. Skip")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        api_key = input("Enter API key: ").strip()
        if api_key:
            backend_config.settings["api_key"] = api_key
            print(f"✓ API key set for {display_name}")
        else:
            print("No API key provided")
    elif choice == "2":
        backend_config.enabled = True
        print(f"✓ {display_name} enabled")
    elif choice == "3":
        backend_config.enabled = False
        print(f"✓ {display_name} disabled")
    elif choice == "4":
        print("Skipped")
    else:
        print("Invalid choice")
    
    config_manager.config = config
    config_manager.save_config()

def main():
    print_header()
    
    print("This wizard will help you configure API keys for AI providers.")
    print("You can configure multiple providers or skip ones you don't need.")
    print()
    
    config_manager = ConfigManager()
    
    providers = [
        {
            "name": "openai",
            "type": "openai",
            "env_var": "OPENAI_API_KEY",
            "setup_url": "https://platform.openai.com/api-keys",
            "display": "OpenAI (ChatGPT)"
        },
        {
            "name": "anthropic",
            "type": "anthropic",
            "env_var": "ANTHROPIC_API_KEY",
            "setup_url": "https://console.anthropic.com/",
            "display": "Anthropic (Claude)"
        },
        {
            "name": "google",
            "type": "google",
            "env_var": "GOOGLE_API_KEY",
            "setup_url": "https://makersuite.google.com/app/apikey",
            "display": "Google (Gemini)"
        },
        {
            "name": "mistral-ai",
            "type": "mistral-ai",
            "env_var": "MISTRAL_AI_API_KEY",
            "setup_url": "https://console.mistral.ai/",
            "display": "Mistral AI"
        },
        {
            "name": "cohere",
            "type": "cohere",
            "env_var": "COHERE_API_KEY",
            "setup_url": "https://dashboard.cohere.com/api-keys",
            "display": "Cohere"
        },
        {
            "name": "groq",
            "type": "groq",
            "env_var": "GROQ_API_KEY",
            "setup_url": "https://console.groq.com/keys",
            "display": "Groq (Fast Inference)"
        }
    ]
    
    print("Available AI Providers:")
    for i, provider in enumerate(providers, 1):
        config = config_manager.get_config()
        backend = config.backends.get(provider["name"])
        status = "✓ Enabled" if backend and backend.enabled else "○ Disabled"
        has_key = "✓ Key set" if (os.getenv(provider["env_var"]) or (backend and backend.settings.get("api_key"))) else "○ No key"
        print(f"  {i}. {provider['display']:30} {status:15} {has_key}")
    
    print()
    print("Options:")
    print("  1. Configure all providers")
    print("  2. Configure specific provider")
    print("  3. Show current configuration")
    print("  4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        # Configure all
        for provider in providers:
            configure_backend(
                config_manager,
                provider["name"],
                provider["type"],
                provider["env_var"],
                provider["setup_url"],
                provider["display"]
            )
    elif choice == "2":
        # Configure specific
        print("\nSelect provider to configure:")
        for i, provider in enumerate(providers, 1):
            print(f"  {i}. {provider['display']}")
        
        try:
            idx = int(input("\nEnter number: ").strip()) - 1
            if 0 <= idx < len(providers):
                provider = providers[idx]
                configure_backend(
                    config_manager,
                    provider["name"],
                    provider["type"],
                    provider["env_var"],
                    provider["setup_url"],
                    provider["display"]
                )
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
    elif choice == "3":
        # Show current config
        config = config_manager.get_config()
        print("\nCurrent Configuration:")
        print("-" * 60)
        for backend_name, backend_config in config.backends.items():
            if backend_name == "ollama":
                continue  # Skip Ollama
            api_key = os.getenv(f"{backend_name.upper().replace('-', '_')}_API_KEY") or backend_config.settings.get("api_key", "")
            key_status = "Set" if api_key else "Not set"
            print(f"{backend_name:20} | Enabled: {backend_config.enabled:5} | API Key: {key_status}")
    elif choice == "4":
        print("Exiting...")
        return
    else:
        print("Invalid choice")
        return
    
    print("\n" + "=" * 60)
    print("Configuration saved!")
    print("Restart the LocalMind server for changes to take effect.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
        sys.exit(0)

