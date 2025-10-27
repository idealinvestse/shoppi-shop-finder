# Refactoring Guide: Advanced Shop Finder

## Översikt (Overview)

Den refaktorerade versionen (`advanced-finder-refactored.py`) innehåller betydande förbättringar för arkitektur, driftsäkerhet och underhållbarhet.

## Huvudförbättringar (Key Improvements)

### 1. **Arkitektoniska Förbättringar** 

#### Separation of Concerns
- **CircuitBreaker**: Hanterar fault tolerance och förhindrar kaskaderande fel
- **DataWriter**: Separat klass för CSV-skrivning med buffring
- **StateManager**: Dedikerad hantering av tillstånd för resume-funktionalitet
- **ProductValidator**: Validering och sanitering av produktdata
- **Stats**: Thread-safe statistikspårning

#### Fördelar
- Varje klass har ett enda ansvar (Single Responsibility Principle)
- Enklare att testa individuella komponenter
- Bättre kodorganisation och läsbarhet

### 2. **Driftsäkerhet (Reliability)**

#### Circuit Breaker Pattern
```python
class CircuitBreaker:
    """Förhindrar att systemet överbelastas vid fel"""
    - CLOSED: Normalt läge, förfrågningar går igenom
    - OPEN: För många fel, blockerar förfrågningar
    - HALF_OPEN: Testar om systemet återhämtat sig
```

**Fördelar:**
- Skyddar mot kaskaderande fel
- Automatisk återhämtning
- Förhindrar resurslockup

#### Förbättrad Felhantering
```python
@backoff.on_exception(
    backoff.expo,
    (aiohttp.ClientError, asyncio.TimeoutError),
    max_tries=3,
    max_time=60,
    giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404
)
```

**Förbättringar:**
- Exponentiell backoff för retry
- Inte retry på 404 (giveup predicate)
- Bättre hantering av 5xx-fel
- Thread-safe felstatistik

#### Data Buffring
```python
class DataWriter:
    """Buffrar skrivningar för bättre prestanda"""
    - Skriver i batch (default 100 produkter)
    - Automatisk flush vid fel
    - Thread-safe operationer
```

**Fördelar:**
- Minskar I/O-operationer
- Garanterad dataintegritet
- Bättre prestanda

### 3. **State Management**

#### Förbättrad Resume-funktionalitet
```python
class StateManager:
    """Hanterar tillstånd i JSON-fil istället för CSV"""
    - Dedikerad state file (finder_state.json)
    - Snabbare laddning av tillstånd
    - Inkluderar metadata (last_updated)
```

**Jämförelse:**
- **Tidigare**: Läste CSV-fil (långsam, opålitlig)
- **Nu**: Dedikerad JSON state file (snabb, robust)

### 4. **Connection Pool Management**

```python
connector = TCPConnector(
    limit=100,                    # Total connection pool
    limit_per_host=10,            # Per host limit
    ttl_dns_cache=300,            # DNS cache TTL
    enable_cleanup_closed=True    # Cleanup closed connections
)
```

**Förbättringar:**
- Bättre resursutnyttjande
- DNS caching för prestanda
- Automatisk cleanup av connections

### 5. **Validering (Validation)**

#### Product Validation
```python
class Product:
    def __post_init__(self):
        """Validerar produktdata vid skapande"""
        - Kontrollerar tomma fält
        - Validerar negativa värden
        - Sanifierar data
```

#### Configuration Validation
```python
class Config:
    def __post_init__(self):
        """Validerar konfiguration"""
        - Kontrollerar giltiga värden
        - Verifierar URL-format
        - Laddar environment variables
```

**Fördelar:**
- Fångar fel tidigt
- Förhindrar invalid data i output
- Tydliga felmeddelanden

### 6. **Miljövariabler (Environment Variables)**

```bash
# Stöd för environment variables
export SHOPPI_WORDLIST="my_shops.txt"
export SHOPPI_OUTPUT="results.csv"
export SHOPPI_BASE_URL="https://api.shoppi.com/{shop}/items"
```

**Fördelar:**
- Flexibel konfiguration
- Säkrare för secrets (om URL innehåller API-nycklar)
- Docker/container-friendly

### 7. **Concurrency Improvements**

#### Tidigare: Batch Processing
```python
# Processade i batchar (komplicerat)
batch_size = self.config.max_concurrent
for i in range(0, len(remaining_shops), batch_size):
    batch = remaining_shops[i:i + batch_size]
    await self.process_shop_batch(session, batch, writer, pbar)
```

#### Nu: Semaphore-baserad Concurrency
```python
# Enklare och mer effektivt
self.semaphore = asyncio.Semaphore(max_concurrent)
tasks = [process_shop(shop) for shop in shops]
await asyncio.gather(*tasks, return_exceptions=True)
```

**Fördelar:**
- Enklare kod
- Bättre felhantering (return_exceptions=True)
- Automatisk load balancing

### 8. **Thread Safety**

#### Stats Tracking
```python
class Stats:
    async def increment(self, field: str, value: int = 1):
        """Thread-safe med async lock"""
        async with self._lock:
            # Säker inkrementering
```

**Viktigt för:**
- Korrekt statistik vid concurrent operations
- Undviker race conditions
- Garanterar dataintegritet

## Användning (Usage)

### Grundläggande
```bash
python advanced-finder-refactored.py --wordlist words.txt --output results.csv
```

### Avancerad
```bash
# Hög concurrency med rate limiting
python advanced-finder-refactored.py \
    --max-concurrent 100 \
    --rate-limit 0.05 \
    --circuit-threshold 10 \
    --resume \
    --log-level DEBUG
```

### Med Miljövariabler
```bash
export SHOPPI_WORDLIST="shops.txt"
export SHOPPI_OUTPUT="products.csv"
export SHOPPI_BASE_URL="https://api.example.com/{shop}/products"

python advanced-finder-refactored.py --resume
```

## Prestanda & Skalning

### Rekommenderade Settings

#### Små Projekt (< 1000 shops)
```bash
--max-concurrent 20
--rate-limit 0.1
--circuit-threshold 5
```

#### Medelstora Projekt (1000-10000 shops)
```bash
--max-concurrent 50
--rate-limit 0.05
--circuit-threshold 10
```

#### Stora Projekt (> 10000 shops)
```bash
--max-concurrent 100
--rate-limit 0.02
--circuit-threshold 15
```

### Minnesanvändning

- **Bufferstorlek**: 100 produkter (kan justeras i DataWriter)
- **Connection Pool**: 100 connections (konfigurerbart)
- **State File**: Lagras komprimerat i JSON

## Felhantering

### Circuit Breaker States

1. **CLOSED** (Normal)
   - Alla förfrågningar går igenom
   - Räknar fel

2. **OPEN** (Överbelastad)
   - Blockerar förfrågningar
   - Väntar på timeout (default 60s)

3. **HALF_OPEN** (Test)
   - Tillåter testförfrågningar
   - Återgår till CLOSED vid success

### Retry Logic

- **Exponential Backoff**: 1s, 2s, 4s, ...
- **Max Tries**: 3
- **Max Time**: 60 seconds
- **Skip**: 404 errors (shop finns inte)

## Testning

### Manuella Tester

```bash
# Test med liten wordlist
echo -e "test1\ntest2\ntest3" > test_words.txt
python advanced-finder-refactored.py --wordlist test_words.txt --output test.csv

# Test resume funktionalitet
# Avbryt med Ctrl+C
python advanced-finder-refactored.py --wordlist large.txt --output out.csv
# Fortsätt
python advanced-finder-refactored.py --wordlist large.txt --output out.csv --resume

# Test circuit breaker (med fel URL)
python advanced-finder-refactored.py --url https://invalid.url/{shop}/products
```

### Unit Tests (Exempel)

```python
import pytest
from advanced_finder_refactored import ProductValidator, Product

def test_product_validation():
    validator = ProductValidator()
    
    # Valid product
    data = {'name': 'Test', 'price': 10.99, 'stock': 5}
    assert validator.validate_product_data(data) == True
    
    # Invalid product (missing field)
    data = {'name': 'Test', 'price': 10.99}
    assert validator.validate_product_data(data) == False
    
def test_product_creation():
    product = Product(
        shop_name='test',
        product_name='Item',
        price=9.99,
        stock=10,
        discovered_at='2024-01-01T12:00:00'
    )
    assert product.price == 9.99
    
    # Test negative price validation
    with pytest.raises(ValueError):
        Product(
            shop_name='test',
            product_name='Item',
            price=-1,
            stock=10,
            discovered_at='2024-01-01'
        )
```

## Migration från Gammal Version

### Steg 1: Backup
```bash
cp advanced-finder.py advanced-finder.py.backup
cp full_catalog.csv full_catalog.csv.backup
```

### Steg 2: Kör Refactored Version
```bash
python advanced-finder-refactored.py \
    --wordlist words.txt \
    --output full_catalog_new.csv \
    --state finder_state.json
```

### Steg 3: Jämför Resultat
```bash
# Kontrollera antal rader
wc -l full_catalog.csv full_catalog_new.csv

# Jämför innehåll (sorterat)
sort full_catalog.csv > old_sorted.csv
sort full_catalog_new.csv > new_sorted.csv
diff old_sorted.csv new_sorted.csv
```

## Felsökning (Troubleshooting)

### Problem: Circuit Breaker är OPEN
**Lösning**: Öka `--circuit-threshold` eller `--circuit-timeout`

### Problem: För långsam
**Lösning**: 
- Öka `--max-concurrent`
- Minska `--rate-limit`
- Kontrollera nätverkslatens

### Problem: Memory Error
**Lösning**:
- Minska buffer size i DataWriter
- Minska `--max-concurrent`
- Processa wordlist i chunks

### Problem: State file korrupt
**Lösning**:
```bash
# Ta bort state file och börja om
rm finder_state.json
python advanced-finder-refactored.py --wordlist words.txt
```

## Best Practices

### 1. Rate Limiting
- Respektera server limits
- Använd rimliga värden (0.05-0.1s)
- Övervaka HTTP 429 errors

### 2. Error Monitoring
- Granska log files regelbundet
- Observera error types i statistik
- Justera circuit breaker settings

### 3. State Management
- Backup state file regelbundet
- Använd `--resume` vid avbrott
- Rensa gamla state files

### 4. Resource Management
- Övervaka minnesanvändning
- Justera connection pool
- Använd rimliga timeout values

## Framtida Förbättringar

### Potential Additions
1. **Prometheus Metrics**: Export för monitoring
2. **Rate Limit Detection**: Automatisk anpassning vid 429
3. **Distributed Processing**: Support för flera workers
4. **Database Output**: Stöd för PostgreSQL/MySQL
5. **API Versioning**: Hantera olika API-versioner
6. **Caching**: Redis cache för products
7. **Webhooks**: Notifikationer vid completion

## Sammanfattning

Den refaktorerade versionen erbjuder:

✅ **Bättre Arkitektur**: Separation of concerns, testbart  
✅ **Högre Driftsäkerhet**: Circuit breaker, retry logic, validation  
✅ **Bättre Prestanda**: Connection pooling, buffering, concurrency  
✅ **Enklare Underhåll**: Tydlig kod, bättre felhantering  
✅ **Mer Flexibel**: Environment variables, configuration validation  
✅ **Production-Ready**: Thread-safe, robust error handling  

Använd den refaktorerade versionen för nya projekt och migrera befintliga projekt gradvis.
