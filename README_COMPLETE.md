# Shop Product Finder - Komplett Guide

## Översikt

Ett komplett system för att skrapa, analysera och presentera produkter från flera shops.

### Komponenter

1. **advanced-finder-refactored.py** - Scraper (samlar produktdata)
2. **catalog_viewer.py** - Viewer (söker och presenterar data)
3. **test_advanced_finder.py** - Test suite (41 unit tests)

## Workflow

```
[Wordlist] → [Scraper] → [CSV/JSON] → [Viewer] → [HTML/Reports]
```

## Snabbstart

### Steg 1: Skrapa Produkter

```bash
# Grundläggande scraping
python advanced-finder-refactored.py --wordlist words.txt --output products.csv

# Med högre concurrency
python advanced-finder-refactored.py \
    --wordlist words.txt \
    --output products.csv \
    --max-concurrent 100 \
    --rate-limit 0.05

# Med resume (fortsätt avbrutna körningar)
python advanced-finder-refactored.py \
    --wordlist words.txt \
    --output products.csv \
    --resume
```

### Steg 2: Sök och Analysera

```bash
# Visa statistik
python catalog_viewer.py products.csv --stats

# Sök produkter
python catalog_viewer.py products.csv --search "laptop"

# Filtrera och sortera
python catalog_viewer.py products.csv \
    --min-price 100 \
    --max-price 500 \
    --sort price \
    --compact
```

### Steg 3: Exportera Resultat

```bash
# HTML-katalog
python catalog_viewer.py products.csv \
    --export catalog.html \
    --format html

# JSON för API
python catalog_viewer.py products.csv \
    --export products.json \
    --format json
```

## Funktioner

### Scraper (advanced-finder-refactored.py)

#### Arkitektur
- ✅ **Circuit Breaker** - Fault tolerance
- ✅ **DataWriter** - Buffrad I/O
- ✅ **StateManager** - Robust resume
- ✅ **ProductValidator** - Data validation
- ✅ **Thread-safe** - Async operations

#### Användning
```bash
# Minimal
python advanced-finder-refactored.py

# Production
python advanced-finder-refactored.py \
    --wordlist production_shops.txt \
    --output full_catalog.csv \
    --max-concurrent 100 \
    --rate-limit 0.02 \
    --circuit-threshold 15 \
    --resume

# Med miljövariabler
export SHOPPI_WORDLIST="shops.txt"
export SHOPPI_OUTPUT="catalog.csv"
python advanced-finder-refactored.py
```

### Viewer (catalog_viewer.py)

#### Funktioner
- ✅ **Full-text search** - Sök i alla fält
- ✅ **Filtrera** - Shop, pris, stock
- ✅ **Sortera** - Efter pris, stock, namn
- ✅ **Statistik** - Analytics och insights
- ✅ **Export** - CSV, JSON, HTML

#### Användning
```bash
# Statistik
python catalog_viewer.py products.csv --stats

# Sök
python catalog_viewer.py products.csv --search "phone" --compact

# Filtrera
python catalog_viewer.py products.csv \
    --shop "TechStore" \
    --min-price 500 \
    --max-price 2000 \
    --min-stock 5

# Export HTML
python catalog_viewer.py products.csv \
    --search "laptop" \
    --export laptops.html \
    --format html
```

## Användningsfall

### 1. E-handel - Produktanalys

```bash
# Skrapa konkurrenters produkter
python advanced-finder-refactored.py \
    --wordlist competitors.txt \
    --output competitors_catalog.csv

# Hitta prisgap
python catalog_viewer.py competitors_catalog.csv \
    --search "smartphone" \
    --sort price \
    --export price_comparison.html \
    --format html
```

### 2. Inventering

```bash
# Skrapa alla shops
python advanced-finder-refactored.py \
    --wordlist all_shops.txt \
    --output inventory.csv \
    --resume

# Hitta låg stock
python catalog_viewer.py inventory.csv \
    --max-stock 5 \
    --export low_stock_alert.csv
```

### 3. Prisbevakning

```bash
# Skrapa dagligen
python advanced-finder-refactored.py \
    --wordlist shops.txt \
    --output "prices_$(date +%Y%m%d).csv"

# Jämför priser
python catalog_viewer.py prices_20240127.csv \
    --search "iPhone" \
    --sort price \
    --compact
```

### 4. Produktkatalog för Webshop

```bash
# Skrapa leverantörer
python advanced-finder-refactored.py \
    --wordlist suppliers.txt \
    --output supplier_catalog.csv

# Generera HTML-katalog
python catalog_viewer.py supplier_catalog.csv \
    --export webshop_catalog.html \
    --format html

# Servera online
python -m http.server 8000
```

## Avancerad Användning

### Automatisk Rapport

```bash
#!/bin/bash
# daily_report.sh

# Skrapa ny data
python advanced-finder-refactored.py \
    --wordlist shops.txt \
    --output daily_catalog.csv \
    --resume

# Generera rapporter
python catalog_viewer.py daily_catalog.csv --stats

# Låg stock alert
python catalog_viewer.py daily_catalog.csv \
    --max-stock 10 \
    --export "low_stock_$(date +%Y%m%d).html" \
    --format html

# Ny produkter (filtrera efter discovered_at)
python catalog_viewer.py daily_catalog.csv \
    --export "new_products_$(date +%Y%m%d).json" \
    --format json
```

### Multi-Shop Analys

```python
from catalog_viewer import CatalogViewer

# Ladda katalog
viewer = CatalogViewer('full_catalog.csv')

# Jämför priser mellan shops
product = "iPhone 15"
results = viewer.search(query=product, sort_by='price')

print(f"Price comparison for: {product}")
for r in results:
    print(f"{r.shop_name}: {r.price} kr (stock: {r.stock})")

# Top produkter per shop
stats = viewer.get_statistics()
for shop, count in stats['top_shops']:
    print(f"{shop}: {count} products")
```

### Integration med Database

```bash
# Exportera till JSON
python catalog_viewer.py products.csv \
    --export products.json \
    --format json

# Import till MongoDB
mongoimport --db shop \
    --collection products \
    --file products.json \
    --jsonArray

# Import till PostgreSQL (via Python)
python << EOF
import json
import psycopg2

with open('products.json') as f:
    data = json.load(f)

conn = psycopg2.connect("dbname=shop")
cur = conn.cursor()

for product in data:
    cur.execute(
        "INSERT INTO products (shop, name, price, stock) VALUES (%s, %s, %s, %s)",
        (product['shop'], product['product'], product['price'], product['stock'])
    )

conn.commit()
EOF
```

## Data Format

### CSV Output (från scraper)
```csv
shop_name,product_name,price,stock,discovered_at
TechStore,Laptop Pro 15,8999.00,15,2024-01-27T10:30:00
GamerShop,Gaming Mouse,399.00,50,2024-01-27T10:31:00
```

### JSON Output (från viewer)
```json
[
  {
    "shop": "TechStore",
    "product": "Laptop Pro 15",
    "price": 8999.0,
    "stock": 15,
    "discovered": "2024-01-27T10:30:00"
  }
]
```

### HTML Output (från viewer)
- Responsiv tabell
- Sökfunktion (real-time)
- Sorteringsbar kolumner
- Färgkodad stock status

## Prestanda

### Scraper
- **Concurrency**: 50-150 shops samtidigt
- **Rate Limiting**: 0.02-0.1s mellan requests
- **Circuit Breaker**: Automatisk recovery vid fel
- **Resume**: Fortsätt från senaste state

### Viewer
- **Laddar**: 10,000+ produkter på < 1s
- **Sökning**: Real-time på stora kataloger
- **Export HTML**: < 1s för 1,000 produkter

## Felsökning

### Scraper Problem

**Circuit Breaker Öppen**
```bash
# Öka tröskelvärde
--circuit-threshold 20 --circuit-timeout 120
```

**För Långsam**
```bash
# Öka concurrency, minska rate limit
--max-concurrent 150 --rate-limit 0.01
```

**Memory Issues**
```bash
# Minska concurrency
--max-concurrent 25
```

### Viewer Problem

**Inga Resultat**
```bash
# Bredare sökning
python catalog_viewer.py products.csv --search "lap"
```

**Fel Format**
```bash
# Kontrollera CSV headers
head -1 products.csv
```

## Testing

```bash
# Kör alla tester
python -m pytest test_advanced_finder.py -v

# Specifik testklass
python -m pytest test_advanced_finder.py::TestCircuitBreaker -v

# Med coverage
python -m pytest test_advanced_finder.py --cov
```

## Dokumentation

- **REFACTORING_GUIDE.md** - Teknisk deep-dive
- **README_REFACTORED.md** - Scraper guide
- **CATALOG_VIEWER_GUIDE.md** - Viewer guide
- **TEST_REPORT.md** - Test resultat
- **SUMMARY.md** - Översikt

## Best Practices

### 1. Respektera Server Limits
```bash
# Använd rimlig rate limiting
--rate-limit 0.1

# Övervaka HTTP 429 errors
tail -f shop_finder_*.log | grep "429"
```

### 2. Backup & State Management
```bash
# Backup state regelbundet
cp finder_state.json finder_state.backup.json

# Backup catalog
cp full_catalog.csv full_catalog.backup.csv
```

### 3. Monitoring
```bash
# Övervaka scraper
tail -f shop_finder_*.log

# Kontrollera circuit breaker
grep "Circuit breaker" shop_finder_*.log

# Räkna fel
grep "ERROR" shop_finder_*.log | wc -l
```

### 4. Data Quality
```bash
# Validera CSV
python -c "import csv; list(csv.DictReader(open('products.csv')))"

# Kontrollera duplicates
sort products.csv | uniq -d

# Räkna produkter
wc -l products.csv
```

## Exempel Workflow

### Komplett E-handels Setup

```bash
# 1. Initial scrape
python advanced-finder-refactored.py \
    --wordlist all_suppliers.txt \
    --output master_catalog.csv \
    --max-concurrent 100

# 2. Generera HTML-katalog
python catalog_viewer.py master_catalog.csv \
    --export web_catalog.html \
    --format html

# 3. Filtrera per kategori
python catalog_viewer.py master_catalog.csv \
    --search "laptop" \
    --export laptops.html \
    --format html

python catalog_viewer.py master_catalog.csv \
    --search "phone" \
    --export phones.html \
    --format html

# 4. Prisanalys
python catalog_viewer.py master_catalog.csv \
    --stats > stats_report.txt

# 5. Låg stock alert
python catalog_viewer.py master_catalog.csv \
    --max-stock 5 \
    --export low_stock.csv

# 6. Daglig uppdatering (cron)
# 0 6 * * * /path/to/update_catalog.sh
```

## Sammanfattning

**Shop Product Finder** är ett komplett system för:

✅ **Skrapa** produktdata från flera shops  
✅ **Validera** och sanitera all data  
✅ **Lagra** i CSV/JSON format  
✅ **Söka** och filtrera produkter  
✅ **Analysera** med statistik  
✅ **Presentera** i HTML-format  
✅ **Exportera** till olika format  
✅ **Integrera** med andra system  

**Production-ready** med:
- Circuit breaker för fault tolerance
- Thread-safe operations
- Robust error handling
- Resume capability
- Comprehensive testing

## Support & Dokumentation

För detaljerad information, se:
- Scraper: `README_REFACTORED.md`
- Viewer: `CATALOG_VIEWER_GUIDE.md`
- Tests: `TEST_REPORT.md`
- Refactoring: `REFACTORING_GUIDE.md`
