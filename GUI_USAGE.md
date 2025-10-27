# Terminal GUI Usage Guide

## Overview

The `advanced-finder-gui.py` provides an interactive terminal interface for shop discovery with two powerful modes:

### 🔍 **Shop Scanner Mode** (NEW!)
- **Purpose**: Find which shops exist without scraping products
- **Output**: A text file with working shop names (one per line)
- **Speed**: Very fast - only checks if shop responds
- **Use Case**: Quick discovery, building shop lists, validation

### 📦 **Full Scraper Mode**
- **Purpose**: Complete product scraping from all shops
- **Output**: CSV file with all products
- **Use Case**: Building product catalogs, price monitoring

## Installation

```bash
pip install -r requirements.txt
```

## Running the GUI

```bash
python advanced-finder-gui.py
```

## Interactive Walkthrough

### 1. Mode Selection

```
Select scanning mode:
❯ 🔍 Shop Scanner (Find working shops only)
  📦 Full Scraper (Get all products)
```

**Shop Scanner**: Only discovers which shops are active
**Full Scraper**: Gets complete product data from shops

### 2. Wordlist Configuration

```
Path to wordlist file: words.txt
```

Enter the path to your file containing shop names (one per line)

### 3. Output File

**For Shop Scanner mode:**
```
File to save working shops: working_shops.txt
```

**For Full Scraper mode:**
```
File to save products (CSV): full_catalog.csv
```

### 4. URL Template

```
Base URL template (use {shop} as placeholder): https://shoppi.com/{shop}/products
```

The `{shop}` placeholder will be replaced with each shop name from your wordlist.

### 5. Performance Preset

```
Performance preset:
  🐌 Conservative (25 concurrent, 0.2s delay)
❯ ⚡ Balanced (50 concurrent, 0.1s delay)
  🚀 Aggressive (100 concurrent, 0.05s delay)
  🎯 Custom
```

- **Conservative**: Safe for rate-limited APIs
- **Balanced**: Good default for most cases
- **Aggressive**: Maximum speed (risk of blocks)
- **Custom**: Fine-tune your own settings

### 6. Review & Start

The tool displays a summary of your configuration:

```
╶─────────────────────────────────────────╴
Mode           🔍 Shop Scanner
Wordlist       words.txt
Output File    working_shops.txt
Base URL       https://shoppi.com/{shop}/products
Max Concurrent 50
Rate Limit     0.1s
Timeout        30s
╶─────────────────────────────────────────╴

Start scanning with these settings? (Y/n)
```

## Live Progress Display

Once scanning starts, you'll see:

```
╔═══════════════════════════════════════════╗
║           SHOP SCANNER MODE               ║
╚═══════════════════════════════════════════╝
┌─────────── Statistics ────────────┐
│ Metric             Value          │
├───────────────────────────────────┤
│ Shops Checked      1,245          │
│ Working Shops      87             │
│ Not Found          1,143          │
│ Errors             15             │
│ Elapsed Time       24.5s          │
│ Scan Rate          50.8/s         │
└───────────────────────────────────┘

┌─────── Recent Discoveries ────────┐
│ ✓ techstore                       │
│ ✓ fashionhub                      │
│ ✓ bookworld                       │
│ ✓ gamezone                        │
│ ✓ electronics                     │
└───────────────────────────────────┘

⠋ Scanning shops... ███████░░░░░░░░░ 45% (453/1000) 0:00:24
```

## Output Files

### Shop Scanner Output (`working_shops.txt`)

Simple text file with working shop names:

```
techstore
fashionhub
bookworld
gamezone
electronics
```

**Perfect for:**
- Building targeted shop lists
- Input for subsequent full scrapes
- API validation
- Shop inventory tracking

### Full Scraper Output (`full_catalog.csv`)

CSV with complete product data:

```csv
shop_name,product_name,price,stock
techstore,Laptop Pro,999.99,15
techstore,USB Cable,9.99,250
fashionhub,Blue Jeans,49.99,30
```

## Final Summary

After completion, you'll see:

```
─────────────────── Scan Complete! ───────────────────

┏━━━━━━━━━━━━━━━━━━━━━ Final Results ━━━━━━━━━━━━━━━━━━━━┓
┃  Total Shops Checked:     400,000                      ┃
┃  Working Shops Found:     12,453                       ┃
┃  Success Rate:            3.1%                         ┃
┃  Time Elapsed:            3,600.0s                     ┃
┃  Scan Rate:               111.1 shops/s                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

✓ Working shops saved to: working_shops.txt

Scan again with different settings? (y/N)
```

## Use Cases

### Use Case 1: Quick Shop Discovery

**Goal**: Find all working shops from a large wordlist

1. Select "Shop Scanner" mode
2. Use aggressive performance preset
3. Output: `working_shops.txt`

**Result**: Fast list of active shops

### Use Case 2: Targeted Product Scraping

**Goal**: Get products only from known working shops

1. First run: Shop Scanner mode → `working_shops.txt`
2. Second run: Full Scraper mode with `working_shops.txt` as input
3. Output: `products.csv`

**Result**: Efficient product collection without wasting time on non-existent shops

### Use Case 3: API Validation

**Goal**: Test which shops in your list are still active

1. Select "Shop Scanner" mode
2. Conservative performance preset (avoid rate limits)
3. Compare output with previous results

**Result**: Updated list of active shops

## Keyboard Controls

- **Ctrl+C**: Stop scanning (progress is saved)
- **Arrow Keys**: Navigate menus
- **Enter**: Confirm selection
- **Y/N**: Answer yes/no questions

## Tips & Best Practices

1. **Start with Shop Scanner**: Always scan for working shops first, then do full scrape
2. **Use Conservative Mode First**: Test with low concurrency to avoid blocks
3. **Save Working Shops**: Use scanner output as input for subsequent scrapes
4. **Monitor Stats**: Watch error rates - high errors may mean rate limiting
5. **Interrupt Safely**: Ctrl+C will save progress gracefully

## Troubleshooting

### GUI doesn't start
```bash
pip install rich questionary --upgrade
```

### Progress bar issues
- Some terminals may not support rich formatting
- Try updating terminal or using Windows Terminal/iTerm2

### No shops found
- Verify URL template is correct
- Check wordlist format (one shop per line)
- Test with a small sample first

## Comparison: CLI vs GUI

| Feature | CLI (`advanced-finder.py`) | GUI (`advanced-finder-gui.py`) |
|---------|---------------------------|-------------------------------|
| Interface | Command-line arguments | Interactive prompts |
| Shop Scanner | ❌ No | ✅ Yes |
| Live Stats | Progress bar only | Full dashboard |
| Resume | ✅ Via `--resume` flag | ❌ Not yet |
| Logging | ✅ Detailed file logs | ❌ Screen only |
| Automation | ✅ Scriptable | ❌ Interactive only |

**Use CLI for**: Scripts, automation, scheduled tasks
**Use GUI for**: Interactive exploration, one-off scans, learning

## Examples

### Example 1: Find Working Shops

```
Mode: 🔍 Shop Scanner
Wordlist: big_list.txt (500,000 shops)
Output: working_shops.txt
Preset: 🚀 Aggressive

Result: Found 15,234 working shops in 45 minutes
```

### Example 2: Scrape Known Shops

```
Mode: 📦 Full Scraper
Wordlist: working_shops.txt (15,234 shops)
Output: all_products.csv
Preset: ⚡ Balanced

Result: 456,789 products in 20 minutes
```

### Example 3: API Testing

```
Mode: 🔍 Shop Scanner
Wordlist: test_shops.txt (100 shops)
Output: active_shops.txt
Preset: 🐌 Conservative

Result: 87 active shops, 13 inactive
```

## Advanced Features

### Custom URL Templates

The GUI supports any URL pattern:

```
https://api.example.com/v1/shops/{shop}/products
https://{shop}.myplatform.com/api/items
https://marketplace.com/seller/{shop}/inventory
```

### Performance Tuning

**High Success Rate (>10%)**: Use aggressive preset
**Low Success Rate (<1%)**: Use conservative to avoid wasted requests
**Rate Limited API**: Increase rate_limit delay

### Multiple Passes

1. **Pass 1**: Shop Scanner → working_shops.txt
2. **Pass 2**: Full Scraper with working_shops.txt → products.csv
3. **Pass 3**: Shop Scanner again (weekly) → updated_shops.txt

This ensures you always have current shop data!

---

**Created with ❤️ for efficient shop discovery**
