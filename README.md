# Advanced Shop Product Finder

A powerful, production-ready concurrent shop scraper that discovers products from multiple shops using a wordlist of shop names.

## Features

✨ **High Performance**
- Asynchronous concurrent requests (10-100x faster than sequential)
- Configurable concurrency levels (default: 50 concurrent requests)
- Connection pooling for optimal resource usage

🛡️ **Robust & Reliable**
- Exponential backoff retry logic for failed requests
- Comprehensive error handling and logging
- Rate limiting to avoid IP bans
- Timeout protection

📊 **Progress & Monitoring**
- Real-time progress bar with tqdm
- Detailed statistics (shops checked, products found, error rates)
- Comprehensive logging to file and console
- Error categorization and reporting

💾 **Data Management**
- Incremental CSV writing (safe for large datasets)
- Resume capability (continue from where you left off)
- CSV headers and proper formatting
- Timestamped product discovery

🎛️ **Highly Configurable**
- Command-line arguments for all settings
- Custom URL templates
- Adjustable timeouts, concurrency, and rate limits
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python advanced-finder.py
```

This will:
- Read shop names from `words.txt`
- Scrape products from each shop
- Save results to `full_catalog.csv`

### Advanced Usage

```bash
# Custom wordlist and output
python advanced-finder.py --wordlist shops.txt --output results.csv

# High concurrency for faster scraping
python advanced-finder.py --max-concurrent 100 --rate-limit 0.05

# Resume interrupted scraping
python advanced-finder.py --resume

# Debug mode with detailed logging
python advanced-finder.py --log-level DEBUG

# Custom URL template
python advanced-finder.py --url "https://myshop.com/{shop}/api/products"
```

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--wordlist` | `-w` | Path to wordlist file | `words.txt` |
| `--output` | `-o` | Output CSV file | `full_catalog.csv` |
| `--url` | `-u` | Base URL template with {shop} | `https://shoppi.com/{shop}/products` |
| `--max-concurrent` | `-c` | Max concurrent requests | `50` |
| `--rate-limit` | `-r` | Delay between requests (seconds) | `0.1` |
| `--timeout` | `-t` | Request timeout (seconds) | `30` |
| `--resume` | | Resume from previous run | `False` |
| `--log-level` | | Logging level | `INFO` |

## Input Format

### Wordlist File (`words.txt`)

One shop name per line:
```
techstore
fashionhub
bookworld
gamezone
```

## Output Format

### CSV File (`full_catalog.csv`)

| shop_name | product_name | price | stock | discovered_at |
|-----------|--------------|-------|-------|---------------|
| techstore | Laptop Pro | 999.99 | 15 | 2025-01-27T01:00:00 |
| techstore | USB Cable | 9.99 | 250 | 2025-01-27T01:00:00 |
| fashionhub | Blue Jeans | 49.99 | 30 | 2025-01-27T01:00:01 |

## Performance

### Speed Comparison

- **Original (sequential)**: ~1 shop/second = ~111 hours for 400k shops
- **Enhanced (50 concurrent)**: ~50-100 shops/second = ~1-2 hours for 400k shops
- **Enhanced (100 concurrent)**: ~100-200 shops/second = ~30-60 minutes for 400k shops

### Memory Efficiency

- Original: Stores all data in memory (could use 1GB+ for 400k shops)
- Enhanced: Incremental writing, constant memory usage (~50-100MB)

## Logging

Each run creates a timestamped log file: `shop_finder_YYYYMMDD_HHMMSS.log`

Log levels:
- **DEBUG**: All requests, responses, and detailed errors
- **INFO**: Successful shop discoveries and summary statistics
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

## Error Handling

The scraper handles:
- Network timeouts
- Connection errors
- Invalid JSON responses
- HTTP errors (404, 500, etc.)
- Missing wordlist files
- File I/O errors

All errors are logged and categorized in the final statistics.

## Resume Capability

If interrupted (Ctrl+C or crash), use `--resume` to continue:

```bash
python advanced-finder.py --resume
```

This will:
1. Read existing CSV file
2. Skip already processed shops
3. Continue from where it left off

## Best Practices

1. **Start conservative**: Begin with default settings (50 concurrent, 0.1s rate limit)
2. **Monitor logs**: Check for errors and adjust accordingly
3. **Respect rate limits**: Avoid aggressive settings that might get you blocked
4. **Use resume**: For large wordlists, use `--resume` if interrupted
5. **Test first**: Try with a small wordlist to verify the URL template works

## Troubleshooting

### No products found
- Verify the URL template is correct
- Check log file for HTTP errors
- Try with `--log-level DEBUG` for detailed output

### Too slow
- Increase `--max-concurrent` (try 100 or 200)
- Decrease `--rate-limit` (try 0.05 or 0.01)

### Getting blocked/rate limited
- Decrease `--max-concurrent` (try 20 or 10)
- Increase `--rate-limit` (try 0.5 or 1.0)
- Add delays or use proxies

### Memory issues
- The enhanced version uses minimal memory
- If still issues, reduce `--max-concurrent`

## Example Statistics Output

```
╔══════════════════════════════════════════╗
║         SCRAPING STATISTICS              ║
╠══════════════════════════════════════════╣
║ Shops Checked:                   400,000 ║
║ Shops Found:                      12,453 ║
║ Products Found:                  156,789 ║
║ Elapsed Time:                   3,600.00s ║
║ Rate:                              111.11/s ║
╚══════════════════════════════════════════╝
```

## License

MIT

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs and feature requests.
