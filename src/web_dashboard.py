from flask import Flask, render_template, request, redirect, url_for, jsonify
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import os

app = Flask(__name__)
db = TradingDatabase()

# Professional Dark UI Template (Embedded for simplicity)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AxonAlgo | Admin Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; }
        .card { background-color: #1e293b; border: 1px solid #334155; }
    </style>
</head>
<body class="p-8">
    <div class="max-w-6xl mx-auto">
        <header class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold text-blue-400">🚀 AxonAlgo Admin</h1>
            <div class="flex gap-4">
                <span class="px-4 py-2 rounded card text-sm">Status: <span class="text-green-400">ONLINE</span></span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="card p-6 rounded-xl text-center">
                <p class="text-gray-400 text-sm">Win Rate</p>
                <p class="text-4xl font-bold">{{ metrics.win_rate }}%</p>
            </div>
            <div class="card p-6 rounded-xl text-center">
                <p class="text-gray-400 text-sm">Total PNL</p>
                <p class="text-4xl font-bold text-green-400">${{ metrics.total_pnl }}</p>
            </div>
            <div class="card p-6 rounded-xl text-center">
                <p class="text-gray-400 text-sm">Trading Mode</p>
                <p class="text-2xl font-bold">{{ 'LIVE' if settings.TRADING_ENABLED else 'SCANNER ONLY' }}</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="card p-8 rounded-2xl">
                <h2 class="text-xl font-semibold mb-6">⚙️ Update Settings</h2>
                <form action="/update" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Trading Enabled</label>
                        <select name="trading_enabled" class="w-full bg-slate-900 border border-slate-700 p-2 rounded">
                            <option value="True" {{ 'selected' if settings.TRADING_ENABLED }}>TRUE</option>
                            <option value="False" {{ 'selected' if not settings.TRADING_ENABLED }}>FALSE</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Risk Per Trade (%)</label>
                        <input type="number" step="0.01" name="risk_pct" value="{{ settings.RISK_PER_TRADE }}" class="w-full bg-slate-900 border border-slate-700 p-2 rounded">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Target Symbol</label>
                        <input type="text" name="symbol" value="{{ settings.SYMBOL }}" class="w-full bg-slate-900 border border-slate-700 p-2 rounded">
                    </div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 py-2 rounded font-bold transition">SAVE SETTINGS</button>
                </form>
            </div>

            <div class="card p-8 rounded-2xl">
                <h2 class="text-xl font-semibold mb-6">📝 Recent Activity</h2>
                <div class="space-y-3 text-sm text-gray-300">
                    <p>• Bot heartbeart: System healthy</p>
                    <p>• H4 Trend Confirmation active</p>
                    <p>• Economic Calendar synced</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    metrics = db.get_metrics()
    settings = {
        "TRADING_ENABLED": Config.TRADING_ENABLED,
        "RISK_PER_TRADE": Config.RISK_PER_TRADE,
        "SYMBOL": Config.SYMBOL
    }
    return render_template_string(HTML_TEMPLATE, metrics=metrics, settings=settings)

@app.route('/update', methods=['POST'])
def update_settings():
    # In a real app, we would write back to .env or a DB.
    # For now, we update the runtime Config
    Config.TRADING_ENABLED = request.form['trading_enabled'] == 'True'
    Config.RISK_PER_TRADE = float(request.form['risk_pct'])
    Config.SYMBOL = request.form['symbol']
    return redirect(url_for('dashboard'))

def render_template_string(template, **kwargs):
    from flask import render_template_string
    return render_template_string(template, **kwargs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
