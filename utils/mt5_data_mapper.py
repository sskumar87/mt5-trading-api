"""
MT5 Historical Orders Data Mapper

This module provides mapping functions to convert numeric codes from MT5 historical orders
to meaningful text descriptions.

Based on MT5 API documentation and TradeOrder structure:
dict_keys(['ticket', 'time_setup', 'time_setup_msc', 'time_done', 'time_done_msc', 
'time_expiration', 'type', 'type_time', 'type_filling', 'state', 'magic', 
'position_id', 'position_by_id', 'reason', 'volume_initial', 'volume_current', 
'price_open', 'sl', 'tp', 'price_current', 'price_stoplimit', 'symbol', 
'comment', 'external_id'])
"""

from typing import Dict, Any, Optional
from datetime import datetime
try:
    import pandas as pd
except ImportError:
    # Mock pandas functionality if not available
    class pd:
        @staticmethod
        def to_datetime(data, unit=None):
            if unit == "s":
                return [datetime.fromtimestamp(t) for t in data]
            return data

class MT5OrderDataMapper:
    """Data mapper for MT5 historical order fields"""
    
    # Order Types Mapping
    ORDER_TYPES = {
        0: "BUY",
        1: "SELL", 
        2: "BUY_LIMIT",
        3: "SELL_LIMIT",
        4: "BUY_STOP",
        5: "SELL_STOP",
        6: "BUY_STOP_LIMIT",
        7: "SELL_STOP_LIMIT"
    }
    
    # Order States Mapping
    ORDER_STATES = {
        0: "STARTED",           # Order checked, but not yet accepted by broker
        1: "PLACED",            # Order accepted
        2: "CANCELED",          # Order canceled by client
        3: "PARTIAL",           # Order partially executed
        4: "FILLED",            # Order fully executed
        5: "REJECTED",          # Order rejected
        6: "EXPIRED",           # Order expired
        7: "REQUEST_ADD",       # Order is being registered (placing to trading system)
        8: "REQUEST_MODIFY",    # Order is being modified (changing its parameters)
        9: "REQUEST_CANCEL"     # Order is being deleted (deleting from trading system)
    }
    
    # Order Reasons Mapping
    ORDER_REASONS = {
        0: "CLIENT",            # Order placed manually
        1: "MOBILE",            # Order placed from mobile application
        2: "WEB",               # Order placed from web platform
        3: "EXPERT",            # Order placed by Expert Advisor or script
        4: "DEALER",            # Order placed by dealer
        5: "SIGNAL"             # Order placed as a result of Signal service
    }
    
    # Order Time Types Mapping
    ORDER_TIME_TYPES = {
        0: "GTC",               # Good till cancel
        1: "DAY",               # Good till current trading day
        2: "SPECIFIED",         # Good till specified date
        3: "SPECIFIED_DAY"      # Good till specified day
    }
    
    # Order Filling Types Mapping
    ORDER_FILLING_TYPES = {
        0: "FOK",               # Fill or Kill
        1: "IOC",               # Immediate or Cancel
        2: "RETURN"             # Return (used for market orders)
    }
    
    @classmethod
    def map_order_type(cls, order_type: int) -> str:
        """Map order type code to text"""
        return cls.ORDER_TYPES.get(order_type, f"UNKNOWN_TYPE_{order_type}")
    
    @classmethod
    def map_order_state(cls, state: int) -> str:
        """Map order state code to text"""
        return cls.ORDER_STATES.get(state, f"UNKNOWN_STATE_{state}")
    
    @classmethod
    def map_order_reason(cls, reason: int) -> str:
        """Map order reason code to text"""
        return cls.ORDER_REASONS.get(reason, f"UNKNOWN_REASON_{reason}")
    
    @classmethod
    def map_time_type(cls, time_type: int) -> str:
        """Map order time type code to text"""
        return cls.ORDER_TIME_TYPES.get(time_type, f"UNKNOWN_TIME_TYPE_{time_type}")
    
    @classmethod
    def map_filling_type(cls, filling_type: int) -> str:
        """Map order filling type code to text"""
        return cls.ORDER_FILLING_TYPES.get(filling_type, f"UNKNOWN_FILLING_{filling_type}")
    
    @classmethod
    def format_timestamp(cls, timestamp: int, timezone_convert: bool = True) -> str:
        """
        Convert Unix timestamp to readable datetime string with timezone conversion
        
        Args:
            timestamp: Unix timestamp in seconds
            timezone_convert: Whether to apply timezone conversion logic from ranges service
            
        Returns:
            Formatted datetime string
        """
        if timestamp == 0:
            return "Not set"
        try:
            if timezone_convert:
                # Apply the same timezone conversion logic as in ranges service
                try:
                    from services.mt5_service import mt5_service
                    
                    # Convert timestamp to pandas datetime
                    dt_utc = pd.to_datetime([timestamp], unit="s")[0]
                    
                    # Localize to broker timezone then convert to local timezone
                    dt_broker = dt_utc.tz_localize(mt5_service.BROKER_TZ)  # Localize MT5 broker time
                    dt_local = dt_broker.tz_convert(mt5_service.LOCAL_TZ)  # Convert to Australia/Sydney
                    
                    return dt_local.strftime("%Y-%m-%d %H:%M:%S %Z")
                except Exception:
                    # Fallback to simple conversion if timezone conversion fails
                    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            return f"Invalid timestamp: {timestamp}"
    
    @classmethod
    def convert_order_timestamps(cls, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert all timestamp fields in order data using timezone conversion logic
        
        Args:
            order_data: Order data dict containing timestamp fields
            
        Returns:
            Dict with converted timezone-aware timestamps
        """
        timestamp_fields = ['time_setup', 'time_done', 'time_expiration']
        converted_data = order_data.copy()
        
        for field in timestamp_fields:
            if field in converted_data and converted_data[field] != 0:
                try:
                    from services.mt5_service import mt5_service
                    
                    # Convert using same logic as ranges service
                    timestamp = converted_data[field]
                    dt_utc = pd.to_datetime([timestamp], unit="s")[0]
                    dt_broker = dt_utc.tz_localize(mt5_service.BROKER_TZ)  # Localize MT5 broker time  
                    dt_local = dt_broker.tz_convert(mt5_service.LOCAL_TZ)   # Convert to Australia/Sydney
                    
                    # Store both original and converted timestamps
                    converted_data[f"{field}_local"] = dt_local
                    converted_data[field] = dt_local.strftime('%d-%m-%Y %H:%M')
                    
                except Exception as e:
                    # Fallback if timezone conversion fails
                    converted_data[f"{field}_formatted"] = cls.format_timestamp(converted_data[field], False)
        
        return converted_data
    
    @classmethod
    def extract_sl_tp_from_comment(cls, comment: str) -> Dict[str, Any]:
        """
        Extract SL/TP values from comment field like '[tp 3471.04]' '[sl 3478.04]'
        
        Args:
            comment: Comment string from order
            
        Returns:
            Dict with extracted sl, tp values and processed comment
        """
        import re
        
        result = {
            'sl_from_comment': None,
            'tp_from_comment': None,
            'comment_processed': comment if comment else "MC"
        }
        
        if not comment or comment == "None":
            return result
        
        # Extract TP values - look for [tp value] or [TP value]
        tp_pattern = r'\[tp\s+([\d.]+)\]'
        tp_match = re.search(tp_pattern, comment, re.IGNORECASE)
        if tp_match:
            try:
                result['tp_from_comment'] = float(tp_match.group(1))
            except ValueError:
                pass
        
        # Extract SL values - look for [sl value] or [SL value]  
        sl_pattern = r'\[sl\s+([\d.]+)\]'
        sl_match = re.search(sl_pattern, comment, re.IGNORECASE)
        if sl_match:
            try:
                result['sl_from_comment'] = float(sl_match.group(1))
            except ValueError:
                pass
        
        return result

    @classmethod
    def map_order_complete(cls, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete mapping of order data with all numeric codes converted to text
        
        Args:
            order_data: Raw order data from MT5 history_orders_get()
            
        Returns:
            Dict with mapped fields and original data preserved
        """
        if not isinstance(order_data, dict):
            # Handle MT5 order object - convert to dict first
            if hasattr(order_data, '_asdict'):
                order_data = order_data._asdict()
            else:
                # Try to convert object attributes to dict
                order_data = {attr: getattr(order_data, attr) for attr in dir(order_data) 
                             if not attr.startswith('_') and not callable(getattr(order_data, attr))}
        
        # First apply timezone conversion to all timestamps
        mapped_order = cls.convert_order_timestamps(order_data)
        
        # Extract SL/TP from comment field
        comment_data = cls.extract_sl_tp_from_comment(order_data.get('comment', ''))
        
        # Add mapped fields
        mapped_order.update({
            # Order identification and timing (timezone-aware timestamps already added by convert_order_timestamps)
            'ticket_str': str(order_data.get('ticket', 'N/A')),
            
            # Order type and characteristics
            'type_text': cls.map_order_type(order_data.get('type', -1)),
            'state_text': cls.map_order_state(order_data.get('state', -1)),
            'reason_text': cls.map_order_reason(order_data.get('reason', -1)),
            'time_type_text': cls.map_time_type(order_data.get('type_time', -1)),
            'filling_type_text': cls.map_filling_type(order_data.get('type_filling', -1)),
            
            # Volume and pricing information
            'volume_executed': order_data.get('volume_initial', 0) - order_data.get('volume_current', 0),
            'is_fully_executed': order_data.get('volume_current', 0) == 0 and order_data.get('volume_initial', 0) > 0,
            'execution_percentage': (
                ((order_data.get('volume_initial', 0) - order_data.get('volume_current', 0)) / order_data.get('volume_initial', 1)) * 100
                if order_data.get('volume_initial', 0) > 0 else 0
            ),
            
            # Order direction
            'direction': 'BUY' if order_data.get('type', -1) in [0, 2, 4, 6] else 'SELL',
            'is_pending': order_data.get('type', -1) in [2, 3, 4, 5, 6, 7],
            'is_market_order': order_data.get('type', -1) in [0, 1],
            
            # Status flags
            'has_stop_loss': order_data.get('sl', 0) > 0,
            'has_take_profit': order_data.get('tp', 0) > 0,
            'has_expiration': order_data.get('time_expiration', 0) > 0,
            
            # Order source summary
            'order_source_summary': f"{cls.map_order_reason(order_data.get('reason', -1))} - {cls.map_order_type(order_data.get('type', -1))} - {cls.map_order_state(order_data.get('state', -1))}",
            
            # Comment processing and SL/TP extraction
            'comment_processed': comment_data['comment_processed'],
            'sl_from_comment': comment_data['sl_from_comment'],
            'tp_from_comment': comment_data['tp_from_comment'],
            'sl_effective': comment_data['sl_from_comment'] if comment_data['sl_from_comment'] is not None else order_data.get('sl', 0),
            'tp_effective': comment_data['tp_from_comment'] if comment_data['tp_from_comment'] is not None else order_data.get('tp', 0)
        })
        
        return mapped_order
    
    @classmethod
    def map_orders_list(cls, orders_list: list) -> list:
        """
        Map a list of orders with complete field mapping
        
        Args:
            orders_list: List of order objects/dicts from MT5
            
        Returns:
            List of mapped orders
        """
        return [cls.map_order_complete(order) for order in orders_list]
    
    @classmethod
    def get_order_summary(cls, order_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of an order
        
        Args:
            order_data: Order data (mapped or unmapped)
            
        Returns:
            String summary of the order
        """
        ticket = order_data.get('ticket', 'Unknown')
        symbol = order_data.get('symbol', 'Unknown')
        order_type = cls.map_order_type(order_data.get('type', -1))
        state = cls.map_order_state(order_data.get('state', -1))
        volume = order_data.get('volume_initial', 0)
        
        setup_time = cls.format_timestamp(order_data.get('time_setup', 0))
        
        return f"Order #{ticket}: {order_type} {volume} lots of {symbol} - Status: {state} (Created: {setup_time})"
    
    @classmethod
    def create_position_summaries(cls, orders_list: list) -> list:
        """
        Create position summaries by grouping orders with the same position_id
        
        Args:
            orders_list: List of mapped order objects
            
        Returns:
            List of position summary dictionaries
        """
        if not orders_list:
            return []
        
        # Group orders by position_id
        position_groups = {}
        for order in orders_list:
            position_id = order.get('position_id')
            if position_id and position_id != 0:  # Only process orders with valid position_ids
                if position_id not in position_groups:
                    position_groups[position_id] = []
                position_groups[position_id].append(order)
        
        position_summaries = []
        
        for position_id, orders in position_groups.items():
            if len(orders) < 2:  # Skip positions with only one order
                continue
                
            # Sort orders by time_setup to get chronological order
            orders_sorted = sorted(orders, key=lambda x: x.get('time_setup', 0))
            
            entry_order = orders_sorted[0]
            exit_order = orders_sorted[-1]
            
            # Determine position type from entry order
            position_type = entry_order.get('direction', 'UNKNOWN')
            symbol = entry_order.get('symbol', 'UNKNOWN')
            
            # Get prices
            entry_price = entry_order.get('price_open', 0)
            if entry_price == 0:  # If price_open is 0, use price_current
                entry_price = entry_order.get('price_current', 0)
            
            exit_price = exit_order.get('price_open', 0)
            if exit_price == 0:  # If price_open is 0, use price_current
                exit_price = exit_order.get('price_current', 0)
            
            # Calculate volume (should be the same for both orders in a complete position)
            volume = entry_order.get('volume_initial', 0)
            
            # Calculate profit/loss
            if position_type == "SELL":
                # For SELL positions: profit when price goes down (entry_price > exit_price)
                price_diff = entry_price - exit_price
            else:  # BUY
                # For BUY positions: profit when price goes up (exit_price > entry_price)
                price_diff = exit_price - entry_price
            
            # Calculate profit/loss (basic calculation - could be enhanced with contract sizes)
            profit_loss = price_diff * volume
            
            # Get timestamps
            entry_time = entry_order.get('time_setup_formatted', entry_order.get('time_setup', 'Unknown'))
            exit_time = exit_order.get('time_done_formatted', exit_order.get('time_done', 'Unknown'))
            
            # Determine if position was profitable
            is_profitable = profit_loss > 0
            
            position_summary = {
                'position_id': position_id,
                'symbol': symbol,
                'position_type': position_type,
                'volume': volume,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'price_difference': price_diff,
                'profit_loss': round(profit_loss, 2),
                'is_profitable': is_profitable,
                'duration_orders': len(orders),
                'entry_order_ticket': entry_order.get('ticket'),
                'exit_order_ticket': exit_order.get('ticket'),
                'entry_reason': entry_order.get('reason_text', 'UNKNOWN'),
                'exit_reason': exit_order.get('reason_text', 'UNKNOWN'),
                'exit_comment': exit_order.get('comment', ''),
                'orders': orders_sorted  # Include all orders for detailed analysis
            }
            
            position_summaries.append(position_summary)
        
        # Sort by entry time
        position_summaries.sort(key=lambda x: x.get('entry_time', ''))
        
        return position_summaries


# Create global instance for easy access
mt5_mapper = MT5OrderDataMapper()

# Convenience functions for direct access
def map_order_type(order_type: int) -> str:
    """Map order type code to text"""
    return mt5_mapper.map_order_type(order_type)

def map_order_state(state: int) -> str:
    """Map order state code to text"""
    return mt5_mapper.map_order_state(state)

def map_order_reason(reason: int) -> str:
    """Map order reason code to text"""
    return mt5_mapper.map_order_reason(reason)

def map_order_complete(order_data: Any) -> Dict[str, Any]:
    """Complete mapping of order data"""
    return mt5_mapper.map_order_complete(order_data)

def map_orders_list(orders_list: list) -> list:
    """Map a list of orders"""
    return mt5_mapper.map_orders_list(orders_list)

def get_order_summary(order_data: Dict[str, Any]) -> str:
    """Generate order summary"""
    return mt5_mapper.get_order_summary(order_data)

def create_position_summaries(orders_list: list) -> list:
    """Create position summaries from orders list"""
    return mt5_mapper.create_position_summaries(orders_list)