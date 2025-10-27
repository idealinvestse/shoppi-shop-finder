# Quick Start Guide

## Choose Your Version

### 🎨 **Terminal GUI** (Recommended for Beginners)
Interactive interface with menus and live statistics

```bash
python advanced-finder-gui.py
```

**Features:**
- ✅ **Shop Scanner Mode** - Only find working shops (NEW!)
- ✅ Interactive menus - No need to remember commands
- ✅ Live dashboard - See stats in real-time
- ✅ Beautiful interface - Colored output and progress bars
- ✅ Guided setup - Prompts for all settings

### ⚙️ **Command Line** (For Automation)
Traditional CLI with arguments for scripting

```bash
python advanced-finder.py --wordlist words.txt --output results.csv
```

**Features:**
- ✅ Scriptable - Can be automated
- ✅ Resume capability - Continue interrupted scans
- ✅ Detailed logging - File-based logs
- ✅ Full control - All options via flags

---

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Prepare Your Wordlist

Create or use `words.txt` with shop names (one per line):

```
techstore
fashionhub
bookworld
gamezone
```

### Step 3: Run the Tool

**Option A: GUI (Easy)**
```bash
python advanced-finder-gui.py
```

**Option B: CLI (Advanced)**
```bash
python advanced-finder.py
```

**Option C: Windows Batch (Double-click)**
```
run_gui.bat
```

---

## Two Scanning Modes

### 🔍 Shop Scanner Mode (NEW!)

**What it does:** Quickly checks which shops exist

**Output:** Text file with working shop names
```
working_shops.txt:
  techstore
  fashionhub
  electronics
```

**Use when:**
- You want to build a list of active shops
- You need to validate shop names
- You want to filter out non-existent shops before full scraping

**Speed:** Very fast (only HTTP request, no parsing)

---

### 📦 Full Scraper Mode

**What it does:** Gets complete product data from shops

**Output:** CSV file with all products
```csv
shop_name,product_name,price,stock
techstore,Laptop Pro,999.99,15
techstore,USB Cable,9.99,250
```

**Use when:**
- You need product catalogs
- Price monitoring
- Inventory tracking

**Speed:** Slower (parses JSON, extracts all products)

---

## Common Workflows

### Workflow 1: Efficient Two-Pass Scraping

**Goal:** Scrape products only from shops that exist

```
Step 1: Shop Scanner
  Input:  all_shops.txt (500,000 shops)
  Output: working_shops.txt (12,000 shops)
  Time:   ~45 minutes

Step 2: Full Scraper
  Input:  working_shops.txt (12,000 shops)
  Output: products.csv (450,000 products)
  Time:   ~15 minutes
  
Total Time: 60 minutes
Single-Pass Time: 4+ hours ❌
```

**Savings: 75% faster!** ⚡

---

### Workflow 2: Weekly Shop Validation

**Goal:** Keep your shop list up-to-date

```
Monday: Shop Scanner → current_shops.txt
Compare: current_shops.txt vs last_week_shops.txt
New shops: 145 found
Dead shops: 78 removed
```

---

### Workflow 3: API Testing

**Goal:** Test API availability

```
Shop Scanner Mode
Conservative preset (no rate limiting issues)
Small test wordlist (100 shops)
→ Validate API is working
```

---

## Performance Presets

### 🐌 Conservative
- **Speed:** ~25 shops/second
- **Risk:** Very low
- **Use for:** Rate-limited APIs, testing

### ⚡ Balanced (Recommended)
- **Speed:** ~50-100 shops/second
- **Risk:** Low
- **Use for:** Most scenarios

### 🚀 Aggressive
- **Speed:** ~100-200 shops/second
- **Risk:** Medium (possible rate limiting)
- **Use for:** Unlimited APIs, maximum speed

---

## Examples

### Example 1: First Time Use (GUI)

```bash
python advanced-finder-gui.py
```

1. Select "🔍 Shop Scanner"
2. Keep defaults (words.txt → working_shops.txt)
3. Choose "⚡ Balanced" preset
4. Start!

**Result:** `working_shops.txt` with all active shops

---

### Example 2: Full Scrape (CLI)

```bash
python advanced-finder.py \
  --wordlist working_shops.txt \
  --output products.csv \
  --max-concurrent 100
```

**Result:** `products.csv` with all products

---

### Example 3: Custom API (GUI)

```bash
python advanced-finder-gui.py
```

1. Select mode
2. Set URL: `https://api.mysite.com/store/{shop}/items`
3. Aggressive preset
4. Start!

---

## Troubleshooting

### No shops found
- ✅ Check URL template has `{shop}` placeholder
- ✅ Verify wordlist format (one name per line)
- ✅ Test with 2-3 known shop names first

### Too slow
- ✅ Use Shop Scanner mode (10x faster than Full Scraper)
- ✅ Increase concurrency: `--max-concurrent 100`
- ✅ Decrease delay: `--rate-limit 0.05`

### Getting rate limited
- ✅ Use Conservative preset
- ✅ Increase `--rate-limit` to 0.5 or 1.0
- ✅ Decrease `--max-concurrent` to 20 or 10

### GUI not working
```bash
pip install rich questionary --upgrade
```

---

## File Overview

| File | Purpose |
|------|---------|
| `advanced-finder-gui.py` | Terminal GUI version (interactive) |
| `advanced-finder.py` | CLI version (for automation) |
| `requirements.txt` | Python dependencies |
| `words.txt` | Sample wordlist |
| `working_shops.txt` | Output: working shop names |
| `full_catalog.csv` | Output: product data |
| `run_gui.bat` | Windows launcher |

---

## Next Steps

1. **Learn More:**
   - Read `GUI_USAGE.md` for detailed GUI guide
   - Read `README.md` for full documentation

2. **Customize:**
   - Modify URL template for your API
   - Adjust performance settings
   - Create custom wordlists

3. **Automate:**
   - Use CLI version in scripts
   - Schedule regular scans
   - Build data pipelines

---

**Ready to discover shops? Run the GUI and start scanning!** 🚀

```bash
python advanced-finder-gui.py
```
