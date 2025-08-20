#!/usr/bin/env python3
"""
mhfports - A tool for creating ports for different devices and platforms
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.tree import Tree
from rich import print as rprint
import toml

# Initialize Rich console
console = Console()
app = typer.Typer(help="🚀 mhfports - Multi-platform port creator", rich_markup_mode="rich")

class MHFPortsError(Exception):
    """Base exception for mhfports"""
    pass

class CompilerNotFoundError(MHFPortsError):
    """Raised when specified compiler is not found"""
    pass

class SpecFileError(MHFPortsError):
    """Raised when there's an issue with the spec file"""
    pass

class MHFPorts:
    """Main class for mhfports functionality"""
    
    SUPPORTED_COMPILERS = {
        'gcc': {
            'executables': ['gcc', 'g++'],
            'description': 'GNU Compiler Collection',
            'platforms': ['linux-x86_64', 'linux-arm64', 'linux-armv7']
        },
        'clang': {
            'executables': ['clang', 'clang++'],
            'description': 'LLVM Clang Compiler',
            'platforms': ['linux-x86_64', 'macos-x86_64', 'macos-arm64']
        },
        'msvc': {
            'executables': ['cl.exe'],
            'description': 'Microsoft Visual C++',
            'platforms': ['windows-x86_64', 'windows-x86']
        },
        'mingw': {
            'executables': ['mingw32-gcc', 'x86_64-w64-mingw32-gcc'],
            'description': 'MinGW Windows Compiler',
            'platforms': ['windows-x86_64', 'windows-x86']
        },
        'arm-gcc': {
            'executables': ['arm-none-eabi-gcc', 'aarch64-linux-gnu-gcc'],
            'description': 'ARM Cross Compiler',
            'platforms': ['embedded-arm', 'linux-arm64', 'android-arm64']
        },
        'python': {
            'executables': ['python', 'python3'],
            'description': 'Python Interpreter',
            'platforms': ['linux-x86_64', 'windows-x86_64', 'macos-x86_64', 'macos-arm64']
        },
        'node': {
            'executables': ['node', 'npm'],
            'description': 'Node.js Runtime',
            'platforms': ['linux-x86_64', 'windows-x86_64', 'macos-x86_64', 'web-js']
        },
        'go': {
            'executables': ['go'],
            'description': 'Go Programming Language',
            'platforms': ['linux-x86_64', 'windows-x86_64', 'macos-x86_64', 'web-wasm']
        },
        'rust': {
            'executables': ['rustc', 'cargo'],
            'description': 'Rust Programming Language',
            'platforms': ['linux-x86_64', 'windows-x86_64', 'macos-x86_64', 'web-wasm']
        },
        'zig': {
            'executables': ['zig'],
            'description': 'Zig Programming Language',
            'platforms': ['linux-x86_64', 'windows-x86_64', 'macos-x86_64', 'web-wasm']
        }
    }
    
    SUPPORTED_PLATFORMS = {
        'linux-x86_64': {'arch': 'x86_64', 'os': 'Linux', 'description': 'Linux 64-bit Intel/AMD'},
        'linux-arm64': {'arch': 'arm64', 'os': 'Linux', 'description': 'Linux 64-bit ARM'},
        'linux-armv7': {'arch': 'armv7', 'os': 'Linux', 'description': 'Linux 32-bit ARM'},
        'windows-x86_64': {'arch': 'x86_64', 'os': 'Windows', 'description': 'Windows 64-bit'},
        'windows-x86': {'arch': 'x86', 'os': 'Windows', 'description': 'Windows 32-bit'},
        'macos-x86_64': {'arch': 'x86_64', 'os': 'macOS', 'description': 'macOS Intel 64-bit'},
        'macos-arm64': {'arch': 'arm64', 'os': 'macOS', 'description': 'macOS Apple Silicon'},
        'android-arm64': {'arch': 'arm64', 'os': 'Android', 'description': 'Android 64-bit ARM'},
        'android-armv7': {'arch': 'armv7', 'os': 'Android', 'description': 'Android 32-bit ARM'},
        'ios-arm64': {'arch': 'arm64', 'os': 'iOS', 'description': 'iOS 64-bit ARM'},
        'ios-x86_64': {'arch': 'x86_64', 'os': 'iOS', 'description': 'iOS Simulator'},
        'web-wasm': {'arch': 'wasm', 'os': 'Web', 'description': 'WebAssembly'},
        'web-js': {'arch': 'js', 'os': 'Web', 'description': 'JavaScript'},
        'embedded-arm': {'arch': 'arm', 'os': 'Embedded', 'description': 'Embedded ARM'},
        'embedded-risc-v': {'arch': 'risc-v', 'os': 'Embedded', 'description': 'Embedded RISC-V'}
    }
    
    def __init__(self):
        self.spec_file = None
        self.spec_data = None
        self.project_root = None
    
    def load_spec(self, spec_path: str = "spec.toml") -> None:
        """Load the specification file"""
        spec_file = Path(spec_path)
        
        if not spec_file.exists():
            raise SpecFileError(f"Spec file not found: {spec_path}")
        
        try:
            with open(spec_file, 'r') as f:
                self.spec_data = toml.load(f)
        except toml.TomlDecodeError as e:
            raise SpecFileError(f"Invalid TOML in spec file: {e}")
        
        self.spec_file = spec_file
        self.project_root = spec_file.parent
        
        # Validate required fields
        self._validate_spec()
    
    def _validate_spec(self) -> None:
        """Validate the loaded spec file"""
        required_fields = ['project', 'compiler', 'main_entry']
        
        for field in required_fields:
            if field not in self.spec_data:
                raise SpecFileError(f"Missing required field in spec: {field}")
        
        # Validate compiler
        compiler = self.spec_data['compiler']
        if isinstance(compiler, dict):
            compiler_type = compiler.get('type')
        else:
            compiler_type = compiler
        
        if compiler_type not in self.SUPPORTED_COMPILERS:
            console.print(f"[yellow]Warning:[/yellow] Compiler '{compiler_type}' not in supported list, but will attempt to use it")
        
        # Validate main entry file exists
        main_entry = Path(self.project_root) / self.spec_data['main_entry']
        if not main_entry.exists():
            raise SpecFileError(f"Main entry file not found: {main_entry}")
    
    def _check_compiler_availability(self, compiler_info: Dict[str, Any]) -> str:
        """Check if the specified compiler is available"""
        if isinstance(compiler_info, str):
            compiler_type = compiler_info
            compiler_path = None
        else:
            compiler_type = compiler_info.get('type')
            compiler_path = compiler_info.get('path')
        
        # If specific path is provided, check that
        if compiler_path:
            if shutil.which(compiler_path):
                return compiler_path
            else:
                raise CompilerNotFoundError(f"Compiler not found at specified path: {compiler_path}")
        
        # Check standard compiler names
        if compiler_type in self.SUPPORTED_COMPILERS:
            for compiler_name in self.SUPPORTED_COMPILERS[compiler_type]['executables']:
                if shutil.which(compiler_name):
                    return compiler_name
        
        # Fallback: try the compiler type directly
        if shutil.which(compiler_type):
            return compiler_type
        
        raise CompilerNotFoundError(f"No available compiler found for type: {compiler_type}")
    
    def _get_output_path(self, platform: str) -> Path:
        """Generate output path for the given platform"""
        project_name = self.spec_data['project']['name']
        version = self.spec_data['project'].get('version', '1.0.0')
        
        output_dir = Path(self.project_root) / 'dist' / f"{project_name}-{version}-{platform}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    def _compile_native(self, platform: str, compiler_path: str) -> Path:
        """Compile for native platforms using C/C++ compilers"""
        output_dir = self._get_output_path(platform)
        main_entry = Path(self.project_root) / self.spec_data['main_entry']
        
        # Determine output executable name
        project_name = self.spec_data['project']['name']
        if platform.startswith('windows'):
            executable_name = f"{project_name}.exe"
        else:
            executable_name = project_name
        
        output_file = output_dir / executable_name
        
        # Build compile command
        compile_cmd = [compiler_path]
        
        # Add compiler flags from spec
        compiler_info = self.spec_data['compiler']
        if isinstance(compiler_info, dict):
            flags = compiler_info.get('flags', [])
            if isinstance(flags, str):
                compile_cmd.extend(flags.split())
            else:
                compile_cmd.extend(flags)
        
        # Add source files
        compile_cmd.append(str(main_entry))
        
        # Add additional source files if specified
        sources = self.spec_data.get('sources', [])
        for source in sources:
            source_path = Path(self.project_root) / source
            if source_path.exists():
                compile_cmd.append(str(source_path))
        
        # Add output specification
        compile_cmd.extend(['-o', str(output_file)])
        
        try:
            result = subprocess.run(compile_cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  cwd=self.project_root)
            
            if result.returncode != 0:
                raise MHFPortsError(f"Compilation failed:\n{result.stderr}")
            
            return output_file
            
        except subprocess.SubprocessError as e:
            raise MHFPortsError(f"Failed to run compiler: {e}")
    
    def _compile_python(self, platform: str) -> Path:
        """Handle Python-based projects"""
        output_dir = self._get_output_path(platform)
        main_entry = Path(self.project_root) / self.spec_data['main_entry']
        
        # Copy Python files to output directory
        shutil.copy2(main_entry, output_dir)
        
        # Copy additional source files
        sources = self.spec_data.get('sources', [])
        for source in sources:
            source_path = Path(self.project_root) / source
            if source_path.exists():
                if source_path.is_file():
                    shutil.copy2(source_path, output_dir)
                else:
                    shutil.copytree(source_path, output_dir / source_path.name, dirs_exist_ok=True)
        
        # Copy requirements.txt if it exists
        requirements = Path(self.project_root) / 'requirements.txt'
        if requirements.exists():
            shutil.copy2(requirements, output_dir)
        
        return output_dir / main_entry.name
    
    def build(self, platforms: List[str]) -> Dict[str, Path]:
        """Build the project for specified platforms"""
        if not self.spec_data:
            raise MHFPortsError("No spec file loaded. Call load_spec() first.")
        
        results = {}
        compiler_info = self.spec_data['compiler']
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for platform in platforms:
                if platform not in self.SUPPORTED_PLATFORMS:
                    console.print(f"[yellow]Warning:[/yellow] Platform '{platform}' not in supported list, but will attempt to build")
                
                task = progress.add_task(f"Building for {platform}...", total=None)
                
                try:
                    # Handle different compiler types
                    if isinstance(compiler_info, dict):
                        compiler_type = compiler_info.get('type')
                    else:
                        compiler_type = compiler_info
                    
                    if compiler_type == 'python':
                        output_file = self._compile_python(platform)
                    else:
                        # Native compilation
                        compiler_path = self._check_compiler_availability(compiler_info)
                        output_file = self._compile_native(platform, compiler_path)
                    
                    results[platform] = output_file
                    progress.update(task, description=f"✅ Built for {platform}")
                    
                except (CompilerNotFoundError, MHFPortsError) as e:
                    progress.update(task, description=f"❌ Failed to build for {platform}")
                    console.print(f"[red]Error building {platform}:[/red] {e}")
                    continue
                
                progress.remove_task(task)
        
        return results

# CLI Commands
@app.command()
def build(
    platforms: Optional[List[str]] = typer.Argument(None, help="Target platforms to build for"),
    spec: str = typer.Option("spec.toml", "--spec", "-s", help="Path to spec file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """
    🔨 Build project for specified platforms
    """
    if verbose:
        console.print("[dim]Loading spec file...[/dim]")
    
    mhf = MHFPorts()
    
    try:
        mhf.load_spec(spec)
        
        # Show project info
        project_info = mhf.spec_data['project']
        panel = Panel(
            f"[bold]{project_info['name']}[/bold] v{project_info.get('version', '1.0.0')}\n"
            f"{project_info.get('description', 'No description')}\n"
            f"[dim]Author: {project_info.get('author', 'Unknown')}[/dim]",
            title="📦 Project Info",
            border_style="blue"
        )
        console.print(panel)
        
        # Determine platforms to build
        if platforms:
            build_platforms = platforms
        else:
            build_platforms = mhf.spec_data.get('build', {}).get('platforms', ['linux-x86_64'])
        
        console.print(f"\n🎯 Building for platforms: {', '.join(build_platforms)}")
        
        results = mhf.build(build_platforms)
        
        if results:
            console.print("\n✨ [bold green]Build completed successfully![/bold green]")
            
            # Create results table
            table = Table(title="📁 Build Results")
            table.add_column("Platform", style="cyan")
            table.add_column("Output File", style="green")
            table.add_column("Status", justify="center")
            
            for platform, output_file in results.items():
                table.add_row(platform, str(output_file), "✅")
            
            console.print(table)
        else:
            console.print("[bold red]❌ All builds failed![/bold red]")
            raise typer.Exit(1)
    
    except (MHFPortsError, FileNotFoundError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def list_targets(
    platforms: bool = typer.Option(False, "--platforms", "-p", help="List supported platforms"),
    compilers: bool = typer.Option(False, "--compilers", "-c", help="List supported compilers")
):
    """
    📋 List supported platforms and compilers
    """
    mhf = MHFPorts()
    
    if platforms or (not platforms and not compilers):
        # Create platforms table
        platforms_table = Table(title="🖥️  Supported Platforms")
        platforms_table.add_column("Platform", style="cyan")
        platforms_table.add_column("OS", style="green")
        platforms_table.add_column("Architecture", style="yellow")
        platforms_table.add_column("Description", style="dim")
        
        for platform, info in mhf.SUPPORTED_PLATFORMS.items():
            platforms_table.add_row(
                platform,
                info['os'],
                info['arch'],
                info['description']
            )
        
        console.print(platforms_table)
    
    if compilers or (not platforms and not compilers):
        if platforms:
            console.print()  # Add spacing
        
        # Create compilers table
        compilers_table = Table(title="🔧 Supported Compilers")
        compilers_table.add_column("Compiler", style="cyan")
        compilers_table.add_column("Description", style="green")
        compilers_table.add_column("Executables", style="yellow")
        compilers_table.add_column("Supported Platforms", style="dim")
        
        for compiler, info in mhf.SUPPORTED_COMPILERS.items():
            compilers_table.add_row(
                compiler,
                info['description'],
                ", ".join(info['executables']),
                ", ".join(info['platforms'][:3]) + ("..." if len(info['platforms']) > 3 else "")
            )
        
        console.print(compilers_table)

@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    compiler: str = typer.Option("gcc", "--compiler", "-c", help="Compiler type"),
    language: str = typer.Option("c", "--language", "-l", help="Programming language (c, cpp, python, go, rust)")
):
    """
    🚀 Initialize a new project
    """
    mhf = MHFPorts()
    
    project_dir = Path(name)
    if project_dir.exists():
        overwrite = typer.confirm(f"Directory '{name}' already exists. Overwrite?")
        if not overwrite:
            console.print("❌ Operation cancelled")
            raise typer.Exit(1)
        shutil.rmtree(project_dir)
    
    project_dir.mkdir(exist_ok=True)
    
    console.print(f"🎨 Creating project '[bold cyan]{name}[/bold cyan]' with [bold yellow]{compiler}[/bold yellow] compiler...")
    
    # Create spec.toml based on language
    spec_content = _generate_spec_content(name, compiler, language)
    
    with open(project_dir / 'spec.toml', 'w') as f:
        f.write(spec_content)
    
    # Create source files based on language
    _create_source_files(project_dir, name, language)
    
    # Show project structure
    tree = Tree(f"📁 [bold blue]{name}[/bold blue]")
    _add_tree_items(tree, project_dir)
    console.print(tree)
    
    # Show next steps
    next_steps = f"""
## Next Steps

1. **Navigate to your project:**
   ```bash
   cd {name}
   ```

2. **Build your project:**
   ```bash
   mhfports build
   ```

3. **List available platforms:**
   ```bash
   mhfports list-targets --platforms
   ```

4. **Build for specific platforms:**
   ```bash
   mhfports build linux-x86_64 windows-x86_64
   ```
"""
    
    markdown = Markdown(next_steps)
    console.print(Panel(markdown, title="🎯 Getting Started", border_style="green"))
    
    console.print(f"✨ [bold green]Project '{name}' created successfully![/bold green]")

def _generate_spec_content(name: str, compiler: str, language: str) -> str:
    """Generate spec.toml content based on language"""
    base_spec = f'''[project]
name = "{name}"
version = "1.0.0"
description = "A port created with mhfports"
author = "Your Name"

[compiler]
type = "{compiler}"
'''
    
    if language in ['c', 'cpp']:
        return base_spec + f'''flags = ["-O2", "-Wall", "-std=c99"]

main_entry = "src/main.{language}"

sources = [
    "src/utils.{language}"
]

[build]
platforms = ["linux-x86_64", "windows-x86_64", "macos-x86_64"]

[dependencies]
# Add your dependencies here
'''
    elif language == 'python':
        return base_spec + f'''

main_entry = "src/main.py"

sources = [
    "src/utils.py"
]

[build]
platforms = ["linux-x86_64", "windows-x86_64", "macos-x86_64"]

[dependencies]
# List your Python packages in requirements.txt
'''
    else:
        return base_spec + f'''

main_entry = "src/main.{language}"

[build]
platforms = ["linux-x86_64", "windows-x86_64", "macos-x86_64"]
'''

def _create_source_files(project_dir: Path, name: str, language: str):
    """Create source files based on language"""
    src_dir = project_dir / 'src'
    src_dir.mkdir(exist_ok=True)
    
    if language == 'c':
        _create_c_files(src_dir, name)
    elif language == 'cpp':
        _create_cpp_files(src_dir, name)
    elif language == 'python':
        _create_python_files(src_dir, name)
    elif language == 'go':
        _create_go_files(src_dir, name)
    elif language == 'rust':
        _create_rust_files(src_dir, name)

def _create_c_files(src_dir: Path, name: str):
    """Create C source files"""
    main_content = f'''#include <stdio.h>
#include "utils.h"

int main() {{
    printf("Hello from {name}!\\n");
    print_version();
    return 0;
}}
'''
    
    utils_content = '''#include <stdio.h>
#include "utils.h"

void print_version() {
    printf("Version 1.0.0\\n");
}
'''
    
    utils_header = '''#ifndef UTILS_H
#define UTILS_H

void print_version();

#endif
'''
    
    with open(src_dir / 'main.c', 'w') as f:
        f.write(main_content)
    
    with open(src_dir / 'utils.c', 'w') as f:
        f.write(utils_content)
    
    with open(src_dir / 'utils.h', 'w') as f:
        f.write(utils_header)

def _create_cpp_files(src_dir: Path, name: str):
    """Create C++ source files"""
    main_content = f'''#include <iostream>
#include "utils.hpp"

int main() {{
    std::cout << "Hello from {name}!" << std::endl;
    print_version();
    return 0;
}}
'''
    
    utils_content = '''#include <iostream>
#include "utils.hpp"

void print_version() {
    std::cout << "Version 1.0.0" << std::endl;
}
'''
    
    utils_header = '''#ifndef UTILS_HPP
#define UTILS_HPP

void print_version();

#endif
'''
    
    with open(src_dir / 'main.cpp', 'w') as f:
        f.write(main_content)
    
    with open(src_dir / 'utils.cpp', 'w') as f:
        f.write(utils_content)
    
    with open(src_dir / 'utils.hpp', 'w') as f:
        f.write(utils_header)

def _create_python_files(src_dir: Path, name: str):
    """Create Python source files"""
    main_content = f'''#!/usr/bin/env python3
"""
{name} - A project created with mhfports
"""

from utils import print_version

def main():
    print(f"Hello from {name}!")
    print_version()

if __name__ == "__main__":
    main()
'''
    
    utils_content = '''"""Utility functions"""

def print_version():
    print("Version 1.0.0")
'''
    
    with open(src_dir / 'main.py', 'w') as f:
        f.write(main_content)
    
    with open(src_dir / 'utils.py', 'w') as f:
        f.write(utils_content)
    
    # Create requirements.txt
    with open(src_dir.parent / 'requirements.txt', 'w') as f:
        f.write("# Add your Python dependencies here\n")

def _create_go_files(src_dir: Path, name: str):
    """Create Go source files"""
    main_content = f'''package main

import (
    "fmt"
)

func main() {{
    fmt.Println("Hello from {name}!")
    printVersion()
}}

func printVersion() {{
    fmt.Println("Version 1.0.0")
}}
'''
    
    with open(src_dir / 'main.go', 'w') as f:
        f.write(main_content)

def _create_rust_files(src_dir: Path, name: str):
    """Create Rust source files"""
    main_content = f'''fn main() {{
    println!("Hello from {name}!");
    print_version();
}}

fn print_version() {{
    println!("Version 1.0.0");
}}
'''
    
    with open(src_dir / 'main.rs', 'w') as f:
        f.write(main_content)

def _add_tree_items(tree: Tree, path: Path):
    """Recursively add items to Rich tree"""
    for item in sorted(path.iterdir()):
        if item.is_file():
            if item.suffix in ['.toml', '.txt']:
                tree.add(f"📄 [green]{item.name}[/green]")
            elif item.suffix in ['.c', '.cpp', '.h', '.hpp', '.py', '.go', '.rs']:
                tree.add(f"📝 [blue]{item.name}[/blue]")
            else:
                tree.add(f"📄 {item.name}")
        elif item.is_dir() and not item.name.startswith('.'):
            subtree = tree.add(f"📁 [bold]{item.name}[/bold]")
            _add_tree_items(subtree, item)

@app.command()
def version():
    """
    📋 Show version information
    """
    version_info = """
# mhfports v1.0.0

**🚀 Multi-platform port creator**

A powerful tool for creating and building software ports across different devices and platforms.

**Features:**
- 🔧 Multiple compiler support (GCC, Clang, MSVC, etc.)
- 🖥️  Cross-platform building (Linux, Windows, macOS, mobile, embedded)
- 📝 TOML-based configuration
- 🎨 Beautiful CLI with Rich output
- 🚀 Easy project initialization

**Author:** mhfports team  
**License:** MIT
"""
    
    markdown = Markdown(version_info)
    console.print(Panel(markdown, title="📦 mhfports", border_style="cyan"))

if __name__ == "__main__":
    app()
