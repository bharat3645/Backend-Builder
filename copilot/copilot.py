#!/usr/bin/env python3
"""
Backend Builder Copilot CLI
AI-powered command-line interface for backend development
"""

import click
import requests
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

console = Console()

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
CONFIG_FILE = Path.home() / ".backend-builder" / "config.json"


class BackendBuilderCopilot:
    """Backend Builder Copilot CLI client"""
    
    def __init__(self):
        self.config = self.load_config()
        self.session = requests.Session()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def api_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with error handling"""
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            console.print(f"[red]API Error: {e}[/red]")
            sys.exit(1)
    
    def describe_backend(self, description: str) -> Dict[str, Any]:
        """Convert natural language description to DSL"""
        console.print(f"[blue]Analyzing: {description}[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("Generating DSL specification...", total=None)
            
            response = self.api_request(
                "POST", 
                "/parse-prompt",
                json={"prompt": description}
            )
            
            progress.update(task, description="DSL generated successfully!")
        
        return response.json()
    
    def generate_dsl(self, prompt: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate DSL from prompt and optionally save to file"""
        result = self.describe_backend(prompt)
        dsl = result.get('dsl', {})
        
        if output_file:
            with open(output_file, 'w') as f:
                yaml.dump(dsl, f, default_flow_style=False)
            console.print(f"[green]DSL saved to {output_file}[/green]")
        
        return dsl
    
    def preview_code(self, dsl_file: str, framework: str = "django") -> Dict[str, Any]:
        """Preview generated code structure"""
        with open(dsl_file, 'r') as f:
            dsl = yaml.safe_load(f)

        console.print(f"[blue]Previewing {framework} code structure...[/blue]")

        response = self.api_request(
            "POST",
            "/preview-code",
            json={"dsl": dsl, "framework": framework}
        )

        return response.json()

    def generate_code(self, dsl_file: str, framework: str = "django", output: Optional[str] = None) -> str:
        """Generate a backend project and save it as a zip file. Returns the output path."""
        with open(dsl_file, 'r') as f:
            dsl = yaml.safe_load(f)

        console.print(f"[blue]Generating {framework} project...[/blue]")

        response = self.api_request(
            "POST",
            "/generate-code",
            json={"dsl": dsl, "framework": framework, "format": "zip"}
        )

        project_name = dsl.get('meta', {}).get('name', 'project')
        output_path = output or f"{project_name}-{framework}.zip"
        with open(output_path, 'wb') as f:
            f.write(response.content)

        return output_path

    def deploy_project(self, dsl_file: str, provider: str = "railway") -> Dict[str, Any]:
        """Deploy project to cloud provider"""
        with open(dsl_file, 'r') as f:
            dsl = yaml.safe_load(f)
        
        console.print(f"[blue]Deploying to {provider}...[/blue]")
        
        # Mock deployment process
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("Preparing deployment...", total=None)
            
            # Simulate deployment steps
            import time
            time.sleep(2)
            progress.update(task, description="Building Docker image...")
            time.sleep(2)
            progress.update(task, description="Pushing to registry...")
            time.sleep(2)
            progress.update(task, description="Configuring services...")
            time.sleep(2)
            progress.update(task, description="Deployment complete!")
        
        return {
            "status": "success",
            "url": f"https://{dsl.get('meta', {}).get('name', 'app')}.{provider}.app",
            "provider": provider
        }
    
    def view_logs(self, project_name: str, lines: int = 100) -> list:
        """View deployment logs"""
        console.print(f"[blue]Fetching logs for {project_name} (last {lines} lines)...[/blue]")
        
        # Mock logs
        logs = [
            "2023-12-01 10:30:00 - INFO - Starting Django application",
            "2023-12-01 10:30:01 - INFO - Database connection established",
            "2023-12-01 10:30:02 - INFO - Redis connection established",
            "2023-12-01 10:30:03 - INFO - Server listening on port 8000",
            "2023-12-01 10:30:10 - INFO - GET /api/v1/posts/ - 200",
            "2023-12-01 10:30:15 - INFO - POST /api/v1/auth/login/ - 200",
        ]
        
        return logs[-lines:]
    
    def run_audit(self, dsl_file: str) -> Dict[str, Any]:
        """Run security and performance audit"""
        with open(dsl_file, 'r') as f:
            dsl = yaml.safe_load(f)
        
        console.print("[blue]Running security and performance audit...[/blue]")
        
        # Mock audit results
        audit_results = {
            "security": {
                "score": 85,
                "issues": [
                    {"level": "warning", "message": "Consider enabling rate limiting"},
                    {"level": "info", "message": "HTTPS is properly configured"}
                ]
            },
            "performance": {
                "score": 92,
                "issues": [
                    {"level": "info", "message": "Database indexes are optimized"},
                    {"level": "warning", "message": "Consider enabling query caching"}
                ]
            },
            "best_practices": {
                "score": 88,
                "issues": [
                    {"level": "info", "message": "Models follow Django conventions"},
                    {"level": "warning", "message": "Add API documentation"}
                ]
            }
        }
        
        return audit_results
    
    def simulate_api(self, dsl_file: str, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        """Simulate API endpoint responses"""
        with open(dsl_file, 'r') as f:
            dsl = yaml.safe_load(f)
        
        console.print(f"[blue]Simulating {method} {endpoint}...[/blue]")
        
        # Mock API response
        response = {
            "status": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-RateLimit-Remaining": "999"
            },
            "body": {
                "data": [
                    {"id": 1, "title": "Sample Post", "content": "This is a sample post"},
                    {"id": 2, "title": "Another Post", "content": "Another sample post"}
                ],
                "meta": {
                    "total": 2,
                    "page": 1,
                    "per_page": 20
                }
            }
        }
        
        return response


# CLI Commands
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Backend Builder Copilot - AI-powered backend development CLI"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['copilot'] = BackendBuilderCopilot()


@cli.command(name='describe_backend')
@click.argument('description')
@click.option('--output', '-o', help='Output file for generated DSL')
@click.pass_context
def describe_backend(ctx, description, output):
    """Convert natural language description to DSL specification"""
    copilot = ctx.obj['copilot']
    
    try:
        result = copilot.describe_backend(description)
        dsl = result.get('dsl', {})
        
        if output:
            with open(output, 'w') as f:
                yaml.dump(dsl, f, default_flow_style=False)
            console.print(f"[green]DSL saved to {output}[/green]")
        else:
            # Display DSL in terminal
            syntax = Syntax(yaml.dump(dsl, default_flow_style=False), "yaml", theme="monokai")
            console.print(Panel(syntax, title="Generated DSL", border_style="blue"))
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='preview_code')
@click.argument('dsl_file', type=click.Path(exists=True))
@click.option('--framework', '-f', default='django', help='Target framework')
@click.pass_context
def preview_code(ctx, dsl_file, framework):
    """Preview generated code structure"""
    copilot = ctx.obj['copilot']
    
    try:
        result = copilot.preview_code(dsl_file, framework)
        
        table = Table(title=f"Code Structure - {framework.title()}")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Description", style="green")
        
        for file_info in result.get('preview', {}).get('files', []):
            table.add_row(
                file_info.get('path', ''),
                file_info.get('type', ''),
                file_info.get('description', '')
            )
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='generate_code')
@click.argument('dsl_file', type=click.Path(exists=True))
@click.option('--framework', '-f', default='django', help='Target framework')
@click.option('--output', '-o', help='Output zip file path')
@click.pass_context
def generate_code(ctx, dsl_file, framework, output):
    """Generate a backend project and save it as a zip file"""
    copilot = ctx.obj['copilot']

    try:
        output_path = copilot.generate_code(dsl_file, framework, output)
        console.print(f"[green]Project generated: {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='deploy_project')
@click.argument('dsl_file', type=click.Path(exists=True))
@click.option('--provider', '-p', default='railway', help='Cloud provider')
@click.pass_context
def deploy_project(ctx, dsl_file, provider):
    """Deploy project to cloud provider"""
    copilot = ctx.obj['copilot']
    
    if not Confirm.ask(f"Deploy to {provider}?"):
        console.print("[yellow]Deployment cancelled[/yellow]")
        return
    
    try:
        result = copilot.deploy_project(dsl_file, provider)
        
        if result.get('status') == 'success':
            console.print(Panel(
                f"[green]Deployment successful![/green]\n\n"
                f"URL: {result.get('url')}\n"
                f"Provider: {result.get('provider')}",
                title="Deployment Complete",
                border_style="green"
            ))
        else:
            console.print(f"[red]Deployment failed: {result.get('error', 'Unknown error')}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='view_logs')
@click.argument('project_name')
@click.option('--lines', '-n', default=100, help='Number of log lines to show')
@click.pass_context
def view_logs(ctx, project_name, lines):
    """View deployment logs"""
    copilot = ctx.obj['copilot']
    
    try:
        logs = copilot.view_logs(project_name, lines)
        
        console.print(f"[blue]Logs for {project_name}:[/blue]\n")
        for log in logs:
            console.print(log)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='run_audit')
@click.argument('dsl_file', type=click.Path(exists=True))
@click.pass_context
def run_audit(ctx, dsl_file):
    """Run security and performance audit"""
    copilot = ctx.obj['copilot']
    
    try:
        results = copilot.run_audit(dsl_file)
        
        for category, data in results.items():
            table = Table(title=f"{category.title()} Audit (Score: {data['score']}/100)")
            table.add_column("Level", style="bold")
            table.add_column("Message", style="white")
            
            for issue in data['issues']:
                level_color = {
                    'error': 'red',
                    'warning': 'yellow',
                    'info': 'blue'
                }.get(issue['level'], 'white')
                
                table.add_row(
                    f"[{level_color}]{issue['level'].upper()}[/{level_color}]",
                    issue['message']
                )
            
            console.print(table)
            console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='simulate_api')
@click.argument('dsl_file', type=click.Path(exists=True))
@click.argument('endpoint')
@click.option('--method', '-m', default='GET', help='HTTP method')
@click.pass_context
def simulate_api(ctx, dsl_file, endpoint, method):
    """Simulate API endpoint responses"""
    copilot = ctx.obj['copilot']
    
    try:
        result = copilot.simulate_api(dsl_file, endpoint, method)
        
        console.print(f"[blue]{method} {endpoint}[/blue]")
        console.print(f"Status: {result['status']}")
        console.print("Headers:")
        for key, value in result['headers'].items():
            console.print(f"  {key}: {value}")
        
        console.print("\nResponse Body:")
        syntax = Syntax(json.dumps(result['body'], indent=2), "json", theme="monokai")
        console.print(syntax)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()