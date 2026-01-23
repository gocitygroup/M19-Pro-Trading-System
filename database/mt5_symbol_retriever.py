"""
MetaTrader 5 Symbol Retriever and Categorizer

This script connects to a running MT5 terminal, retrieves all tradable symbols,
categorizes them by asset type and subcategory, and exports to JSON.

Author: Trading Systems Engineering
"""

import MetaTrader5 as mt5
import json
import msgpack
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import os

# Determine the utils directory (this file's location)
UTILS_DIR = Path(__file__).parent.resolve()


@dataclass
class SymbolInfo:
    """Data class to hold symbol information."""
    name: str
    description: str
    category: str
    subcategory: str
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    digits: Optional[int] = None
    trade_contract_size: Optional[float] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None


class MT5Connection:
    """Handles MetaTrader 5 connection lifecycle."""
    
    def __init__(self):
        self.connected = False
    
    def initialize(self) -> bool:
        """
        Initialize connection to MT5 terminal.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not mt5.initialize():
            print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
            return False
        
        self.connected = True
        print("[SUCCESS] Connected to MetaTrader 5")
        return True
    
    def validate_connection(self) -> bool:
        """
        Validate the connection and display terminal info.
        
        Returns:
            bool: True if connection is valid
        """
        if not self.connected:
            print("[ERROR] Not connected to MT5")
            return False
        
        terminal_info = mt5.terminal_info()
        account_info = mt5.account_info()
        
        if terminal_info is None or account_info is None:
            print("[ERROR] Failed to retrieve terminal/account info")
            return False
        
        print(f"\n[INFO] Terminal: {terminal_info.name}")
        print(f"[INFO] Company: {terminal_info.company}")
        print(f"[INFO] Account: {account_info.login}")
        print(f"[INFO] Server: {account_info.server}")
        print(f"[INFO] Balance: {account_info.balance} {account_info.currency}\n")
        
        return True
    
    def shutdown(self):
        """Gracefully shutdown MT5 connection."""
        if self.connected:
            mt5.shutdown()
            print("[INFO] MT5 connection closed")
            self.connected = False


class SymbolCategorizer:
    """Categorizes trading symbols into asset classes and subcategories."""
    
    # Major Forex pairs - pairs involving major currencies
    MAJOR_CURRENCIES = {'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SGD', 'HKD', 'CNY', 'INR', 'KRW', 'MXN', 'RUB', 'ZAR', 'TRY', 'BRL', 'CLP', 'COP', 'PEN', 'ARS', 'CHL', 'CHN', 'HKG', 'IND', 'MEX', 'PER', 'RUS', 'SAU', 'SGP', 'THA', 'TUR', 'VNM', 'ZAF'}
    
    # Crypto identifiers
    CRYPTO_PATTERNS = {
        'BTC': r'BTC|BITCOIN',
        'ETH': r'ETH|ETHEREUM',
        'STABLECOIN': r'USDT|USDC|BUSD|DAI|TUSD|USDD',
        'ALTCOIN': r'XRP|LTC|ADA|DOT|DOGE|SHIB|MATIC|SOL|BNB|LINK|UNI|AVAX'
    }
    
    # Commodity patterns
    METAL_PATTERNS = r'XAU|GOLD|XAG|SILVER|COPPER|PLATINUM|PALLADIUM'
    ENERGY_PATTERNS = r'OIL|WTI|BRENT|CRUDE|GAS|NGAS|NATURALGAS'
    
    @staticmethod
    def extract_currency_pair(symbol: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract base and quote currencies from a symbol name.
        
        Args:
            symbol: Symbol name (e.g., EURUSD, GBPUSD.a)
            
        Returns:
            Tuple of (base_currency, quote_currency) or (None, None)
        """
        # Remove common suffixes and special characters
        cleaned = re.sub(r'[._#-].*$', '', symbol).upper()
        
        # Check if it matches forex pattern (6-8 chars, all letters)
        if len(cleaned) >= 6 and cleaned.isalpha():
            # Try to match known currency pairs
            for i in range(3, 5):  # Currency codes are typically 3-4 chars
                if i <= len(cleaned) - 3:
                    base = cleaned[:i]
                    quote = cleaned[i:i+3] if i+3 <= len(cleaned) else cleaned[i:]
                    
                    # Check if both are valid currency codes
                    if (len(base) in [3, 4] and len(quote) == 3 and 
                        base.isalpha() and quote.isalpha()):
                        return base, quote
        
        return None, None
    
    def categorize_forex(self, base: str, quote: str) -> str:
        """
        Categorize forex pair into Major, Minor, or Cross.
        
        Args:
            base: Base currency
            quote: Quote currency
            
        Returns:
            Subcategory string
        """
        has_usd = 'USD' in (base, quote)
        base_is_major = base in self.MAJOR_CURRENCIES
        quote_is_major = quote in self.MAJOR_CURRENCIES
        
        if has_usd and base_is_major and quote_is_major:
            return "Major"
        elif has_usd and (base_is_major or quote_is_major):
            return "Minor"
        elif base_is_major and quote_is_major:
            return "Cross"
        else:
            return "Exotic"
    
    def categorize_crypto(self, symbol: str) -> str:
        """
        Categorize cryptocurrency pair.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Subcategory string
        """
        symbol_upper = symbol.upper()
        
        for crypto_type, pattern in self.CRYPTO_PATTERNS.items():
            if re.search(pattern, symbol_upper):
                return crypto_type
        
        return "Other"
    
    def categorize_commodity(self, symbol: str) -> str:
        """
        Categorize commodity.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Subcategory string
        """
        symbol_upper = symbol.upper()
        
        if re.search(self.METAL_PATTERNS, symbol_upper):
            return "Metals"
        elif re.search(self.ENERGY_PATTERNS, symbol_upper):
            return "Energies"
        else:
            return "Other"
    
    def categorize_symbol(self, symbol_name: str, symbol_path: str) -> Tuple[str, str, Optional[str], Optional[str]]:
        """
        Determine the category and subcategory of a symbol.
        
        Args:
            symbol_name: Symbol name
            symbol_path: MT5 symbol path (e.g., "Forex\\Majors")
            
        Returns:
            Tuple of (category, subcategory, base_currency, quote_currency)
        """
        symbol_upper = symbol_name.upper()
        path_upper = symbol_path.upper()
        
        # Check crypto first (most distinctive)
        if any(re.search(pattern, symbol_upper) for pattern in self.CRYPTO_PATTERNS.values()):
            subcategory = self.categorize_crypto(symbol_name)
            return "Crypto", subcategory, None, None
        
        # Check commodities
        if (re.search(self.METAL_PATTERNS, symbol_upper) or 
            re.search(self.ENERGY_PATTERNS, symbol_upper) or
            'COMMODITY' in path_upper or 'COMMODITIES' in path_upper):
            subcategory = self.categorize_commodity(symbol_name)
            return "Commodities", subcategory, None, None
        
        # Try to parse as forex pair
        base, quote = self.extract_currency_pair(symbol_name)
        if base and quote:
            subcategory = self.categorize_forex(base, quote)
            return "Forex", subcategory, base, quote
        
        # Check path hints for forex
        if 'FOREX' in path_upper or 'CURRENCY' in path_upper or 'FX' in path_upper:
            return "Forex", "Unknown", None, None
        
        # Default to Other
        return "Other", "Unknown", None, None


class SymbolRetriever:
    """Retrieves and processes symbols from MT5."""
    
    def __init__(self, connection: MT5Connection, categorizer: SymbolCategorizer):
        self.connection = connection
        self.categorizer = categorizer
    
    def retrieve_all_symbols(self) -> List[SymbolInfo]:
        """
        Retrieve all tradable symbols from MT5.
        
        Returns:
            List of SymbolInfo objects
        """
        if not self.connection.connected:
            print("[ERROR] Not connected to MT5")
            return []
        
        # Get all symbols
        symbols = mt5.symbols_get()
        
        if symbols is None or len(symbols) == 0:
            print("[WARNING] No symbols retrieved")
            return []
        
        print(f"[INFO] Retrieved {len(symbols)} symbols from broker")
        
        symbol_infos = []
        
        for symbol in symbols:
            # Skip non-tradable symbols
            if not symbol.visible:
                continue
            
            # Categorize the symbol
            category, subcategory, base, quote = self.categorizer.categorize_symbol(
                symbol.name, 
                symbol.path
            )
            
            # Create SymbolInfo object
            symbol_info = SymbolInfo(
                name=symbol.name,
                description=symbol.description,
                category=category,
                subcategory=subcategory,
                base_currency=base,
                quote_currency=quote,
                digits=symbol.digits,
                trade_contract_size=symbol.trade_contract_size,
                volume_min=symbol.volume_min,
                volume_max=symbol.volume_max
            )
            
            symbol_infos.append(symbol_info)
        
        print(f"[INFO] Processed {len(symbol_infos)} tradable symbols")
        
        return symbol_infos


class DataExporter:
    """Exports symbol data to various formats (JSON, MessagePack)."""
    
    @staticmethod
    def _prepare_data(symbol_infos: List[SymbolInfo]) -> Dict:
        """
        Prepare data structure for export.
        
        Args:
            symbol_infos: List of SymbolInfo objects
            
        Returns:
            Dictionary with categorized data and metadata
        """
        # Group symbols by category and subcategory
        categorized = {}
        stats = {}
        
        for symbol_info in symbol_infos:
            category = symbol_info.category
            subcategory = symbol_info.subcategory
            
            # Initialize nested structure
            if category not in categorized:
                categorized[category] = {}
            if subcategory not in categorized[category]:
                categorized[category][subcategory] = []
            
            # Add symbol to appropriate category
            categorized[category][subcategory].append(asdict(symbol_info))
            
            # Update stats
            if category not in stats:
                stats[category] = {}
            stats[category][subcategory] = stats[category].get(subcategory, 0) + 1
        
        # Create final structure
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_symbols": len(symbol_infos),
                "statistics": stats
            },
            "symbols": categorized
        }
    
    @staticmethod
    def _print_summary(data: Dict):
        """Print export summary."""
        stats = data["metadata"]["statistics"]
        total = data["metadata"]["total_symbols"]
        
        print(f"\n[SUCCESS] Exported {total} symbols")
        print("\n=== SUMMARY ===")
        for category, subcategories in stats.items():
            print(f"\n{category}:")
            for subcategory, count in subcategories.items():
                print(f"  {subcategory}: {count}")
    
    @classmethod
    def _get_utils_output_path(cls, filename: str) -> Path:
        # Ensures outputs are written to the utils directory, regardless of the working dir
        utils_dir = UTILS_DIR
        utils_dir.mkdir(parents=True, exist_ok=True)
        return utils_dir / filename

    @classmethod
    def export_json(cls, symbol_infos: List[SymbolInfo], filename: str = "mt5_symbols.json"):
        """
        Export symbols to JSON file saved in the utils directory.
        
        Args:
            symbol_infos: List of SymbolInfo objects
            filename: Output filename
        """
        output = cls._prepare_data(symbol_infos)

        output_path = cls._get_utils_output_path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"[INFO] JSON file saved: {output_path} ({file_size:,} bytes, {file_size / 1024:.2f} KB)")

        cls._print_summary(output)

    @classmethod
    def export_msgpack(cls, symbol_infos: List[SymbolInfo], filename: str = "mt5_symbols.msgpack"):
        """
        Export symbols to MessagePack file (binary, more efficient than JSON) in the utils directory.
        
        Args:
            symbol_infos: List of SymbolInfo objects
            filename: Output filename
        """
        output = cls._prepare_data(symbol_infos)

        output_path = cls._get_utils_output_path(filename)
        with open(output_path, 'wb') as f:
            msgpack.pack(output, f, use_bin_type=True)
        
        file_size = output_path.stat().st_size
        print(f"[INFO] MessagePack file saved: {output_path} ({file_size:,} bytes, {file_size / 1024:.2f} KB)")

        cls._print_summary(output)

    @classmethod
    def export(cls, 
               symbol_infos: List[SymbolInfo], 
               format: Literal["json", "msgpack", "both"] = "msgpack",
               base_filename: str = "mt5_symbols"):
        """
        Export symbols to specified format(s) in the utils directory.
        
        Args:
            symbol_infos: List of SymbolInfo objects
            format: Export format - "json", "msgpack", or "both"
            base_filename: Base filename (without extension)
        """
        if format in ["json", "both"]:
            cls.export_json(symbol_infos, f"{base_filename}.json")
        
        if format in ["msgpack", "both"]:
            cls.export_msgpack(symbol_infos, f"{base_filename}.msgpack")


def main(export_format: Literal["json", "msgpack", "both"] = "msgpack"):
    """
    Main execution function.
    
    Args:
        export_format: Export format - "json", "msgpack" (default), or "both"
    """
    print("=" * 60)
    print("MetaTrader 5 Symbol Retriever & Categorizer")
    print("=" * 60)
    
    # Initialize connection
    connection = MT5Connection()
    
    try:
        # Connect to MT5
        if not connection.initialize():
            return
        
        # Validate connection
        if not connection.validate_connection():
            return
        
        # Initialize components
        categorizer = SymbolCategorizer()
        retriever = SymbolRetriever(connection, categorizer)
        
        # Retrieve symbols
        print("[INFO] Retrieving symbols...")
        symbol_infos = retriever.retrieve_all_symbols()
        
        if not symbol_infos:
            print("[ERROR] No symbols to export")
            return
        
        # Export to specified format(s)
        print(f"[INFO] Exporting to {export_format.upper()} format...")
        exporter = DataExporter()
        exporter.export(symbol_infos, format=export_format, base_filename="mt5_symbols")
        
        print("\n[INFO] Process completed successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always cleanup connection
        connection.shutdown()
        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
