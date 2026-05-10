import requests
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.enabled = len(self.token) > 0 and len(self.chat_id) > 0

    def send_message(self, message):
        """Sends a text message to the configured Telegram chat."""
        if not self.enabled:
            return
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"🤖 *Finter Alert*\n\n{message}",
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.error(f"Telegram Failed: {response.text}")
        except Exception as e:
            logger.error(f"Telegram Notifier Crash: {e}")

    def send_trade_alert(self, signal_type, symbol, lots, sl, tp, rr):
        """Specifically formatted trade alert."""
        msg = (
            f"✅ *TRADE OPENED*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📈 *Symbol:* {symbol}\n"
            f"⚡ *Type:* {signal_type}\n"
            f"📦 *Lots:* {lots}\n"
            f"🛡️ *SL:* {sl}\n"
            f"🎯 *TP:* {tp}\n"
            f"📊 *RR:* {rr}\n"
        )
        self.send_message(msg)

    def send_status_report(self, balance, win_rate, pnl):
        """Periodic status update for monitoring."""
        msg = (
            f"📊 *DAILY STATUS REPORT*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 *Balance:* ${balance}\n"
            f"🏆 *Win Rate:* {win_rate}%\n"
            f"💵 *Net PNL:* ${pnl}\n"
            f"🟢 *Status:* System Healthy"
        )
        self.send_message(msg)
