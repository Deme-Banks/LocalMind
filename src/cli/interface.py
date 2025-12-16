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

from ..utils.config import ConfigManager
from ..utils.logger import setup_logger
from ..core.model_loader import ModelLoader


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
        status_icon = "✅" if backend.is_available() else "❌"
        models = backend.list_models()
        table.add_row(
            f"Backend: {backend_name}",
            status_icon,
            f"{len(models)} models available"
        )
    
    # Default model
    table.add_row(
        "Default Model",
        "📌",
        config.default_model
    )
    
    console.print(table)


@cli.command()
@click.pass_context
def models(ctx):
    """List available models"""
    model_loader = ctx.obj["model_loader"]
    available_models = model_loader.list_available_models()
    
    if not available_models:
        console.print("[yellow]⚠️  No models available. Make sure backends are configured.[/yellow]")
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
                    console.print("[yellow]Goodbye! 👋[/yellow]")
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
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
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
            console.print("[green]✅ Ollama is running![/green]")
            ollama_models = [m["name"] for m in response.json().get("models", [])]
            if ollama_models:
                console.print(f"   Found {len(ollama_models)} models")
            else:
                console.print("[yellow]⚠️  No models found. Install one with: ollama pull llama2[/yellow]")
        else:
            console.print("[yellow]⚠️  Ollama not responding[/yellow]")
    except Exception:
        console.print("[yellow]⚠️  Ollama not found. Install from https://ollama.ai[/yellow]")
    
    console.print("\n[green]✅ Setup complete![/green]")
    console.print("Run 'localmind chat' to start chatting!")


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()

