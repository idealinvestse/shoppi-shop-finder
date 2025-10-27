#!/usr/bin/env python3
"""
Example usage of the Advanced Shop Finder programmatically.
This shows how to use the ShopFinder class directly in your own code.
"""

from advanced_finder import ShopFinder, Config

# Example 1: Basic usage with defaults
def basic_example():
    config = Config()
    finder = ShopFinder(config)
    finder.run()

# Example 2: Custom configuration
def custom_example():
    config = Config(
        wordlist_path='custom_shops.txt',
        output_path='custom_results.csv',
        base_url='https://example.com/api/{shop}/products',
        max_concurrent=100,
        rate_limit=0.05,
        log_level='DEBUG'
    )
    finder = ShopFinder(config)
    finder.run()

# Example 3: High-speed scraping
def fast_scraping():
    config = Config(
        max_concurrent=200,
        rate_limit=0.01,
        timeout=15
    )
    finder = ShopFinder(config)
    finder.run()

if __name__ == '__main__':
    # Run the basic example
    basic_example()
