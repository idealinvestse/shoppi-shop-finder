#!/usr/bin/env python3
"""
Advanced Shop Product Finder

A powerful, concurrent shop scraper that discovers products from multiple shops
using a wordlist of shop names. Features async requests, rate limiting, error
handling, and comprehensive logging.
"""

import asyncio
import csv
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from tqdm.asyncio import tqdm
import backoff


# Configuration
@dataclass
class Config:
    """Configuration for the shop finder."""
    wordlist_path: str = 'words.txt'
    output_path: str = 'full_catalog.csv'
    base_url: str = 'https://shoppi.com/{shop}/products'
    max_concurrent: int = 50
    rate_limit: float = 0.1  # seconds between requests per worker
    timeout: int = 30
    retries: int = 3
    log_level: str = 'INFO'
    resume: bool = False


@dataclass
class Product:
    """Product data model."""
    shop_name: str
    product_name: str
    price: float
    stock: int
    discovered_at: str


class Stats:
    """Track scraping statistics."""
    def __init__(self):
        self.shops_checked = 0
        self.shops_found = 0
        self.products_found = 0
        self.errors = defaultdict(int)
        self.start_time = datetime.now()

    def summary(self) -> str:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return f"""
╔══════════════════════════════════════════╗
║         SCRAPING STATISTICS              ║
╠══════════════════════════════════════════╣
║ Shops Checked:     {self.shops_checked:>15,} ║
║ Shops Found:       {self.shops_found:>15,} ║
║ Products Found:    {self.products_found:>15,} ║
║ Elapsed Time:      {elapsed:>12.2f}s ║
║ Rate:              {self.shops_checked/max(elapsed,1):>12.2f}/s ║
╚══════════════════════════════════════════╝
"""


class ShopFinder:
    """Main shop finder class with async scraping capabilities."""
    
    def __init__(self, config: Config):
        self.config = config
        self.stats = Stats()
        self.processed_shops: Set[str] = set()
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging with file and console handlers."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=log_format,
            handlers=[
                logging.FileHandler(f'shop_finder_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_wordlist(self) -> List[str]:
        """Load and validate the wordlist file."""
        wordlist_file = Path(self.config.wordlist_path)
        
        if not wordlist_file.exists():
            self.logger.error(f"Wordlist file not found: {self.config.wordlist_path}")
            raise FileNotFoundError(f"Wordlist not found: {self.config.wordlist_path}")
        
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        
        # Remove duplicates while preserving order
        unique_words = list(dict.fromkeys(words))
        self.logger.info(f"Loaded {len(unique_words):,} unique shop names from wordlist")
        return unique_words

    def load_processed_shops(self) -> Set[str]:
        """Load previously processed shops for resume capability."""
        if not self.config.resume:
            return set()
        
        output_file = Path(self.config.output_path)
        if not output_file.exists():
            return set()
        
        processed = set()
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    processed.add(row['shop_name'])
            self.logger.info(f"Resuming: {len(processed):,} shops already processed")
        except Exception as e:
            self.logger.warning(f"Could not load processed shops: {e}")
        
        return processed

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=60
    )
    async def fetch_shop_products(self, session: ClientSession, shop_name: str) -> Optional[List[Product]]:
        """Fetch products from a single shop with retry logic."""
        url = self.config.base_url.format(shop=shop_name)
        
        try:
            async with session.get(url) as response:
                self.stats.shops_checked += 1
                
                if response.status == 200:
                    text = await response.text()
                    
                    if 'products' in text:
                        try:
                            data = json.loads(text)
                            products = data.get('products', [])
                            
                            if products:
                                self.stats.shops_found += 1
                                self.logger.info(f"✓ Found {len(products)} products in '{shop_name}'")
                                
                                product_list = []
                                for p in products:
                                    product = Product(
                                        shop_name=shop_name,
                                        product_name=p.get('name', 'Unknown'),
                                        price=float(p.get('price', 0)),
                                        stock=int(p.get('stock', 0)),
                                        discovered_at=datetime.now().isoformat()
                                    )
                                    product_list.append(product)
                                
                                self.stats.products_found += len(product_list)
                                return product_list
                        except json.JSONDecodeError as e:
                            self.stats.errors['json_decode'] += 1
                            self.logger.debug(f"JSON decode error for {shop_name}: {e}")
                elif response.status == 404:
                    self.logger.debug(f"Shop not found: {shop_name}")
                else:
                    self.stats.errors[f'http_{response.status}'] += 1
                    self.logger.debug(f"HTTP {response.status} for {shop_name}")
                    
        except asyncio.TimeoutError:
            self.stats.errors['timeout'] += 1
            self.logger.debug(f"Timeout for {shop_name}")
        except aiohttp.ClientError as e:
            self.stats.errors['client_error'] += 1
            self.logger.debug(f"Client error for {shop_name}: {e}")
        except Exception as e:
            self.stats.errors['other'] += 1
            self.logger.error(f"Unexpected error for {shop_name}: {e}")
        
        return None

    async def process_shop_batch(self, session: ClientSession, shop_names: List[str], 
                                 csv_writer, pbar) -> None:
        """Process a batch of shops concurrently."""
        tasks = []
        for shop_name in shop_names:
            if shop_name in self.processed_shops:
                pbar.update(1)
                continue
            
            task = self.fetch_shop_products(session, shop_name)
            tasks.append((shop_name, task))
            await asyncio.sleep(self.config.rate_limit)  # Rate limiting
        
        for shop_name, task in tasks:
            products = await task
            if products:
                for product in products:
                    csv_writer.writerow(asdict(product))
            
            self.processed_shops.add(shop_name)
            pbar.update(1)

    async def scrape_all_shops(self, shop_names: List[str]):
        """Main scraping orchestrator with concurrent requests."""
        timeout = ClientTimeout(total=self.config.timeout)
        connector = TCPConnector(limit=self.config.max_concurrent, limit_per_host=10)
        
        # Prepare CSV file
        mode = 'a' if self.config.resume else 'w'
        output_file = Path(self.config.output_path)
        write_header = not (self.config.resume and output_file.exists())
        
        async with ClientSession(timeout=timeout, connector=connector) as session:
            with open(self.config.output_path, mode, newline='', encoding='utf-8') as f:
                fieldnames = ['shop_name', 'product_name', 'price', 'stock', 'discovered_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if write_header:
                    writer.writeheader()
                
                # Filter out already processed shops
                remaining_shops = [s for s in shop_names if s not in self.processed_shops]
                
                with tqdm(total=len(remaining_shops), desc="Scanning shops", 
                         unit="shop", ncols=100) as pbar:
                    # Process in batches for better control
                    batch_size = self.config.max_concurrent
                    for i in range(0, len(remaining_shops), batch_size):
                        batch = remaining_shops[i:i + batch_size]
                        await self.process_shop_batch(session, batch, writer, pbar)
                        f.flush()  # Ensure data is written incrementally

    def run(self):
        """Run the shop finder."""
        self.logger.info("="*50)
        self.logger.info("Starting Advanced Shop Product Finder")
        self.logger.info("="*50)
        
        try:
            # Load wordlist and processed shops
            shop_names = self.load_wordlist()
            self.processed_shops = self.load_processed_shops()
            
            # Run async scraper
            asyncio.run(self.scrape_all_shops(shop_names))
            
            # Print statistics
            print(self.stats.summary())
            self.logger.info(f"Results saved to: {self.config.output_path}")
            
            if self.stats.errors:
                self.logger.info("Errors encountered:")
                for error_type, count in self.stats.errors.items():
                    self.logger.info(f"  {error_type}: {count:,}")
            
        except KeyboardInterrupt:
            self.logger.warning("\nInterrupted by user. Progress saved.")
            print(self.stats.summary())
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Advanced Shop Product Finder - Concurrent shop scraping tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --wordlist shops.txt --output results.csv
  %(prog)s --max-concurrent 100 --rate-limit 0.05
  %(prog)s --resume --log-level DEBUG
        """
    )
    
    parser.add_argument('-w', '--wordlist', default='words.txt',
                       help='Path to wordlist file (default: words.txt)')
    parser.add_argument('-o', '--output', default='full_catalog.csv',
                       help='Output CSV file (default: full_catalog.csv)')
    parser.add_argument('-u', '--url', default='https://shoppi.com/{shop}/products',
                       help='Base URL template with {shop} placeholder')
    parser.add_argument('-c', '--max-concurrent', type=int, default=50,
                       help='Maximum concurrent requests (default: 50)')
    parser.add_argument('-r', '--rate-limit', type=float, default=0.1,
                       help='Delay between requests in seconds (default: 0.1)')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous run')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    config = Config(
        wordlist_path=args.wordlist,
        output_path=args.output,
        base_url=args.url,
        max_concurrent=args.max_concurrent,
        rate_limit=args.rate_limit,
        timeout=args.timeout,
        log_level=args.log_level,
        resume=args.resume
    )
    
    finder = ShopFinder(config)
    finder.run()


if __name__ == '__main__':
    main()

