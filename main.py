import typer
import subprocess
import os

from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from pathlib import Path
from typing import Optional
from toml import load as toml_load

app = typer.Typer()
console = Console()

def load_config() -> dict:
    config_path = Path("spec.toml")
    if not config_path.exists():
        console.print("[bold red]Spec file 'spec.toml' not found![/]")
        raise typer.Exit(code=1)
    
    return toml_load(config_path)

@app.command()
def run(
    command: str = typer.Argument(..., help="Command to run"),
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Path to the spec file (default: spec.toml)"),
):
    """Run a command with the specified spec."""
    if spec:
        config_path = Path(spec)
    else:
        config_path = Path("spec.toml")

    if not config_path.exists():
        console.print(f"[bold red]Spec file '{config_path}' not found![/]")
        raise typer.Exit(code=1)

    config = load_config()
    
    # Display the spec in a table format
    table = Table(title="Spec Configuration")
    for key, value in config.items():
        table.add_column(key, justify="left", style="cyan")
        table.add_row(str(value))
    
    console.print(table)

    # Run the command
    try:
        result = subprocess.run(command, shell=True, check=True)
        console.print(f"[bold green]Command '{command}' executed successfully![/]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Command failed with error: {e}[/]")
        raise typer.Exit(code=1)

@app.command()
def new(
    name: str = typer.Argument(..., help="Name of the new spec"),
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Path to the spec file (default: spec.toml)"),
):
    """Create a new spec file."""
    if spec:
        config_path = Path(spec)
    else:
        config_path = Path("spec.toml")

    if config_path.exists():
        console.print(f"[bold red]Spec file '{config_path}' already exists![/]")
        raise typer.Exit(code=1)

    # Create a new spec file with default content
    default_content = {
        "name": name,
        "version": "0.1.0",
        "description": f"Spec for {name}",
        "commands": [],
        "target": "arm-none-eabi",
        "packages": []
    }
    
    with open(config_path, 'w') as f:
        toml.dump(default_content, f)
    
    console.print(f"[bold green]New spec file '{config_path}' created successfully![/]")

if __name__ == "__main__":
    app()
