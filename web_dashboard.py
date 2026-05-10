from flask import Flask, render_template_string, request, redirect, url_for, session
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # Secure random key for sessions
db = TradingDatabase()

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>AxonAlgo | Secure Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 flex items-center justify-center h-screen">
    <div class="bg-slate-900 p-8 rounded-2xl border border-slate-800 w-96 shadow-2xl">
        <h1 class="text-2xl font-bold text-blue-400 mb-6 text-center">🔐 Secure Login</h1>
        <form action="/login" method="POST" class="space-y-4">
            <input type="password" name="password" placeholder="Admin Password" class="w-full bg-slate-800 border border-slate-700 p-3 rounded text-white outline-none focus:border-blue-500">
            <button class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded font-bold transition text-white">ACCESS DASHBOARD</button>
        </form>
        {% if error %}<p class="text-red-500 text-xs mt-4 text-center">{{ error }}</p>{% endif %}
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AxonAlgo | Admin Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #020617; color: #f8fafc; }
        .card { background-color: #0f172a; border: 1px solid #1e293b; }
    </style>
</head>
<body class="p-8">
    <div class="max-w-6xl mx-auto">
        <header class="flex justify-between items-center mb-12">
            <h1 class="text-3xl font-bold text-blue-400">🚀 AxonAlgo Admin</h1>
            <div class="flex gap-4">
                <a href="/logout" class="text-xs text-slate-500 hover:text-white transition">Logout</a>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div class="card p-8 rounded-2xl text-center shadow-xl">
                <p class="text-slate-500 text-xs uppercase tracking-widest mb-2">Win Rate</p>
                <p class="text-5xl font-black">{{ metrics.win_rate }}%</p>
            </div>
            <div class="card p-8 rounded-2xl text-center shadow-xl">
                <p class="text-slate-500 text-xs uppercase tracking-widest mb-2">Total PNL</p>
                <p class="text-5xl font-black text-emerald-400">${{ metrics.total_pnl }}</p>
            </div>
            <div class="card p-8 rounded-2xl text-center shadow-xl">
                <p class="text-slate-500 text-xs uppercase tracking-widest mb-2">Bot Status</p>
                <p class="text-2xl font-bold text-blue-400">{{ 'LIVE TRADING' if settings.TRADING_ENABLED else 'SCANNER MODE' }}</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="card p-10 rounded-3xl shadow-2xl">
                <h2 class="text-xl font-semibold mb-8 flex items-center gap-2">
                    <span class="p-2 bg-blue-500/10 text-blue-400 rounded-lg">⚙️</span> Settings Control
                </h2>
                <form action="/update" method="POST" class="space-y-6">
                    <div>
                        <label class="block text-xs text-slate-500 uppercase font-bold mb-2">Trading Authorization</label>
                        <select name="trading_enabled" class="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl focus:ring-2 ring-blue-500 outline-none">
                            <option value="True" {{ 'selected' if settings.TRADING_ENABLED }}>ENABLED</option>
                            <option value="False" {{ 'selected' if not settings.TRADING_ENABLED }}>DISABLED</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-slate-500 uppercase font-bold mb-2">Risk Exposure (%)</label>
                        <input type="number" step="0.01" name="risk_pct" value="{{ settings.RISK_PER_TRADE }}" class="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl focus:ring-2 ring-blue-500 outline-none">
                    </div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 py-4 rounded-xl font-black text-sm uppercase tracking-widest shadow-lg transition-all active:scale-95">UPDATE SYSTEM</button>
                </form>
            </div>

            <div class="card p-10 rounded-3xl shadow-2xl border-l-4 border-l-blue-500">
                <h2 class="text-xl font-semibold mb-8 flex items-center gap-2">
                    <span class="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">🛡️</span> System Health
                </h2>
                <div class="space-y-4 text-sm">
                    <div class="flex justify-between p-3 bg-slate-950/50 rounded-lg">
                        <span class="text-slate-400">Multi-Symbol Engine</span>
                        <span class="text-emerald-400 font-bold">ACTIVE</span>
                    </div>
                    <div class="flex justify-between p-3 bg-slate-950/50 rounded-lg">
                        <span class="text-slate-400">News Filter Sync</span>
                        <span class="text-emerald-400 font-bold">HEALTHY</span>
                    </div>
                    <div class="flex justify-between p-3 bg-slate-950/50 rounded-lg">
                        <span class="text-slate-400">H4 Trend Alignment</span>
                        <span class="text-blue-400 font-bold">READY</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return render_template_string(LOGIN_TEMPLATE, error="Invalid Access Token")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    metrics = db.get_metrics()
    settings = {
        "TRADING_ENABLED": Config.TRADING_ENABLED,
        "RISK_PER_TRADE": Config.RISK_PER_TRADE
    }
    return render_template_string(HTML_TEMPLATE, metrics=metrics, settings=settings)

@app.route('/update', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    Config.TRADING_ENABLED = request.form['trading_enabled'] == 'True'
    Config.RISK_PER_TRADE = float(request.form['risk_pct'])
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
