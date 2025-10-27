# Advanced Shop Finder - Refactored Version

## Snabb Start (Quick Start)

### Installation

```bash
# Installera beroenden
pip install aiohttp tqdm backoff
```

### Grundläggande Användning

```bash
# Kör med standardinställningar
python advanced-finder-refactored.py

# Med egna inställningar
python advanced-finder-refactored.py \
    --wordlist shops.txt \
    --output products.csv \
    --max-concurrent 50 \
    --rate-limit 0.1
```

### Resume Efter Avbrott

```bash
# Avbryt med Ctrl+C, fortsätt sedan med:
python advanced-finder-refactored.py --resume
```

## Huvudförbättringar

### 🏗️ Arkitektur
- **CircuitBreaker**: Förhindrar kaskaderande fel
- **DataWriter**: Buffrad skrivning med automatisk flush
- **StateManager**: Robust state management för resume
- **ProductValidator**: Validering av all data

### 🛡️ Driftsäkerhet
- Exponential backoff retry
- Connection pooling
- Thread-safe operations
- Automatic state saving

### ⚡ Prestanda
- Semaphore-baserad concurrency
- DNS caching
- Buffrad I/O
- Optimerad connection pool

## Konfiguration

### Via Kommandorad

```bash
python advanced-finder-refactored.py \
    --max-concurrent 100 \
    --rate-limit 0.05 \
    --timeout 30 \
    --circuit-threshold 10 \
    --resume
```

### Via Miljövariabler

```bash
export SHOPPI_WORDLIST="my_shops.txt"
export SHOPPI_OUTPUT="results.csv"
export SHOPPI_BASE_URL="https://api.example.com/{shop}/products"

python advanced-finder-refactored.py
```

## Filer

- **advanced-finder-refactored.py** - Huvudfil (använd denna!)
- **REFACTORING_GUIDE.md** - Detaljerad dokumentation
- **finder_state.json** - State fil (skapas automatiskt)
- **shop_finder_YYYYMMDD_HHMMSS.log** - Log fil

## Skillnader från Original

| Feature | Original | Refactored |
|---------|----------|------------|
| Concurrency | Batch processing | Semaphore-based |
| State management | CSV parsing | JSON state file |
| Error handling | Basic | Circuit breaker + retry |
| Data validation | None | Full validation |
| Resource management | Basic | Advanced pooling |
| Thread safety | Partial | Complete |

## Exempel

### Test med Liten Dataset

```bash
# Skapa test wordlist
echo -e "shop1\nshop2\nshop3" > test.txt

# Kör
python advanced-finder-refactored.py --wordlist test.txt --output test.csv
```

### Production Settings

```bash
python advanced-finder-refactored.py \
    --wordlist production_shops.txt \
    --output full_catalog.csv \
    --max-concurrent 100 \
    --rate-limit 0.02 \
    --circuit-threshold 15 \
    --resume \
    --log-level INFO
```

## Felsökning

### Circuit Breaker Öppen
```bash
# Öka tröskelvärdet
--circuit-threshold 20 --circuit-timeout 120
```

### För Långsam
```bash
# Öka concurrency, minska rate limit
--max-concurrent 150 --rate-limit 0.01
```

### Memory Issues
```bash
# Minska concurrency
--max-concurrent 25
```

## Support

För detaljerad dokumentation, se **REFACTORING_GUIDE.md**.

## Licens

Samma som originalprojektet.
