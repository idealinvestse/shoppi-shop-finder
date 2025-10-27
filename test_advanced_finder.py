#!/usr/bin/env python3
"""
Unit and Integration Tests for Advanced Shop Finder (Refactored)

Run with: pytest test_advanced_finder.py -v
"""

import pytest
import asyncio
import json
import csv
from pathlib import Path

# Import classes to test
import sys
import importlib.util
sys.path.insert(0, str(Path(__file__).parent))

# Import from file with hyphens
spec = importlib.util.spec_from_file_location(
    "advanced_finder_refactored",
    Path(__file__).parent / "advanced-finder-refactored.py"
)
advanced_finder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(advanced_finder)

Config = advanced_finder.Config
Product = advanced_finder.Product
Stats = advanced_finder.Stats
CircuitBreaker = advanced_finder.CircuitBreaker
DataWriter = advanced_finder.DataWriter
StateManager = advanced_finder.StateManager
ProductValidator = advanced_finder.ProductValidator
ShopFinder = advanced_finder.ShopFinder
CircuitState = advanced_finder.CircuitState


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test files."""
    return tmp_path


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    return Config(
        wordlist_path=str(temp_dir / 'test_words.txt'),
        output_path=str(temp_dir / 'test_output.csv'),
        state_path=str(temp_dir / 'test_state.json'),
        base_url='https://test.com/{shop}/products',
        max_concurrent=5,
        rate_limit=0.01,
        timeout=5,
        log_level='ERROR'  # Reduce noise in tests
    )


@pytest.fixture
def sample_product():
    """Create sample product."""
    return Product(
        shop_name='testshop',
        product_name='Test Product',
        price=99.99,
        stock=10,
        discovered_at='2024-01-01T12:00:00'
    )


@pytest.fixture
def sample_product_data():
    """Sample product data from API."""
    return {
        'name': 'Test Item',
        'price': 19.99,
        'stock': 5
    }


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestConfig:
    """Test Config class."""
    
    def test_config_creation(self, test_config):
        """Test basic config creation."""
        assert test_config.max_concurrent == 5
        assert test_config.rate_limit == 0.01
        assert test_config.timeout == 5
    
    def test_config_validation_max_concurrent(self, temp_dir):
        """Test max_concurrent validation."""
        with pytest.raises(ValueError, match="max_concurrent must be at least 1"):
            Config(
                wordlist_path=str(temp_dir / 'words.txt'),
                max_concurrent=0
            )
    
    def test_config_validation_rate_limit(self, temp_dir):
        """Test rate_limit validation."""
        with pytest.raises(ValueError, match="rate_limit cannot be negative"):
            Config(
                wordlist_path=str(temp_dir / 'words.txt'),
                rate_limit=-0.1
            )
    
    def test_config_validation_timeout(self, temp_dir):
        """Test timeout validation."""
        with pytest.raises(ValueError, match="timeout must be at least 1 second"):
            Config(
                wordlist_path=str(temp_dir / 'words.txt'),
                timeout=0
            )
    
    def test_config_validation_url(self, temp_dir):
        """Test URL validation."""
        with pytest.raises(ValueError, match="base_url must contain"):
            Config(
                wordlist_path=str(temp_dir / 'words.txt'),
                base_url='https://test.com/products'  # Missing {shop}
            )
    
    def test_config_env_variables(self, temp_dir, monkeypatch):
        """Test environment variable loading."""
        monkeypatch.setenv('SHOPPI_WORDLIST', 'env_words.txt')
        monkeypatch.setenv('SHOPPI_OUTPUT', 'env_output.csv')
        monkeypatch.setenv('SHOPPI_BASE_URL', 'https://env.com/{shop}')
        
        config = Config(
            wordlist_path=str(temp_dir / 'words.txt'),
            output_path=str(temp_dir / 'output.csv')
        )
        
        assert config.wordlist_path == 'env_words.txt'
        assert config.output_path == 'env_output.csv'
        assert config.base_url == 'https://env.com/{shop}'


# ============================================================================
# PRODUCT TESTS
# ============================================================================

class TestProduct:
    """Test Product class."""
    
    def test_product_creation(self, sample_product):
        """Test basic product creation."""
        assert sample_product.shop_name == 'testshop'
        assert sample_product.product_name == 'Test Product'
        assert sample_product.price == 99.99
        assert sample_product.stock == 10
    
    def test_product_validation_empty_shop_name(self):
        """Test shop_name validation."""
        with pytest.raises(ValueError, match="shop_name cannot be empty"):
            Product(
                shop_name='',
                product_name='Test',
                price=10.0,
                stock=5,
                discovered_at='2024-01-01'
            )
    
    def test_product_validation_empty_product_name(self):
        """Test product_name validation."""
        with pytest.raises(ValueError, match="product_name cannot be empty"):
            Product(
                shop_name='shop',
                product_name='  ',
                price=10.0,
                stock=5,
                discovered_at='2024-01-01'
            )
    
    def test_product_validation_negative_price(self):
        """Test negative price validation."""
        with pytest.raises(ValueError, match="price cannot be negative"):
            Product(
                shop_name='shop',
                product_name='Test',
                price=-10.0,
                stock=5,
                discovered_at='2024-01-01'
            )
    
    def test_product_validation_negative_stock(self):
        """Test negative stock validation."""
        with pytest.raises(ValueError, match="stock cannot be negative"):
            Product(
                shop_name='shop',
                product_name='Test',
                price=10.0,
                stock=-5,
                discovered_at='2024-01-01'
            )
    
    def test_product_to_dict(self, sample_product):
        """Test to_dict method."""
        data = sample_product.to_dict()
        
        assert data['shop_name'] == 'testshop'
        assert data['product_name'] == 'Test Product'
        assert data['price'] == 99.99
        assert data['stock'] == 10
        assert 'discovered_at' in data
    
    def test_product_to_dict_sanitization(self):
        """Test to_dict sanitizes values."""
        product = Product(
            shop_name='  shop  ',
            product_name='  product  ',
            price=19.999,
            stock=5,
            discovered_at='2024-01-01'
        )
        
        data = product.to_dict()
        assert data['shop_name'] == 'shop'
        assert data['product_name'] == 'product'
        assert data['price'] == 20.0  # Rounded


# ============================================================================
# STATS TESTS
# ============================================================================

class TestStats:
    """Test Stats class."""
    
    @pytest.mark.asyncio
    async def test_stats_increment_shops_checked(self):
        """Test incrementing shops_checked."""
        stats = Stats()
        await stats.increment('shops_checked', 5)
        assert stats.shops_checked == 5
    
    @pytest.mark.asyncio
    async def test_stats_increment_shops_found(self):
        """Test incrementing shops_found."""
        stats = Stats()
        await stats.increment('shops_found', 3)
        assert stats.shops_found == 3
    
    @pytest.mark.asyncio
    async def test_stats_increment_products_found(self):
        """Test incrementing products_found."""
        stats = Stats()
        await stats.increment('products_found', 10)
        assert stats.products_found == 10
    
    @pytest.mark.asyncio
    async def test_stats_add_error(self):
        """Test adding errors."""
        stats = Stats()
        await stats.add_error('timeout', 2)
        await stats.add_error('http_500', 1)
        
        assert stats.errors['timeout'] == 2
        assert stats.errors['http_500'] == 1
    
    @pytest.mark.asyncio
    async def test_stats_thread_safety(self):
        """Test thread-safe operations."""
        stats = Stats()
        
        # Simulate concurrent increments
        tasks = [
            stats.increment('shops_checked', 1)
            for _ in range(100)
        ]
        
        await asyncio.gather(*tasks)
        assert stats.shops_checked == 100
    
    def test_stats_summary(self):
        """Test summary generation."""
        stats = Stats()
        stats.shops_checked = 100
        stats.shops_found = 50
        stats.products_found = 200
        
        summary = stats.summary()
        assert '100' in summary
        assert '50' in summary
        assert '200' in summary


# ============================================================================
# CIRCUIT BREAKER TESTS
# ============================================================================

class TestCircuitBreaker:
    """Test CircuitBreaker class."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)
        
        async def failing_func():
            raise Exception("Test error")
        
        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Should raise circuit breaker exception
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self):
        """Test transition to half-open state."""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)
        
        async def failing_func():
            raise Exception("Test error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(1.1)
        
        # Next call should attempt (half-open)
        async def success_func():
            return "recovered"
        
        result = await cb.call(success_func)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset."""
        cb = CircuitBreaker()
        cb.failure_count = 5
        cb.state = CircuitState.OPEN
        
        cb.reset()
        
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED


# ============================================================================
# DATA WRITER TESTS
# ============================================================================

class TestDataWriter:
    """Test DataWriter class."""
    
    @pytest.mark.asyncio
    async def test_datawriter_basic_write(self, temp_dir, sample_product):
        """Test basic writing."""
        output_path = temp_dir / 'test.csv'
        
        async with DataWriter(str(output_path), buffer_size=10) as writer:
            await writer.write(sample_product)
        
        # Verify file exists and has content
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['shop_name'] == 'testshop'
    
    @pytest.mark.asyncio
    async def test_datawriter_buffering(self, temp_dir):
        """Test buffering behavior."""
        output_path = temp_dir / 'test.csv'
        
        async with DataWriter(str(output_path), buffer_size=5) as writer:
            # Write 5 products (should trigger flush)
            for i in range(5):
                product = Product(
                    shop_name=f'shop{i}',
                    product_name=f'Product {i}',
                    price=10.0,
                    stock=5,
                    discovered_at='2024-01-01'
                )
                await writer.write(product)
        
        # Verify all written
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5
    
    @pytest.mark.asyncio
    async def test_datawriter_resume_mode(self, temp_dir, sample_product):
        """Test resume mode appends to file."""
        output_path = temp_dir / 'test.csv'
        
        # Write first product
        async with DataWriter(str(output_path), resume=False) as writer:
            await writer.write(sample_product)
        
        # Append second product
        product2 = Product(
            shop_name='shop2',
            product_name='Product 2',
            price=20.0,
            stock=3,
            discovered_at='2024-01-01'
        )
        
        async with DataWriter(str(output_path), resume=True) as writer:
            await writer.write(product2)
        
        # Verify both products
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2


# ============================================================================
# STATE MANAGER TESTS
# ============================================================================

class TestStateManager:
    """Test StateManager class."""
    
    @pytest.mark.asyncio
    async def test_statemanager_save_and_load(self, temp_dir):
        """Test saving and loading state."""
        state_path = temp_dir / 'state.json'
        sm = StateManager(str(state_path))
        
        await sm.add_shop('shop1')
        await sm.add_shop('shop2')
        await sm.save()
        
        # Load in new instance
        sm2 = StateManager(str(state_path))
        processed = await sm2.load()
        
        assert 'shop1' in processed
        assert 'shop2' in processed
        assert len(processed) == 2
    
    @pytest.mark.asyncio
    async def test_statemanager_no_file(self, temp_dir):
        """Test loading when no file exists."""
        state_path = temp_dir / 'nonexistent.json'
        sm = StateManager(str(state_path))
        
        processed = await sm.load()
        assert len(processed) == 0
    
    @pytest.mark.asyncio
    async def test_statemanager_add_shop(self, temp_dir):
        """Test adding shops."""
        state_path = temp_dir / 'state.json'
        sm = StateManager(str(state_path))
        
        await sm.add_shop('shop1')
        assert 'shop1' in sm.processed_shops
        
        await sm.add_shop('shop2')
        assert 'shop2' in sm.processed_shops
        assert len(sm.processed_shops) == 2
    
    @pytest.mark.asyncio
    async def test_statemanager_thread_safety(self, temp_dir):
        """Test thread-safe operations."""
        state_path = temp_dir / 'state.json'
        sm = StateManager(str(state_path))
        
        # Concurrent adds
        tasks = [
            sm.add_shop(f'shop{i}')
            for i in range(50)
        ]
        
        await asyncio.gather(*tasks)
        assert len(sm.processed_shops) == 50


# ============================================================================
# PRODUCT VALIDATOR TESTS
# ============================================================================

class TestProductValidator:
    """Test ProductValidator class."""
    
    def test_validate_valid_product_data(self, sample_product_data):
        """Test validation of valid product data."""
        validator = ProductValidator()
        assert validator.validate_product_data(sample_product_data) is True
    
    def test_validate_missing_field(self):
        """Test validation with missing field."""
        validator = ProductValidator()
        data = {'name': 'Test', 'price': 10.0}  # Missing stock
        assert validator.validate_product_data(data) is False
    
    def test_validate_invalid_price(self):
        """Test validation with invalid price."""
        validator = ProductValidator()
        data = {'name': 'Test', 'price': 'invalid', 'stock': 5}
        assert validator.validate_product_data(data) is False
    
    def test_validate_invalid_stock(self):
        """Test validation with invalid stock."""
        validator = ProductValidator()
        data = {'name': 'Test', 'price': 10.0, 'stock': 'invalid'}
        assert validator.validate_product_data(data) is False
    
    def test_create_product_valid(self, sample_product_data):
        """Test creating product from valid data."""
        validator = ProductValidator()
        product = validator.create_product('testshop', sample_product_data)
        
        assert product is not None
        assert product.shop_name == 'testshop'
        assert product.product_name == 'Test Item'
        assert product.price == 19.99
    
    def test_create_product_invalid(self):
        """Test creating product from invalid data."""
        validator = ProductValidator()
        data = {'name': 'Test', 'price': 'invalid', 'stock': 5}
        product = validator.create_product('testshop', data)
        
        assert product is None


# ============================================================================
# SHOP FINDER INTEGRATION TESTS
# ============================================================================

class TestShopFinder:
    """Test ShopFinder class."""
    
    def test_shopfinder_initialization(self, test_config):
        """Test ShopFinder initialization."""
        finder = ShopFinder(test_config)
        
        assert finder.config == test_config
        assert isinstance(finder.stats, Stats)
        assert isinstance(finder.circuit_breaker, CircuitBreaker)
        assert isinstance(finder.validator, ProductValidator)
    
    def test_load_wordlist(self, test_config, temp_dir):
        """Test loading wordlist."""
        wordlist_path = temp_dir / 'test_words.txt'
        wordlist_path.write_text('shop1\nshop2\nshop3\nshop2\n')  # Duplicate
        
        finder = ShopFinder(test_config)
        words = finder.load_wordlist()
        
        assert len(words) == 3  # Duplicates removed
        assert 'shop1' in words
        assert 'shop2' in words
        assert 'shop3' in words
    
    def test_load_wordlist_not_found(self, test_config):
        """Test loading non-existent wordlist."""
        finder = ShopFinder(test_config)
        
        with pytest.raises(FileNotFoundError):
            finder.load_wordlist()
    
    @pytest.mark.asyncio
    async def test_load_state_resume_disabled(self, test_config):
        """Test loading state when resume is disabled."""
        test_config.resume = False
        finder = ShopFinder(test_config)
        
        processed = await finder.load_state()
        assert len(processed) == 0
    
    @pytest.mark.asyncio
    async def test_load_state_resume_enabled(self, test_config, temp_dir):
        """Test loading state when resume is enabled."""
        # Create state file
        state_path = temp_dir / 'test_state.json'
        state_path.write_text(json.dumps({
            'processed_shops': ['shop1', 'shop2']
        }))
        
        test_config.resume = True
        finder = ShopFinder(test_config)
        
        processed = await finder.load_state()
        assert 'shop1' in processed
        assert 'shop2' in processed


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
