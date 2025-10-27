#!/usr/bin/env python3
"""
Advanced Shop Product Finder - Refactored Version

A robust, concurrent shop scraper with improved architecture:
- Circuit breaker pattern for fault tolerance
- Separate data writer with buffering
- State management for reliable resume
- Enhanced error handling and validation
- Connection pool management
- Thread-safe statistics tracking
"""

import asyncio
import csv
import json
import logging
import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
from enum import Enum

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from tqdm.asyncio import tqdm
import backoff


# Enums and Constants
class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# Configuration
@dataclass
class Config:
    """Configuration for the shop finder with validation."""
    wordlist_path: str = 'words.txt'
    output_path: str = 'full_catalog.csv'
    state_path: str = 'finder_state.json'
    base_url: str = 'https://shoppi.com/{shop}/products'
    max_concurrent: int = 50
    rate_limit: float = 0.1
    timeout: int = 30
    retries: int = 3
    log_level: str = 'INFO'
    resume: bool = False
    
    # Circuit breaker settings
    circuit_failure_threshold: int = 5
    circuit_timeout: int = 60
    
    # Connection pool settings
    connection_pool_size: int = 100
    connection_per_host: int = 10
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if self.rate_limit < 0:
            raise ValueError("rate_limit cannot be negative")
        if self.timeout < 1:
            raise ValueError("timeout must be at least 1 second")
        if '{shop}' not in self.base_url:
            raise ValueError("base_url must contain {shop} placeholder")
        
        # Load from environment variables if available
        self.wordlist_path = os.getenv('SHOPPI_WORDLIST', self.wordlist_path)
        self.output_path = os.getenv('SHOPPI_OUTPUT', self.output_path)
        self.base_url = os.getenv('SHOPPI_BASE_URL', self.base_url)


@dataclass
class Product:
    """Product data model with validation."""
    shop_name: str
    product_name: str
    price: float
    stock: int
    discovered_at: str
    
    def __post_init__(self):
        """Validate product data."""
        if not self.shop_name or not self.shop_name.strip():
            raise ValueError("shop_name cannot be empty")
        if not self.product_name or not self.product_name.strip():
            raise ValueError("product_name cannot be empty")
        if self.price < 0:
            raise ValueError("price cannot be negative")
        if self.stock < 0:
            raise ValueError("stock cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with sanitized values."""
        return {
            'shop_name': self.shop_name.strip(),
            'product_name': self.product_name.strip(),
            'price': round(self.price, 2),
            'stock': self.stock,
            'discovered_at': self.discovered_at
        }


class Stats:
    """Thread-safe scraping statistics tracker."""
    def __init__(self):
        self.shops_checked = 0
        self.shops_found = 0
        self.products_found = 0
        self.errors = defaultdict(int)
        self.start_time = datetime.now()
        self._lock = asyncio.Lock()

    async def increment(self, field: str, value: int = 1):
        """Thread-safe increment of statistics."""
        async with self._lock:
            if field == 'shops_checked':
                self.shops_checked += value
            elif field == 'shops_found':
                self.shops_found += value
            elif field == 'products_found':
                self.products_found += value
    
    async def add_error(self, error_type: str, count: int = 1):
        """Thread-safe error tracking."""
        async with self._lock:
            self.errors[error_type] += count

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


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and (datetime.now() - self.last_failure_time).total_seconds() > self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.failure_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
            raise e
    
    def reset(self):
        """Reset circuit breaker."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None


class DataWriter:
    """Async CSV writer with buffering and error handling."""
    
    def __init__(self, output_path: str, resume: bool = False, buffer_size: int = 100):
        self.output_path = Path(output_path)
        self.resume = resume
        self.buffer_size = buffer_size
        self.buffer: List[Dict[str, Any]] = []
        self.file = None
        self.writer = None
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Open CSV file for writing."""
        mode = 'a' if self.resume and self.output_path.exists() else 'w'
        write_header = not (self.resume and self.output_path.exists())
        
        self.file = open(self.output_path, mode, newline='', encoding='utf-8', buffering=1)
        fieldnames = ['shop_name', 'product_name', 'price', 'stock', 'discovered_at']
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        
        if write_header:
            self.writer.writeheader()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Flush and close file."""
        await self.flush()
        if self.file:
            self.file.close()
    
    async def write(self, product: Product):
        """Write product to buffer."""
        async with self._lock:
            try:
                self.buffer.append(product.to_dict())
                
                if len(self.buffer) >= self.buffer_size:
                    await self._flush_buffer()
            except Exception as e:
                logging.error(f"Error writing product: {e}")
                raise
    
    async def _flush_buffer(self):
        """Internal flush without lock."""
        if self.buffer and self.writer:
            try:
                self.writer.writerows(self.buffer)
                self.file.flush()
                self.buffer.clear()
            except Exception as e:
                logging.error(f"Error flushing buffer: {e}")
                raise
    
    async def flush(self):
        """Force flush buffer to disk."""
        async with self._lock:
            await self._flush_buffer()


class StateManager:
    """Manage scraper state for resume capability."""
    
    def __init__(self, state_path: str):
        self.state_path = Path(state_path)
        self.processed_shops: Set[str] = set()
        self._lock = asyncio.Lock()
    
    async def load(self) -> Set[str]:
        """Load processed shops from state file."""
        if not self.state_path.exists():
            return set()
        
        try:
            async with self._lock:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_shops = set(data.get('processed_shops', []))
                return self.processed_shops
        except Exception as e:
            logging.warning(f"Could not load state file: {e}")
            return set()
    
    async def add_shop(self, shop_name: str):
        """Add shop to processed set."""
        async with self._lock:
            self.processed_shops.add(shop_name)
    
    async def save(self):
        """Save state to disk."""
        async with self._lock:
            try:
                with open(self.state_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'processed_shops': list(self.processed_shops),
                        'last_updated': datetime.now().isoformat()
                    }, f, indent=2)
            except Exception as e:
                logging.error(f"Could not save state file: {e}")


class ProductValidator:
    """Validate and sanitize product data."""
    
    @staticmethod
    def validate_product_data(data: Dict[str, Any]) -> bool:
        """Check if product data is valid."""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['name', 'price', 'stock']
        if not all(field in data for field in required_fields):
            return False
        
        try:
            float(data['price'])
            int(data['stock'])
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def create_product(shop_name: str, product_data: Dict[str, Any]) -> Optional[Product]:
        """Create Product instance with validation."""
        try:
            return Product(
                shop_name=shop_name,
                product_name=str(product_data.get('name', 'Unknown')).strip(),
                price=float(product_data.get('price', 0)),
                stock=int(product_data.get('stock', 0)),
                discovered_at=datetime.now().isoformat()
            )
        except (ValueError, TypeError) as e:
            logging.debug(f"Invalid product data: {e}")
            return None


class ShopFinder:
    """Main shop finder class with improved architecture and reliability."""
    
    def __init__(self, config: Config):
        self.config = config
        self.stats = Stats()
        self.state_manager = StateManager(config.state_path)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            timeout=config.circuit_timeout
        )
        self.validator = ProductValidator()
        self.semaphore = None
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

    async def load_state(self) -> Set[str]:
        """Load previously processed shops for resume capability."""
        if not self.config.resume:
            return set()
        
        processed = await self.state_manager.load()
        if processed:
            self.logger.info(f"Resuming: {len(processed):,} shops already processed")
        return processed

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=60,
        giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404
    )
    async def _fetch_shop_products_internal(self, session: ClientSession, shop_name: str) -> Optional[List[Product]]:
        """Internal fetch method with retry logic."""
        url = self.config.base_url.format(shop=shop_name)
        
        async with session.get(url) as response:
            await self.stats.increment('shops_checked')
            
            if response.status == 200:
                text = await response.text()
                
                if 'products' not in text:
                    return None
                
                try:
                    data = json.loads(text)
                    products_data = data.get('products', [])
                    
                    if not products_data:
                        return None
                    
                    # Validate and create products
                    product_list = []
                    for p in products_data:
                        if not self.validator.validate_product_data(p):
                            continue
                        
                        product = self.validator.create_product(shop_name, p)
                        if product:
                            product_list.append(product)
                    
                    if product_list:
                        await self.stats.increment('shops_found')
                        await self.stats.increment('products_found', len(product_list))
                        self.logger.info(f"✓ Found {len(product_list)} valid products in '{shop_name}'")
                        return product_list
                        
                except json.JSONDecodeError as e:
                    await self.stats.add_error('json_decode')
                    self.logger.debug(f"JSON decode error for {shop_name}: {e}")
                    
            elif response.status == 404:
                self.logger.debug(f"Shop not found: {shop_name}")
            else:
                await self.stats.add_error(f'http_{response.status}')
                self.logger.debug(f"HTTP {response.status} for {shop_name}")
                if response.status >= 500:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
        
        return None
    
    async def fetch_shop_products(self, session: ClientSession, shop_name: str) -> Optional[List[Product]]:
        """Fetch products from a single shop with circuit breaker and retry logic."""
        async with self.semaphore:
            try:
                return await self.circuit_breaker.call(
                    self._fetch_shop_products_internal,
                    session,
                    shop_name
                )
            except asyncio.TimeoutError:
                await self.stats.add_error('timeout')
                self.logger.debug(f"Timeout for {shop_name}")
            except aiohttp.ClientError as e:
                if not (isinstance(e, aiohttp.ClientResponseError) and e.status == 404):
                    await self.stats.add_error('client_error')
                    self.logger.debug(f"Client error for {shop_name}: {e}")
            except Exception as e:
                await self.stats.add_error('other')
                self.logger.error(f"Unexpected error for {shop_name}: {e}")
            
            return None

    async def process_shop(self, session: ClientSession, shop_name: str, 
                          writer: DataWriter, pbar) -> None:
        """Process a single shop."""
        try:
            products = await self.fetch_shop_products(session, shop_name)
            
            if products:
                for product in products:
                    await writer.write(product)
            
            await self.state_manager.add_shop(shop_name)
            
        except Exception as e:
            self.logger.error(f"Failed to process shop {shop_name}: {e}")
        finally:
            pbar.update(1)
            # Rate limiting
            await asyncio.sleep(self.config.rate_limit)

    async def scrape_all_shops(self, shop_names: List[str]):
        """Main scraping orchestrator with concurrent requests."""
        # Initialize semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # Setup connection pool
        timeout = ClientTimeout(total=self.config.timeout, connect=10)
        connector = TCPConnector(
            limit=self.config.connection_pool_size,
            limit_per_host=self.config.connection_per_host,
            ttl_dns_cache=300,
            enable_cleanup_closed=True
        )
        
        # Load processed shops
        processed_shops = await self.load_state()
        remaining_shops = [s for s in shop_names if s not in processed_shops]
        
        if not remaining_shops:
            self.logger.info("All shops already processed.")
            return
        
        self.logger.info(f"Processing {len(remaining_shops):,} shops")
        
        try:
            async with ClientSession(timeout=timeout, connector=connector) as session:
                async with DataWriter(self.config.output_path, self.config.resume) as writer:
                    with tqdm(total=len(remaining_shops), desc="Scanning shops", 
                             unit="shop", ncols=100) as pbar:
                        # Create tasks for all shops
                        tasks = [
                            self.process_shop(session, shop_name, writer, pbar)
                            for shop_name in remaining_shops
                        ]
                        
                        # Process all shops concurrently
                        await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Final flush and save state
                        await writer.flush()
                        await self.state_manager.save()
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}", exc_info=True)
            # Save state even on error
            await self.state_manager.save()
            raise

    def run(self):
        """Run the shop finder."""
        self.logger.info("="*50)
        self.logger.info("Starting Advanced Shop Product Finder (Refactored)")
        self.logger.info("="*50)
        
        try:
            # Load wordlist and processed shops
            shop_names = self.load_wordlist()
            
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
        description='Advanced Shop Product Finder (Refactored) - Robust concurrent shop scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --wordlist shops.txt --output results.csv
  %(prog)s --max-concurrent 100 --rate-limit 0.05
  %(prog)s --resume --log-level DEBUG
  
Environment Variables:
  SHOPPI_WORDLIST  - Wordlist file path
  SHOPPI_OUTPUT    - Output CSV file path
  SHOPPI_BASE_URL  - Base URL template
        """
    )
    
    parser.add_argument('-w', '--wordlist', default='words.txt',
                       help='Path to wordlist file (default: words.txt)')
    parser.add_argument('-o', '--output', default='full_catalog.csv',
                       help='Output CSV file (default: full_catalog.csv)')
    parser.add_argument('-s', '--state', default='finder_state.json',
                       help='State file for resume (default: finder_state.json)')
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
    parser.add_argument('--circuit-threshold', type=int, default=5,
                       help='Circuit breaker failure threshold (default: 5)')
    parser.add_argument('--circuit-timeout', type=int, default=60,
                       help='Circuit breaker timeout in seconds (default: 60)')
    
    args = parser.parse_args()
    
    config = Config(
        wordlist_path=args.wordlist,
        output_path=args.output,
        state_path=args.state,
        base_url=args.url,
        max_concurrent=args.max_concurrent,
        rate_limit=args.rate_limit,
        timeout=args.timeout,
        log_level=args.log_level,
        resume=args.resume,
        circuit_failure_threshold=args.circuit_threshold,
        circuit_timeout=args.circuit_timeout
    )
    
    finder = ShopFinder(config)
    finder.run()


if __name__ == '__main__':
    main()
