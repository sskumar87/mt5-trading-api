from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class Instrument:
    symbol: str
    range: float  # attribute name 'range' is fine here (doesn't affect builtin range())

class InstrumentConstants:
    """Constants for trading instruments and their range sizes"""
    
    INSTRUMENT_MAP: Dict[str, Instrument] = {
        "XAUUSD": Instrument("XAUUSD+", 1.5),
        "BTCUSD": Instrument("BTCUSD", 50),
        "ETHUSD": Instrument("ETHUSD", 5),
        "NAS100": Instrument("NAS100", 5),
        "GBPUSD": Instrument("GBPUSD+", 0.00030),
        "EURUSD": Instrument("EURUSD+", 0.00030),
        "USDJPY": Instrument("USDJPY+", 0.003),
    }
    
    @classmethod
    def get_instrument(cls, symbol: str) -> Instrument:
        """Get instrument by symbol key"""
        return cls.INSTRUMENT_MAP.get(symbol.upper())
    
    @classmethod
    def get_all_symbols(cls) -> list[str]:
        """Get all available symbol keys"""
        return list(cls.INSTRUMENT_MAP.keys())
    
    @classmethod
    def get_range_size(cls, symbol: str) -> float:
        """Get range size for a symbol with fallback logic"""
        symbol_upper = symbol.upper().strip()
        
        # Direct match first
        if symbol_upper in cls.INSTRUMENT_MAP:
            return cls.INSTRUMENT_MAP[symbol_upper].range
        
        # Try without + suffix
        base_symbol = symbol_upper.rstrip('+')
        if base_symbol in cls.INSTRUMENT_MAP:
            return cls.INSTRUMENT_MAP[base_symbol].range
        
        # Try with + suffix
        plus_symbol = base_symbol + '+'
        if plus_symbol in cls.INSTRUMENT_MAP:
            return cls.INSTRUMENT_MAP[plus_symbol].range
        
        # Fallback pattern matching
        for key, instrument in cls.INSTRUMENT_MAP.items():
            if key.rstrip('+') == base_symbol:
                return instrument.range
        
        return 1.0  # Default range size