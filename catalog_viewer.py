#!/usr/bin/env python3
"""
Catalog Viewer - Search and Browse Product Catalog

A powerful viewer for browsing and searching the scraped product catalog.
"""

import csv
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Product:
    """Product with enhanced display capabilities."""
    shop_name: str
    product_name: str
    price: float
    stock: int
    discovered_at: str
    
    def matches_search(self, query: str) -> bool:
        """Check if product matches search query."""
        query_lower = query.lower()
        searchable = f"{self.shop_name} {self.product_name}".lower()
        return query_lower in searchable
    
    def in_price_range(self, min_price: Optional[float], max_price: Optional[float]) -> bool:
        """Check if product is in price range."""
        if min_price is not None and self.price < min_price:
            return False
        if max_price is not None and self.price > max_price:
            return False
        return True
    
    def in_stock_range(self, min_stock: Optional[int], max_stock: Optional[int]) -> bool:
        """Check if product is in stock range."""
        if min_stock is not None and self.stock < min_stock:
            return False
        if max_stock is not None and self.stock > max_stock:
            return False
        return True
    
    def display(self, index: int = 0) -> str:
        """Display product in formatted way."""
        separator = '=' * 80
        return f"\n{separator}\n[{index}] {self.product_name}\n{separator}\nShop:       {self.shop_name}\nPrice:      {self.price:,.2f} kr\nStock:      {self.stock} units\nDiscovered: {self.discovered_at}\n"


class CatalogViewer:
    """Interactive catalog viewer with search and filter."""
    
    def __init__(self, catalog_path: str):
        self.catalog_path = Path(catalog_path)
        self.products: List[Product] = []
        self.load_catalog()
    
    def load_catalog(self):
        """Load products from CSV catalog."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {self.catalog_path}")
        
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    product = Product(
                        shop_name=row['shop_name'],
                        product_name=row['product_name'],
                        price=float(row['price']),
                        stock=int(row['stock']),
                        discovered_at=row['discovered_at']
                    )
                    self.products.append(product)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid row: {e}")
        
        print(f"Loaded {len(self.products):,} products from catalog")
    
    def search(self, query: str = '', 
               shop: Optional[str] = None,
               min_price: Optional[float] = None,
               max_price: Optional[float] = None,
               min_stock: Optional[int] = None,
               max_stock: Optional[int] = None,
               sort_by: str = 'product_name',
               limit: Optional[int] = None) -> List[Product]:
        """Search and filter products."""
        results = self.products.copy()
        
        # Text search
        if query:
            results = [p for p in results if p.matches_search(query)]
        
        # Shop filter
        if shop:
            shop_lower = shop.lower()
            results = [p for p in results if shop_lower in p.shop_name.lower()]
        
        # Price range filter
        results = [p for p in results if p.in_price_range(min_price, max_price)]
        
        # Stock range filter
        results = [p for p in results if p.in_stock_range(min_stock, max_stock)]
        
        # Sort
        reverse = False
        if sort_by.startswith('-'):
            reverse = True
            sort_by = sort_by[1:]
        
        if sort_by == 'price':
            results.sort(key=lambda p: p.price, reverse=reverse)
        elif sort_by == 'stock':
            results.sort(key=lambda p: p.stock, reverse=reverse)
        elif sort_by == 'shop':
            results.sort(key=lambda p: p.shop_name.lower(), reverse=reverse)
        elif sort_by == 'discovered':
            results.sort(key=lambda p: p.discovered_at, reverse=reverse)
        else:
            results.sort(key=lambda p: p.product_name.lower(), reverse=reverse)
        
        # Limit
        if limit:
            results = results[:limit]
        
        return results
    
    def display_results(self, results: List[Product], show_details: bool = True):
        """Display search results."""
        if not results:
            print("\nNo products found matching your criteria.")
            return
        
        print(f"\nFound {len(results):,} products\n")
        
        if show_details:
            for i, product in enumerate(results, 1):
                print(product.display(i))
        else:
            header_format = f"{'#':<5} {'Shop':<20} {'Product':<40} {'Price':>12} {'Stock':>8}"
            print(header_format)
            print("-" * 90)
            for i, product in enumerate(results, 1):
                shop = product.shop_name[:20]
                name = product.product_name[:40]
                print(f"{i:<5} {shop:<20} {name:<40} {product.price:>11,.2f}kr {product.stock:>7}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        if not self.products:
            return {}
        
        shops = {}
        prices = [p.price for p in self.products]
        stocks = [p.stock for p in self.products]
        
        for product in self.products:
            shops[product.shop_name] = shops.get(product.shop_name, 0) + 1
        
        return {
            'total_products': len(self.products),
            'total_shops': len(shops),
            'top_shops': sorted(shops.items(), key=lambda x: x[1], reverse=True)[:10],
            'price_stats': {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices)
            },
            'stock_stats': {
                'min': min(stocks),
                'max': max(stocks),
                'avg': sum(stocks) / len(stocks),
                'total': sum(stocks)
            }
        }
    
    def display_statistics(self):
        """Display catalog statistics."""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print(" CATALOG STATISTICS".center(80))
        print("="*80)
        
        print(f"\nProducts:  {stats['total_products']:,}")
        print(f"Shops:     {stats['total_shops']:,}")
        
        print(f"\nPrice Range:")
        print(f"   Min:  {stats['price_stats']['min']:>10,.2f} kr")
        print(f"   Avg:  {stats['price_stats']['avg']:>10,.2f} kr")
        print(f"   Max:  {stats['price_stats']['max']:>10,.2f} kr")
        
        print(f"\nStock:")
        print(f"   Total: {stats['stock_stats']['total']:>10,} units")
        print(f"   Min:   {stats['stock_stats']['min']:>10,} units")
        print(f"   Avg:   {stats['stock_stats']['avg']:>10,.1f} units")
        print(f"   Max:   {stats['stock_stats']['max']:>10,} units")
        
        print(f"\nTop 10 Shops by Product Count:")
        for i, (shop, count) in enumerate(stats['top_shops'], 1):
            print(f"   {i:>2}. {shop:<30} {count:>6,} products")
        
        print("\n" + "="*80 + "\n")
    
    def export_results(self, results: List[Product], output_path: str, format_type: str = 'csv'):
        """Export search results to file."""
        output_file = Path(output_path)
        
        if format_type == 'json':
            data = [{
                'shop': p.shop_name,
                'product': p.product_name,
                'price': p.price,
                'stock': p.stock,
                'discovered': p.discovered_at
            } for p in results]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format_type == 'html':
            html = self.generate_html(results)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
        
        else:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['shop_name', 'product_name', 'price', 'stock', 'discovered_at'])
                writer.writeheader()
                for p in results:
                    writer.writerow({
                        'shop_name': p.shop_name,
                        'product_name': p.product_name,
                        'price': p.price,
                        'stock': p.stock,
                        'discovered_at': p.discovered_at
                    })
        
        print(f"Exported {len(results):,} products to {output_file}")
    
    def generate_html(self, results: List[Product]) -> str:
        """Generate HTML view of results."""
        rows_html = ""
        for product in results:
            stock_class = 'low-stock' if product.stock < 5 else ''
            rows_html += f"<tr><td class='shop'>{product.shop_name}</td><td>{product.product_name}</td>"
            rows_html += f"<td class='price'>{product.price:,.2f} kr</td>"
            rows_html += f"<td class='stock {stock_class}'>{product.stock}</td>"
            rows_html += f"<td>{product.discovered_at[:10]}</td></tr>\n"
        
        html_template = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Product Catalog</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
.container{{max-width:1200px;margin:0 auto;background:white;padding:20px}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}
th{{background:#007bff;color:white;padding:10px;text-align:left}}
td{{padding:8px;border-bottom:1px solid #ddd}}
.price{{text-align:right;font-weight:bold;color:#28a745}}
.shop{{color:#007bff}}
.low-stock{{color:#dc3545}}
</style>
</head>
<body>
<div class="container">
<h1>Product Catalog ({len(results):,} products)</h1>
<table>
<tr><th>Shop</th><th>Product</th><th>Price</th><th>Stock</th><th>Date</th></tr>
{rows_html}
</table>
</div>
</body>
</html>"""
        return html_template


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Search and browse product catalog')
    
    parser.add_argument('catalog', help='Path to catalog CSV file')
    parser.add_argument('--search', '-s', help='Search query')
    parser.add_argument('--shop', help='Filter by shop name')
    parser.add_argument('--min-price', type=float, help='Minimum price')
    parser.add_argument('--max-price', type=float, help='Maximum price')
    parser.add_argument('--min-stock', type=int, help='Minimum stock')
    parser.add_argument('--max-stock', type=int, help='Maximum stock')
    parser.add_argument('--sort', default='product_name',
                       choices=['product_name', 'shop', 'price', '-price', 'stock', '-stock'],
                       help='Sort by field')
    parser.add_argument('--limit', '-l', type=int, help='Limit results')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--compact', action='store_true', help='Compact view')
    parser.add_argument('--export', '-e', help='Export to file')
    parser.add_argument('--format', choices=['csv', 'json', 'html'], default='csv')
    
    args = parser.parse_args()
    
    try:
        viewer = CatalogViewer(args.catalog)
        
        if args.stats:
            viewer.display_statistics()
            return
        
        results = viewer.search(
            query=args.search or '',
            shop=args.shop,
            min_price=args.min_price,
            max_price=args.max_price,
            min_stock=args.min_stock,
            max_stock=args.max_stock,
            sort_by=args.sort,
            limit=args.limit
        )
        
        viewer.display_results(results, show_details=not args.compact)
        
        if args.export:
            viewer.export_results(results, args.export, args.format)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
