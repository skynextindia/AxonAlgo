import MetaTrader5 as mt5
import datetime
import logging
import pytz

logger = logging.getLogger(__name__)

class NewsEngine:
    def __init__(self, buffer_minutes=60):
        """
        buffer_minutes: How many minutes before/after news to avoid trading.
        """
        self.buffer = buffer_minutes

    def get_upcoming_events(self, symbol):
        """
        Fetches High-Impact news events for the currencies associated with the symbol.
        """
        try:
            # Check if MT5 version supports calendar
            if not hasattr(mt5, 'calendar_events_get'):
                return []

            # 1. Determine relevant currencies (e.g., XAUUSD -> USD)
            currencies = self._get_symbol_currencies(symbol)
            
            # 2. Define Time Range (Current Day)
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            start_of_day = now_utc.replace(hour=0, minute=0, second=0)
            end_of_day = now_utc.replace(hour=23, minute=59, second=59)
            
            all_events = []
            for curr in currencies:
                events = mt5.calendar_events_get(
                    time_from=int(start_of_day.timestamp()),
                    time_to=int(end_of_day.timestamp()),
                    currency=curr,
                    importance=mt5.CALENDAR_IMPORTANCE_HIGH
                )
                if events:
                    all_events.extend(events)
            
            return all_events
        except Exception as e:
            # Silently fail if calendar is not supported by broker
            return []
 
    def is_volatile_now(self, symbol):
        """
        Checks if we are currently in a 'No-Trade' news window.
        """
        try:
            now_utc = datetime.datetime.now(datetime.timezone.utc).timestamp()
            events = self.get_upcoming_events(symbol)
            
            for event in events:
                # event.time is in UTC
                event_time = event.time
                window_start = event_time - (self.buffer * 60)
                window_end = event_time + (self.buffer * 60)
                
                if window_start <= now_utc <= window_end:
                    return True, event.name
            
            return False, None
        except Exception as e:
            logger.error(f"News Filter Error: {e}")
            return False, None

    def _get_symbol_currencies(self, symbol):
        """Extracts base and quote currencies from symbol name."""
        # Common MT5 pairs are 6 chars (EURUSD) or metals (XAUUSD)
        # This is a simplified mapper
        major_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]
        found = []
        for curr in major_currencies:
            if curr in symbol:
                found.append(curr)
        return found if found else ["USD"] # Default to USD if unknown
