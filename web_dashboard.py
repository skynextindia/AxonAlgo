from flask import Flask, render_template_string, request, redirect, url_for, session
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import os
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = TradingDatabase()

# --- ULTRA-PREMIUM INSTITUTIONAL UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AXON | Institutional Command</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #030712; --panel: rgba(17, 24, 39, 0.7); --border: rgba(255, 255, 255, 0.1); --neon: #3b82f6; }
        body { background-color: var(--bg); color: #f1f5f9; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass { background: var(--panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 1.5rem; }
        .neon-text { text-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .status-pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
        input, select { background: rgba(0,0,0,0.3) !important; border: 1px solid var(--border) !important; color: white !important; }
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-7xl mx-auto">
        <!-- TOP NAV -->
        <nav class="flex justify-between items-center mb-10 px-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-black text-xl italic shadow-[0_0_20px_rgba(37,99,235,0.4)]">A</div>
                <div>
                    <h1 class="text-xl font-extrabold tracking-tighter uppercase italic">AxonAlgo <span class="text-blue-500">Pro</span></h1>
                    <p class="text-[10px] text-slate-500 mono uppercase tracking-widest">Institutional Grade v1.0.2</p>
                </div>
            </div>
            <div class="flex items-center gap-6">
                <div class="flex items-center gap-2 text-xs mono">
                    <span class="w-2 h-2 bg-emerald-500 rounded-full status-pulse shadow-[0_0_8px_#10b981]"></span>
                    SERVER: <span class="text-slate-300">CORE_ACTIVE</span>
                </div>
                <a href="/logout" class="text-xs hover:text-red-400 transition-colors uppercase font-bold tracking-tighter">Exit Terminal</a>
            </div>
        </nav>

        <!-- PERFORMANCE GRID -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
            <div class="glass p-8 relative overflow-hidden group">
                <div class="absolute -right-4 -bottom-4 text-blue-500/5 text-8xl font-black italic">WIN</div>
                <p class="text-xs text-slate-500 uppercase font-bold tracking-widest mb-2">Alpha Win Rate</p>
                <h2 class="text-5xl font-black neon-text">{{ metrics.win_rate }}<span class="text-xl text-blue-500">%</span></h2>
            </div>
            <div class="glass p-8 relative overflow-hidden">
                <div class="absolute -right-4 -bottom-4 text-emerald-500/5 text-8xl font-black italic">PNL</div>
                <p class="text-xs text-slate-500 uppercase font-bold tracking-widest mb-2">Net Realized PNL</p>
                <h2 class="text-5xl font-black text-emerald-400 italic">${{ metrics.total_pnl }}</h2>
            </div>
            <div class="glass p-8">
                <p class="text-xs text-slate-500 uppercase font-bold tracking-widest mb-2">Active Assets</p>
                <div class="flex gap-2 flex-wrap">
                    {% for sym in settings.SYMBOLS %}
                    <span class="px-2 py-1 bg-slate-800 rounded text-[10px] mono text-blue-300">{{ sym }}</span>
                    {% endfor %}
                </div>
            </div>
            <div class="glass p-8 flex flex-col justify-center border-l-4 border-l-blue-600">
                <p class="text-xs text-slate-500 uppercase font-bold tracking-widest mb-1">Authorization</p>
                <h3 class="text-xl font-black {{ 'text-emerald-400' if settings.TRADING_ENABLED else 'text-red-400' }}">
                    {{ 'SYSTEM_LIVE' if settings.TRADING_ENABLED else 'SCAN_ONLY' }}
                </h3>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
            <!-- CONTROL CENTER -->
            <div class="lg:col-span-1 space-y-6">
                <div class="glass p-8 shadow-2xl">
                    <h3 class="text-lg font-bold mb-8 flex items-center gap-2">
                        <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                        Global Parameters
                    </h3>
                    <form action="/update" method="POST" class="space-y-6">
                        <div class="space-y-2">
                            <label class="text-[10px] text-slate-500 uppercase font-black tracking-widest">Execution Mode</label>
                            <select name="trading_enabled" class="w-full p-4 rounded-xl focus:ring-2 ring-blue-500">
                                <option value="True" {{ 'selected' if settings.TRADING_ENABLED }}>[LIVE] AUTH_EXECUTE</option>
                                <option value="False" {{ 'selected' if not settings.TRADING_ENABLED }}>[SCAN] READ_ONLY</option>
                            </select>
                        </div>
                        <div class="space-y-2">
                            <label class="text-[10px] text-slate-500 uppercase font-black tracking-widest">Equity Risk (%)</label>
                            <input type="number" step="0.01" name="risk_pct" value="{{ settings.RISK_PER_TRADE }}" class="w-full p-4 rounded-xl focus:ring-2 ring-blue-500">
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 p-5 rounded-xl font-black text-sm uppercase tracking-widest shadow-[0_0_30px_rgba(37,99,235,0.2)] transition-all active:scale-95">Push Updates to Core</button>
                    </form>
                </div>
            </div>

            <!-- LIVE POSITION FEED -->
            <div class="lg:col-span-2 glass p-10">
                <h3 class="text-lg font-bold mb-8 flex items-center gap-2">
                    <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                    Institutional Order Flow
                </h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left mono text-xs">
                        <thead>
                            <tr class="text-slate-500 border-b border-white/5">
                                <th class="pb-4 font-normal uppercase">Asset</th>
                                <th class="pb-4 font-normal uppercase">Type</th>
                                <th class="pb-4 font-normal uppercase">Volume</th>
                                <th class="pb-4 font-normal uppercase text-right">Profit</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5">
                            {% if positions %}
                                {% for pos in positions %}
                                <tr>
                                    <td class="py-4 font-bold">{{ pos.symbol }}</td>
                                    <td class="py-4 {{ 'text-blue-400' if pos.type == 0 else 'text-red-400' }}">
                                        {{ 'LONG' if pos.type == 0 else 'SHORT' }}
                                    </td>
                                    <td class="py-4">{{ pos.volume }}</td>
                                    <td class="py-4 text-right {{ 'text-emerald-400' if pos.profit > 0 else 'text-red-400' }} font-bold">
                                        {{ '+' if pos.profit > 0 }}{{ pos.profit }}
                                    </td>
                                </tr>
                                {% endfor %}
                            {% else %}
                                <tr>
                                    <td colspan="4" class="py-10 text-center text-slate-600 italic uppercase tracking-widest">No active market exposure</td>
                                </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer class="mt-10 py-6 border-t border-white/5 flex justify-between items-center text-[10px] text-slate-500 mono uppercase tracking-widest">
            <div>&copy; 2026 AXON ALGO TECHNOLOGIES</div>
            <div>UTC SYNC: <span id="utc-clock">00:00:00</span></div>
        </footer>
    </div>

    <script>
        function updateClock() {
            const now = new Date();
            document.getElementById('utc-clock').textContent = now.toISOString().split('T')[1].split('.')[0];
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>AXON | SECURITY</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: #010409; color: white; }</style>
</head>
<body class="flex items-center justify-center h-screen bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-black to-black">
    <div class="w-full max-w-sm p-10 rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-2xl">
        <div class="mb-10 text-center">
            <h1 class="text-2xl font-black italic tracking-tighter uppercase mb-2">Axon<span class="text-blue-500">Algo</span></h1>
            <p class="text-[9px] text-slate-500 uppercase tracking-widest font-bold">System Authorization Required</p>
        </div>
        <form action="/login" method="POST" class="space-y-6">
            <div class="relative">
                <input type="password" name="password" required placeholder="••••••••" class="w-full bg-black/40 border border-white/5 p-4 rounded-xl text-center text-xl tracking-[0.5em] outline-none focus:border-blue-600 transition-all">
            </div>
            <button class="w-full bg-blue-600 hover:bg-blue-500 p-4 rounded-xl font-black text-xs uppercase tracking-[0.2em] shadow-lg active:scale-95 transition-all">Authenticate</button>
        </form>
        {% if error %}<p class="text-red-500 text-[10px] mt-6 text-center font-bold uppercase tracking-widest">{{ error }}</p>{% endif %}
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
        return render_template_string(LOGIN_TEMPLATE, error="Authentication Failed")
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
        "RISK_PER_TRADE": Config.RISK_PER_TRADE,
        "SYMBOLS": Config.SYMBOLS
    }
    
    # Fetch live positions from MT5
    positions = []
    if mt5.initialize():
        res = mt5.positions_get()
        if res:
            for p in res:
                positions.append({
                    "symbol": p.symbol,
                    "type": p.type,
                    "volume": p.volume,
                    "profit": round(p.profit, 2)
                })
    
    return render_template_string(HTML_TEMPLATE, metrics=metrics, settings=settings, positions=positions)

@app.route('/update', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    Config.TRADING_ENABLED = request.form['trading_enabled'] == 'True'
    Config.RISK_PER_TRADE = float(request.form['risk_pct'])
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
