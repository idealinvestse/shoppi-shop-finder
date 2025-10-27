#!/usr/bin/env python3
"""
Advanced Shop Finder - Terminal GUI Version

Interactive terminal interface for shop discovery with two modes:
1. Shop Scanner - Find working shops and save to file
2. Full Scraper - Scrape products from shops
"""

import asyncio
import csv
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import backoff
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich import box
import questionary
from questionary import Style


console = Console()

# Custom style for questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])


@dataclass
class ScanConfig:
    """Configuration for shop scanning."""
    wordlist_path: str
    output_path: str
    base_url: str
    max_concurrent: int
    rate_limit: float
    timeout: int
    scan_only: bool  # New: only check if shop exists
    working_shops_file: str  # New: file to save working shops


class ShopScanner:
    """Shop scanner with terminal GUI."""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.stats = {
            'checked': 0,
            'working': 0,
            'not_found': 0,
            'errors': 0,
            'products': 0
        }
        self.working_shops: List[str] = []
        self.start_time = datetime.now()
        
    def load_wordlist(self) -> List[str]:
        """Load wordlist file."""
        wordlist_file = Path(self.config.wordlist_path)
        if not wordlist_file.exists():
            console.print(f"[red]❌ Wordlist not found: {self.config.wordlist_path}[/red]")
            raise FileNotFoundError(f"Wordlist not found: {self.config.wordlist_path}")
        
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        
        unique_words = list(dict.fromkeys(words))
        return unique_words

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=2,
        max_time=30
    )
    async def check_shop(self, session: ClientSession, shop_name: str) -> Optional[dict]:
        """Check if a shop exists and optionally get products."""
        url = self.config.base_url.format(shop=shop_name)
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    if 'products' in text:
                        if self.config.scan_only:
                            # Just mark as working, don't parse products
                            return {'shop': shop_name, 'working': True}
                        else:
                            # Full scrape mode
                            try:
                                data = json.loads(text)
                                products = data.get('products', [])
                                return {
                                    'shop': shop_name,
                                    'working': True,
                                    'products': products
                                }
                            except json.JSONDecodeError:
                                return None
                return None
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return None
        except Exception:
            return None

    def create_stats_table(self) -> Table:
        """Create a rich table with current statistics."""
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", justify="right", style="green", width=15)
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.stats['checked'] / max(elapsed, 1)
        
        table.add_row("Shops Checked", f"{self.stats['checked']:,}")
        table.add_row("Working Shops", f"[green]{self.stats['working']:,}[/green]")
        table.add_row("Not Found", f"{self.stats['not_found']:,}")
        table.add_row("Errors", f"[red]{self.stats['errors']:,}[/red]")
        
        if not self.config.scan_only:
            table.add_row("Products Found", f"{self.stats['products']:,}")
        
        table.add_row("Elapsed Time", f"{elapsed:.1f}s")
        table.add_row("Scan Rate", f"{rate:.1f}/s")
        
        return table

    async def scan_shops(self, shop_names: List[str]):
        """Scan shops with progress display."""
        timeout = ClientTimeout(total=self.config.timeout)
        connector = TCPConnector(limit=self.config.max_concurrent, limit_per_host=10)
        
        # Prepare output files
        if self.config.scan_only:
            working_file = open(self.config.working_shops_file, 'w', encoding='utf-8')
        else:
            csv_file = open(self.config.output_path, 'w', newline='', encoding='utf-8')
            fieldnames = ['shop_name', 'product_name', 'price', 'stock']
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            csv_writer.writeheader()
        
        try:
            async with ClientSession(timeout=timeout, connector=connector) as session:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TextColumn("({task.completed}/{task.total})"),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    
                    task = progress.add_task(
                        "[cyan]Scanning shops...",
                        total=len(shop_names)
                    )
                    
                    # Create layout for stats
                    layout = Layout()
                    layout.split_column(
                        Layout(name="header", size=3),
                        Layout(name="stats", size=12),
                        Layout(name="recent", size=8)
                    )
                    
                    recent_finds = []
                    
                    with Live(layout, console=console, refresh_per_second=4):
                        # Process in batches
                        batch_size = self.config.max_concurrent
                        
                        for i in range(0, len(shop_names), batch_size):
                            batch = shop_names[i:i + batch_size]
                            tasks = []
                            
                            for shop_name in batch:
                                task_coro = self.check_shop(session, shop_name)
                                tasks.append((shop_name, task_coro))
                                await asyncio.sleep(self.config.rate_limit)
                            
                            # Wait for batch to complete
                            for shop_name, task_coro in tasks:
                                result = await task_coro
                                self.stats['checked'] += 1
                                
                                if result and result.get('working'):
                                    self.stats['working'] += 1
                                    self.working_shops.append(shop_name)
                                    
                                    if self.config.scan_only:
                                        # Save working shop name
                                        working_file.write(f"{shop_name}\n")
                                        working_file.flush()
                                        recent_finds.append(f"[green]✓[/green] {shop_name}")
                                    else:
                                        # Save products
                                        products = result.get('products', [])
                                        self.stats['products'] += len(products)
                                        for p in products:
                                            csv_writer.writerow({
                                                'shop_name': shop_name,
                                                'product_name': p.get('name', 'Unknown'),
                                                'price': p.get('price', 0),
                                                'stock': p.get('stock', 0)
                                            })
                                        csv_file.flush()
                                        recent_finds.append(
                                            f"[green]✓[/green] {shop_name} ({len(products)} products)"
                                        )
                                else:
                                    if result is None:
                                        self.stats['not_found'] += 1
                                    else:
                                        self.stats['errors'] += 1
                                
                                # Keep only last 5 finds
                                if len(recent_finds) > 5:
                                    recent_finds.pop(0)
                                
                                # Update display
                                mode = "SHOP SCANNER MODE" if self.config.scan_only else "FULL SCRAPE MODE"
                                layout['header'].update(
                                    Panel(
                                        f"[bold cyan]{mode}[/bold cyan]",
                                        style="bold white on blue"
                                    )
                                )
                                layout['stats'].update(Panel(self.create_stats_table(), title="Statistics"))
                                
                                recent_panel = "\n".join(recent_finds) if recent_finds else "[dim]No shops found yet...[/dim]"
                                layout['recent'].update(
                                    Panel(recent_panel, title="Recent Discoveries", border_style="green")
                                )
                                
                                progress.update(task, advance=1)
        
        finally:
            if self.config.scan_only:
                working_file.close()
            else:
                csv_file.close()

    def show_summary(self):
        """Display final summary."""
        console.print()
        console.rule("[bold cyan]Scan Complete![/bold cyan]")
        console.print()
        
        # Summary panel
        summary = Table.grid(padding=1)
        summary.add_column(style="cyan", justify="right")
        summary.add_column(style="green")
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        summary.add_row("Total Shops Checked:", f"{self.stats['checked']:,}")
        summary.add_row("Working Shops Found:", f"[bold green]{self.stats['working']:,}[/bold green]")
        summary.add_row("Success Rate:", f"{(self.stats['working']/max(self.stats['checked'],1)*100):.1f}%")
        
        if not self.config.scan_only:
            summary.add_row("Total Products:", f"{self.stats['products']:,}")
        
        summary.add_row("Time Elapsed:", f"{elapsed:.1f}s")
        summary.add_row("Scan Rate:", f"{self.stats['checked']/max(elapsed,1):.1f} shops/s")
        
        console.print(Panel(summary, title="[bold]Final Results[/bold]", border_style="cyan"))
        
        # Output files
        console.print()
        if self.config.scan_only:
            console.print(f"[green]✓[/green] Working shops saved to: [cyan]{self.config.working_shops_file}[/cyan]")
        else:
            console.print(f"[green]✓[/green] Products saved to: [cyan]{self.config.output_path}[/cyan]")
        console.print()


def show_banner():
    """Display application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║         🔍 ADVANCED SHOP FINDER - GUI MODE 🔍        ║
    ║                                                       ║
    ║         Powerful Shop Discovery & Scraping Tool      ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def get_user_config() -> ScanConfig:
    """Interactive configuration using questionary."""
    console.clear()
    show_banner()
    
    console.print("[bold yellow]Configuration Setup[/bold yellow]\n")
    
    # Mode selection
    mode = questionary.select(
        "Select scanning mode:",
        choices=[
            "🔍 Shop Scanner (Find working shops only)",
            "📦 Full Scraper (Get all products)"
        ],
        style=custom_style
    ).ask()
    
    scan_only = "Scanner" in mode
    
    # Wordlist file
    wordlist = questionary.path(
        "Path to wordlist file:",
        default="words.txt",
        style=custom_style
    ).ask()
    
    # Output configuration
    if scan_only:
        output = questionary.text(
            "File to save working shops:",
            default="working_shops.txt",
            style=custom_style
        ).ask()
        working_shops_file = output
        products_file = "full_catalog.csv"
    else:
        output = questionary.text(
            "File to save products (CSV):",
            default="full_catalog.csv",
            style=custom_style
        ).ask()
        products_file = output
        working_shops_file = "working_shops.txt"
    
    # URL template
    url = questionary.text(
        "Base URL template (use {shop} as placeholder):",
        default="https://shoppi.com/{shop}/products",
        style=custom_style
    ).ask()
    
    # Performance settings
    performance = questionary.select(
        "Performance preset:",
        choices=[
            "🐌 Conservative (25 concurrent, 0.2s delay)",
            "⚡ Balanced (50 concurrent, 0.1s delay)",
            "🚀 Aggressive (100 concurrent, 0.05s delay)",
            "🎯 Custom"
        ],
        style=custom_style
    ).ask()
    
    if "Conservative" in performance:
        max_concurrent, rate_limit = 25, 0.2
    elif "Balanced" in performance:
        max_concurrent, rate_limit = 50, 0.1
    elif "Aggressive" in performance:
        max_concurrent, rate_limit = 100, 0.05
    else:
        max_concurrent = int(questionary.text(
            "Max concurrent requests:",
            default="50",
            style=custom_style
        ).ask())
        rate_limit = float(questionary.text(
            "Rate limit (seconds between requests):",
            default="0.1",
            style=custom_style
        ).ask())
    
    timeout = int(questionary.text(
        "Request timeout (seconds):",
        default="30",
        style=custom_style
    ).ask())
    
    return ScanConfig(
        wordlist_path=wordlist,
        output_path=products_file,
        base_url=url,
        max_concurrent=max_concurrent,
        rate_limit=rate_limit,
        timeout=timeout,
        scan_only=scan_only,
        working_shops_file=working_shops_file
    )


def show_config_summary(config: ScanConfig):
    """Display configuration summary."""
    console.print("\n")
    console.rule("[bold cyan]Configuration Summary[/bold cyan]")
    console.print()
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Mode", "🔍 Shop Scanner" if config.scan_only else "📦 Full Scraper")
    table.add_row("Wordlist", config.wordlist_path)
    table.add_row("Output File", config.working_shops_file if config.scan_only else config.output_path)
    table.add_row("Base URL", config.base_url)
    table.add_row("Max Concurrent", str(config.max_concurrent))
    table.add_row("Rate Limit", f"{config.rate_limit}s")
    table.add_row("Timeout", f"{config.timeout}s")
    
    console.print(table)
    console.print()
    
    proceed = questionary.confirm(
        "Start scanning with these settings?",
        default=True,
        style=custom_style
    ).ask()
    
    return proceed


async def main_async():
    """Main async function."""
    try:
        config = get_user_config()
        
        if not show_config_summary(config):
            console.print("[yellow]Scan cancelled.[/yellow]")
            return
        
        console.clear()
        show_banner()
        
        scanner = ShopScanner(config)
        shop_names = scanner.load_wordlist()
        
        console.print(f"[cyan]Loaded {len(shop_names):,} shops from wordlist[/cyan]\n")
        
        await scanner.scan_shops(shop_names)
        
        scanner.show_summary()
        
        # Ask if user wants to scan again
        again = questionary.confirm(
            "Scan again with different settings?",
            default=False,
            style=custom_style
        ).ask()
        
        if again:
            await main_async()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Scan interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")


def main():
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
