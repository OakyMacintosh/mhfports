import typer
import os
import subprocess

from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from pathlib import Path
from typing import Optional

app = typer.Typer()
console = Console()

@app.command()
def newdistro(
    name: str = typer.Argument(..., help="Name of the mighf distribution"),
  #  version: str = typer.Argument(..., help="Version of the mighf distribution"),
    description: str = typer.Argument(..., help="Description of the new distribution"),
):
    """Create a new distribution specification."""
    distro_spec = {
        "name": name,
   #     "version": version,
        "description": description,
    }
    
    # Display the created specification
    table = Table(title="New Distribution Specification")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")
    
    for key, value in distro_spec.items():
        table.add_row(key, value)
    
    console.print(table)
    console.print(Markdown("Distribution specification created successfully!"))
    # Save the specification to a file
    spec_path = Path(f"{name}_spec.json")
    with spec_path.open("w") as f:
        import json
        json.dump(distro_spec, f, indent=4)
    console.print(f"Specification saved to {spec_path}")

@app.command()
def parse_spec(
        spec_file: Path = typer.Argument(..., help="Path to the distribution specification file"),
):
    """Parse and display the distribution specification."""
    if not spec_file.exists():
        console.print(f"[red]Error:[/] Spec file {spec_file} does not exist.")
        raise typer.Exit(code=1)
    
    with spec_file.open("r") as f:
        import json
        spec_data = json.load(f)
    
    # Display the parsed specification
    table = Table(title="Parsed Distribution Specification")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")
    
    for key, value in spec_data.items():
        table.add_row(key, str(value))
    console.print(Markdown(f"### Distribution Specification from {spec_file}"))
    console.print(table)

@app.command()
def finish_distro(
    output: str = typer.Argument(..., help="Name of the output file for the finished distribution"),
    spec_file: Path = typer.Argument(..., help="Path to the distribution specification file"),
):
    """Finish the distribution by generating the output file."""
    if not spec_file.exists():
        console.print(f"[red]Error:[/] Spec file {spec_file} does not exist.")
        raise typer.Exit(code=1)
    
    with spec_file.open("r") as f:
        import json
        spec_data = json.load(f)
    
    # Here you would implement the logic to finalize the distribution
    # For now, we just save the spec data to the output file
    output_path = Path(output)
    with output_path.open("w") as f:
        json.dump(spec_data, f, indent=4)
    
    console.print(f"Distribution finished and saved to {output_path}")

@app.command()
def info(
        spec_file: Path = typer.Argument(..., help="Path to the distribution specification file"),
):
    """Display information about the distribution."""
    if not spec_file.exists():
        console.print(f"[red]Error:[/] Spec file {spec_file} does not exist.")
        raise typer.Exit(code=1)
    
    with spec_file.open("r") as f:
        import json
        spec_data = json.load(f)
    
    # Display the information
    console.print(Markdown(f"### Information for Distribution: {spec_data.get('name', 'Unknown')}"))
    console.print(Markdown(f"**Description:** {spec_data.get('description', 'No description provided')}"))

@app.command()
def autodo(
        spec_file: Path = typer.Argument(..., help="Path to the distribution specification file"),
        makefile: Path = typer.Argument(..., help="Path to the Makefile for the distribution"),
        typer.Option("--new", "-N", is_flag=True, help="Create a new Makefile if it does not exist."),
        typer.Option("--force", "-F", is_flag=True, help="Force overwrite the existing Makefile."),
        typer.Option("--use-gcc", "-G", is_flag=True, help="Use GCC for building the distribution."),
        typer.Option("--use-asm", "-A", is_flag=True, help="Use an assembler for building the distribution.")
    ):

    """Automatically generate a Makefile for the distribution."""
    if not spec_file.exists():
        console.print(f"[red]Error:[/] Spec file {spec_file} does not exist.")
        raise typer.Exit(code=1)

    if not makefile.exists():
        console.print(f"[red]Error:[/] Makefile {makefile} does not exist.")
        raise typer.Exit(code=1)

    with spec_file.open("r") as f:
        import json
        spec_data = json.load(f)

    if use_asm:
        # ask for assembler name
        asm_name = typer.prompt("Enter the assembler name (default: nasm)", default="nasm")
        asm_flags = typer.prompt("Enter assembler flags (default: -f elf64)", default="-f elf64")
        asm_command = f"{asm_name} {asm_flags} -o $@ $<"

    if use_gcc:
        # ask for gcc flags
        gcc_flags = typer.prompt("Enter GCC flags (default: -m64 -c)", default="-m64 -c")
        gcc_command = f"gcc {gcc_flags} -o $@ $<"

    with makefile.open("w") as f:
        f.write("# Makefile for the distribution\n")
        f.write(f"NAME = {spec_data.get('name', 'unknown')}\n")
        f.write(f"VERSION = {spec_data.get('version', '0.1')}\n")
        f.write(f"DESCRIPTION = {spec_data.get('description', 'No description provided')}\n\n")

        if use_asm:
            f.write("ASM = " + asm_name + "\n")
            f.write("ASMFLAGS = " + asm_flags + "\n")
            f.write("ASM_COMMAND = " + asm_command + "\n\n")

        if use_gcc:
            f.write("GCC = gcc\n")
            f.write("GCCFLAGS = " + gcc_flags + "\n")
            f.write("GCC_COMMAND = " + gcc_command + "\n\n")

        f.write("all:\n")
        if use_asm:
            f.write("\t$(ASM_COMMAND)\n")
        if use_gcc:
            f.write("\t$(GCC_COMMAND)\n")
        f.write("\n")

if __name__ == "__main__":
    app()
