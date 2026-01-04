"""
Command-line interface for LocalMind
Beautiful, interactive CLI using Rich and Click
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from typing import Optional
import sys
import os

from ..utils.config import ConfigManager
from ..utils.logger import setup_logger
from ..core.model_loader import ModelLoader

# Configure console for Windows encoding issues
if sys.platform == "win32":
    # Set UTF-8 encoding for Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    # Use legacy_windows=False to avoid encoding issues
    console = Console(legacy_windows=False, force_terminal=True)
else:
    console = Console()

logger = setup_logger()


@click.group()
@click.option("--config", type=click.Path(), help="Path to config file")
@click.pass_context
def cli(ctx, config):
    """LocalMind - Privacy-focused local AI"""
    ctx.ensure_object(dict)
    ctx.obj["config_manager"] = ConfigManager(config_path=config)
    ctx.obj["model_loader"] = ModelLoader(ctx.obj["config_manager"])


@cli.command()
def version():
    """Show version information"""
    console.print("[bold blue]LocalMind[/bold blue] v0.1.0")
    console.print("Privacy-focused local AI")


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status"""
    config_manager = ctx.obj["config_manager"]
    model_loader = ctx.obj["model_loader"]
    config = config_manager.get_config()
    
    # Create status table
    table = Table(title="LocalMind Status", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    # Check backends
    for backend_name, backend in model_loader.backends.items():
        status_icon = "[green]OK[/green]" if backend.is_available() else "[red]FAIL[/red]"
        models = backend.list_models()
        table.add_row(
            f"Backend: {backend_name}",
            status_icon,
            f"{len(models)} models available"
        )
    
    # Default model
    table.add_row(
        "Default Model",
        "[cyan]SET[/cyan]",
        config.default_model or "Not set"
    )
    
    console.print(table)


@cli.command()
@click.pass_context
def models(ctx):
    """List available models"""
    model_loader = ctx.obj["model_loader"]
    available_models = model_loader.list_available_models()
    
    if not available_models:
        console.print("[yellow]Warning: No models available. Make sure backends are configured.[/yellow]")
        return
    
    for backend_name, models_list in available_models.items():
        console.print(f"\n[bold cyan]{backend_name}[/bold cyan]")
        if models_list:
            for model in models_list:
                console.print(f"  • {model}")
        else:
            console.print("  [dim]No models found[/dim]")


@cli.command()
@click.argument("prompt", required=False)
@click.option("--model", "-m", help="Model to use")
@click.option("--system", "-s", help="System prompt")
@click.option("--temperature", "-t", type=float, help="Temperature (0.0-2.0)")
@click.option("--stream", is_flag=True, help="Stream output")
@click.pass_context
def chat(ctx, prompt, model, system, temperature, stream):
    """Chat with LocalMind (interactive mode if no prompt)"""
    model_loader = ctx.obj["model_loader"]
    
    if prompt:
        # Single prompt mode
        try:
            response = model_loader.generate(
                prompt=prompt,
                model=model,
                system_prompt=system,
                temperature=temperature
            )
            console.print(Markdown(response.text))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        # Interactive mode
        console.print(Panel.fit(
            "[bold blue]LocalMind[/bold blue] - Interactive Chat Mode\n"
            "Type your message and press Enter. Type 'exit' or 'quit' to end.",
            border_style="blue"
        ))
        
        conversation_history = []
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if not user_input.strip():
                    continue
                
                # Build context from history
                context = "\n".join([
                    f"User: {msg['user']}\nAssistant: {msg['assistant']}"
                    for msg in conversation_history[-5:]  # Last 5 exchanges
                ])
                
                full_prompt = f"{context}\nUser: {user_input}\nAssistant:" if context else user_input
                
                console.print("[dim]Thinking...[/dim]")
                
                try:
                    response = model_loader.generate(
                        prompt=full_prompt,
                        model=model,
                        system_prompt=system or "You are a helpful AI assistant.",
                        temperature=temperature or 0.7
                    )
                    
                    console.print(f"\n[bold green]LocalMind[/bold green]")
                    console.print(Markdown(response.text))
                    
                    # Save to history
                    conversation_history.append({
                        "user": user_input,
                        "assistant": response.text
                    })
                    
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except EOFError:
                break


@cli.command()
@click.pass_context
def setup(ctx):
    """Interactive setup wizard"""
    config_manager = ctx.obj["config_manager"]
    config = config_manager.get_config()
    
    console.print(Panel.fit(
        "[bold blue]LocalMind Setup Wizard[/bold blue]\n"
        "Let's configure your local AI setup.",
        border_style="blue"
    ))
    
    # Check Ollama
    console.print("\n[cyan]Checking Ollama...[/cyan]")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            console.print("[green]Ollama is running![/green]")
            ollama_models = [m["name"] for m in response.json().get("models", [])]
            if ollama_models:
                console.print(f"   Found {len(ollama_models)} models")
            else:
                console.print("[yellow]Warning: No models found. Install one with: ollama pull llama2[/yellow]")
        else:
            console.print("[yellow]Warning: Ollama not responding[/yellow]")
    except Exception:
        console.print("[yellow]Warning: Ollama not found. Install from https://ollama.ai[/yellow]")
    
    # Check API backends
    console.print("\n[cyan]Checking API Backends...[/cyan]")
    api_backends = {
        "openai": ("OPENAI_API_KEY", "OpenAI (ChatGPT)"),
        "anthropic": ("ANTHROPIC_API_KEY", "Anthropic (Claude)"),
        "google": ("GOOGLE_API_KEY", "Google (Gemini)"),
        "mistral-ai": ("MISTRAL_AI_API_KEY", "Mistral AI"),
        "cohere": ("COHERE_API_KEY", "Cohere"),
        "groq": ("GROQ_API_KEY", "Groq")
    }
    
    for backend_name, (env_var, display_name) in api_backends.items():
        backend_config = config.backends.get(backend_name)
        if backend_config:
            api_key = os.getenv(env_var) or backend_config.settings.get("api_key", "")
            if api_key and backend_config.enabled:
                console.print(f"[green]✓ {display_name} - Configured and enabled[/green]")
            elif api_key:
                console.print(f"[yellow]○ {display_name} - API key set but disabled[/yellow]")
            elif backend_config.enabled:
                console.print(f"[yellow]○ {display_name} - Enabled but no API key[/yellow]")
            else:
                console.print(f"[dim]○ {display_name} - Not configured[/dim]")
    
    console.print("\n[green]Setup complete![/green]")
    console.print("Run 'python scripts/configure_apis.py' to configure API keys")
    console.print("Or run 'localmind chat' to start chatting!")


@cli.command()
@click.pass_context
def configure(ctx):
    """Configure API keys for AI providers"""
    config_manager = ctx.obj["config_manager"]
    config = config_manager.get_config()
    
    console.print(Panel.fit(
        "[bold blue]API Configuration[/bold blue]\n"
        "Configure API keys for AI providers",
        border_style="blue"
    ))
    
    providers = [
        {
            "name": "openai",
            "display": "OpenAI (ChatGPT)",
            "env_var": "OPENAI_API_KEY",
            "setup_url": "https://platform.openai.com/api-keys"
        },
        {
            "name": "anthropic",
            "display": "Anthropic (Claude)",
            "env_var": "ANTHROPIC_API_KEY",
            "setup_url": "https://console.anthropic.com/"
        },
        {
            "name": "google",
            "display": "Google (Gemini)",
            "env_var": "GOOGLE_API_KEY",
            "setup_url": "https://makersuite.google.com/app/apikey"
        },
        {
            "name": "mistral-ai",
            "display": "Mistral AI",
            "env_var": "MISTRAL_AI_API_KEY",
            "setup_url": "https://console.mistral.ai/"
        },
        {
            "name": "cohere",
            "display": "Cohere",
            "env_var": "COHERE_API_KEY",
            "setup_url": "https://dashboard.cohere.com/api-keys"
        },
        {
            "name": "groq",
            "display": "Groq (Fast Inference)",
            "env_var": "GROQ_API_KEY",
            "setup_url": "https://console.groq.com/keys"
        }
    ]
    
    console.print("\n[cyan]Current Configuration:[/cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("API Key", style="yellow")
    
    for provider in providers:
        backend_config = config.backends.get(provider["name"])
        if backend_config:
            api_key = os.getenv(provider["env_var"]) or backend_config.settings.get("api_key", "")
            status = "Enabled" if backend_config.enabled else "Disabled"
            key_status = "Set" if api_key else "Not set"
            table.add_row(provider["display"], status, key_status)
        else:
            table.add_row(provider["display"], "Not configured", "Not set")
    
    console.print(table)
    
    console.print("\n[cyan]Configure a provider:[/cyan]")
    for i, provider in enumerate(providers, 1):
        console.print(f"  {i}. {provider['display']}")
    console.print("  0. Exit")
    
    try:
        choice = Prompt.ask("\nSelect provider to configure", default="0")
        idx = int(choice) - 1
        
        if idx == -1:
            return
        
        if 0 <= idx < len(providers):
            provider = providers[idx]
            backend_config = config.backends.get(provider["name"])
            
            if not backend_config:
                from ..utils.config import BackendConfig
                # Map provider names to backend types
                type_map = {
                    "openai": "openai",
                    "anthropic": "anthropic",
                    "google": "google",
                    "mistral-ai": "mistral-ai",
                    "cohere": "cohere",
                    "groq": "groq"
                }
                backend_config = BackendConfig(
                    type=type_map.get(provider["name"], provider["name"]),
                    enabled=False,
                    settings={}
                )
                config.backends[provider["name"]] = backend_config
            
            console.print(f"\n[bold]{provider['display']} Configuration[/bold]")
            console.print(f"Get API key: {provider['setup_url']}")
            
            api_key = Prompt.ask("Enter API key (or press Enter to skip)", default="", show_default=False)
            if api_key:
                backend_config.settings["api_key"] = api_key
                console.print("[green]API key saved![/green]")
            
            enable = Confirm.ask("Enable this backend?", default=backend_config.enabled)
            backend_config.enabled = enable
            
            config_manager.config = config
            config_manager.save_config()
            
            console.print("[green]Configuration saved![/green]")
            console.print("[yellow]Restart the server for changes to take effect.[/yellow]")
        else:
            console.print("[red]Invalid selection[/red]")
    except (ValueError, KeyboardInterrupt):
        console.print("\n[yellow]Configuration cancelled[/yellow]")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", default=5000, type=int, help="Port to listen on (default: 5000)")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def web(ctx, host, port, debug):
    """Start web interface server"""
    try:
        from ..web.server import WebServer
        
        config_manager = ctx.obj["config_manager"]
        server = WebServer(config_manager, host=host, port=port)
        
        console.print(Panel.fit(
            f"[bold blue]LocalMind Web Server[/bold blue]\n"
            f"Starting server on [cyan]http://{host}:{port}[/cyan]\n"
            f"Access the web interface from any device on your network!",
            border_style="blue"
        ))
        
        server.run(debug=debug)
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
        console.print(f"[red]Error: Missing dependency: {missing_module}[/red]")
        console.print(f"[yellow]Please install all dependencies:[/yellow]")
        console.print(f"[cyan]  pip install -r requirements.txt[/cyan]")
        console.print(f"[dim]{e}[/dim]")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        if "No module named" in error_msg:
            missing_module = error_msg.split("'")[1] if "'" in error_msg else "unknown"
            console.print(f"[red]Error: Missing dependency: {missing_module}[/red]")
            console.print(f"[yellow]Please install all dependencies:[/yellow]")
            console.print(f"[cyan]  pip install -r requirements.txt[/cyan]")
        else:
            console.print(f"[red]Error starting web server: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()

