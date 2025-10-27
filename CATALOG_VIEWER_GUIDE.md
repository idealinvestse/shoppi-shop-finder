# Catalog Viewer Guide

## Översikt

`catalog_viewer.py` är ett kraftfullt verktyg för att söka, filtrera och presentera produktkatalogen på ett användarvänligt sätt.

## Installation

Inga extra dependencies krävs utöver Python standard library.

## Användning

### Grundläggande Kommandon

#### Visa Statistik
```bash
python catalog_viewer.py full_catalog.csv --stats
```

**Output:**
```
================================================================================
                           CATALOG STATISTICS
================================================================================

Products:  1,234
Shops:     45

Price Range:
   Min:        9.99 kr
   Avg:      499.50 kr
   Max:    9,999.00 kr

Stock:
   Total:     15,678 units
   Min:            1 units
   Avg:         12.7 units
   Max:          500 units

Top 10 Shops by Product Count:
    1. TechStore                           156 products
    2. ElectronicsHub                      142 products
    3. GadgetWorld                         128 products
```

#### Sök Efter Produkter
```bash
# Sök efter "laptop"
python catalog_viewer.py full_catalog.csv --search "laptop"

# Sök efter "phone" med kompakt vy
python catalog_viewer.py full_catalog.csv --search "phone" --compact
```

#### Filtrera Efter Shop
```bash
python catalog_viewer.py full_catalog.csv --shop "TechStore"
```

#### Filtrera Efter Pris
```bash
# Produkter mellan 100-500 kr
python catalog_viewer.py full_catalog.csv --min-price 100 --max-price 500

# Produkter under 100 kr
python catalog_viewer.py full_catalog.csv --max-price 100

# Produkter över 1000 kr
python catalog_viewer.py full_catalog.csv --min-price 1000
```

#### Filtrera Efter Lagerstatus
```bash
# Produkter med minst 10 i lager
python catalog_viewer.py full_catalog.csv --min-stock 10

# Produkter med låg stock (< 5)
python catalog_viewer.py full_catalog.csv --max-stock 5
```

### Sortering

```bash
# Sortera efter pris (stigande)
python catalog_viewer.py full_catalog.csv --sort price

# Sortera efter pris (fallande)
python catalog_viewer.py full_catalog.csv --sort -price

# Sortera efter stock
python catalog_viewer.py full_catalog.csv --sort stock

# Sortera efter shop
python catalog_viewer.py full_catalog.csv --sort shop
```

### Kombinera Filtrer

```bash
# Hitta laptops i TechStore mellan 5000-10000 kr med stock > 5
python catalog_viewer.py full_catalog.csv \
    --search "laptop" \
    --shop "TechStore" \
    --min-price 5000 \
    --max-price 10000 \
    --min-stock 5 \
    --sort -price
```

### Begränsa Resultat

```bash
# Visa bara top 10 billigaste produkter
python catalog_viewer.py full_catalog.csv --sort price --limit 10

# Visa top 20 produkter med mest stock
python catalog_viewer.py full_catalog.csv --sort -stock --limit 20
```

### Export

#### Exportera till CSV
```bash
python catalog_viewer.py full_catalog.csv \
    --search "laptop" \
    --export laptops.csv \
    --format csv
```

#### Exportera till JSON
```bash
python catalog_viewer.py full_catalog.csv \
    --shop "TechStore" \
    --export techstore_products.json \
    --format json
```

**JSON Format:**
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

#### Exportera till HTML
```bash
python catalog_viewer.py full_catalog.csv \
    --export catalog.html \
    --format html
```

HTML-filen innehåller:
- Responsiv tabell
- Sökfunktion (live)
- Sorteringsbar (klicka på kolumnrubriker)
- Färgkodad stock (röd för < 5)
- Styling och formatering

## Användningsfall

### 1. Hitta Billigaste Produkter
```bash
python catalog_viewer.py full_catalog.csv \
    --search "phone" \
    --sort price \
    --limit 10 \
    --compact
```

### 2. Inventering Per Shop
```bash
python catalog_viewer.py full_catalog.csv \
    --shop "MyShop" \
    --export myshop_inventory.csv
```

### 3. Låg Stock Alert
```bash
python catalog_viewer.py full_catalog.csv \
    --max-stock 5 \
    --export low_stock_alert.csv
```

### 4. Prisanalys
```bash
python catalog_viewer.py full_catalog.csv \
    --search "laptop" \
    --min-price 5000 \
    --max-price 10000 \
    --sort price \
    --compact
```

### 5. Produktjämförelse (HTML)
```bash
python catalog_viewer.py full_catalog.csv \
    --search "smartphone" \
    --sort -price \
    --export comparison.html \
    --format html
```

### 6. Dataanalys (JSON)
```bash
python catalog_viewer.py full_catalog.csv \
    --export all_products.json \
    --format json
```

## Output Format

### Detaljerad Vy
```
================================================================================
[1] Laptop Pro 15
================================================================================
Shop:       TechStore
Price:      8,999.00 kr
Stock:      15 units
Discovered: 2024-01-27T10:30:00

================================================================================
[2] Gaming Laptop X
================================================================================
Shop:       GamerShop
Price:      12,999.00 kr
Stock:      8 units
Discovered: 2024-01-27T11:15:00
```

### Kompakt Vy (--compact)
```
#     Shop                 Product                                     Price    Stock
------------------------------------------------------------------------------------------
1     TechStore            Laptop Pro 15                            8,999.00kr      15
2     GamerShop            Gaming Laptop X                         12,999.00kr       8
3     OfficeSupply         Business Laptop                          6,499.00kr      25
```

## Tips & Tricks

### 1. Snabb Produktsökning
Skapa alias för vanliga sökningar:
```bash
alias find-laptop="python catalog_viewer.py full_catalog.csv --search laptop --compact"
alias find-cheap="python catalog_viewer.py full_catalog.csv --max-price 500 --compact"
```

### 2. Automatisk Rapport
Skapa daglig rapport:
```bash
# low_stock_report.sh
python catalog_viewer.py full_catalog.csv \
    --max-stock 10 \
    --export "low_stock_$(date +%Y%m%d).html" \
    --format html
```

### 3. Prisjämförelse
Exportera till JSON och använd jq:
```bash
python catalog_viewer.py full_catalog.csv \
    --search "laptop" \
    --export laptops.json \
    --format json

# Hitta genomsnittspris
cat laptops.json | jq '[.[].price] | add / length'
```

### 4. Shop-specifika Kataloger
Generera HTML-kataloger per shop:
```bash
for shop in TechStore GamerShop OfficeSupply; do
    python catalog_viewer.py full_catalog.csv \
        --shop "$shop" \
        --export "${shop}_catalog.html" \
        --format html
done
```

## Avancerade Exempel

### Multi-Shop Prisjämförelse
```bash
# Hitta samma produkt i olika shops
python catalog_viewer.py full_catalog.csv \
    --search "iPhone 15" \
    --sort price \
    --compact
```

### Stock Monitoring
```bash
# Produkter med kritiskt låg stock
python catalog_viewer.py full_catalog.csv \
    --max-stock 3 \
    --sort stock \
    --export critical_stock.csv
```

### Premium Products
```bash
# Produkter över 10,000 kr
python catalog_viewer.py full_catalog.csv \
    --min-price 10000 \
    --sort -price \
    --export premium_products.html \
    --format html
```

## Integration med Andra Verktyg

### Excel
```bash
# Exportera till CSV, öppna i Excel
python catalog_viewer.py full_catalog.csv \
    --shop "MyShop" \
    --export myshop.csv

# Windows
start myshop.csv

# Mac
open myshop.csv
```

### Database Import
```bash
# Exportera till JSON för database import
python catalog_viewer.py full_catalog.csv \
    --export products.json \
    --format json

# Import till MongoDB (exempel)
mongoimport --db shop --collection products --file products.json --jsonArray
```

### Web Dashboard
```bash
# Generera HTML dashboard
python catalog_viewer.py full_catalog.csv \
    --export dashboard.html \
    --format html

# Servera med Python HTTP server
python -m http.server 8000
# Öppna: http://localhost:8000/dashboard.html
```

## Felhantering

### Problem: Catalog inte hittad
```
Error: Catalog not found: full_catalog.csv
```
**Lösning**: Kontrollera att katalogfilen finns och sökvägen är korrekt.

### Problem: Inga resultat
```
No products found matching your criteria.
```
**Lösning**: Prova bredare sökkriterier eller kontrollera spelling.

### Problem: Invalid CSV
```
Warning: Skipping invalid row: ...
```
**Lösning**: Kör scraper igen eller rensa CSV-filen manuellt.

## API (Programmatisk Användning)

```python
from catalog_viewer import CatalogViewer

# Ladda katalog
viewer = CatalogViewer('full_catalog.csv')

# Sök
results = viewer.search(
    query='laptop',
    min_price=5000,
    max_price=10000,
    sort_by='price',
    limit=10
)

# Visa resultat
for product in results:
    print(f"{product.product_name}: {product.price} kr")

# Statistik
stats = viewer.get_statistics()
print(f"Total products: {stats['total_products']}")

# Export
viewer.export_results(results, 'filtered.json', 'json')
```

## Sammanfattning

`catalog_viewer.py` ger dig kraftfulla verktyg för att:
- ✅ Söka och filtrera produkter
- ✅ Visa statistik och analytics
- ✅ Sortera efter olika kriterier
- ✅ Exportera till CSV, JSON, HTML
- ✅ Generera rapporter och dashboards
- ✅ Integrera med andra system

För fler exempel, se `python catalog_viewer.py --help`
