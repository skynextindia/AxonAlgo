from flask import Flask, render_template_string, request, redirect, url_for, session
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import os
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = TradingDatabase()

# --- ULTRA-PREMIUM INSTITUTIONAL UI (FORCE UPDATE v2) ---
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
        :root { --bg: #020617; --panel: rgba(15, 23, 42, 0.8); --border: rgba(255, 255, 255, 0.08); --neon: #3b82f6; }
        body { background-color: var(--bg); color: #f8fafc; font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
        .glass { background: var(--panel); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 1.5rem; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
        .neon-border { border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 0 20px rgba(59, 130, 246, 0.1); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .status-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .5; transform: scale(0.95); } }
        input, select { background: #000 !important; border: 1px solid var(--border) !important; color: white !important; transition: all 0.2s; }
        input:focus, select:focus { border-color: var(--neon) !important; box-shadow: 0 0 10px rgba(59, 130, 246, 0.2); }
    </style>
</head>
<body class="p-4 md:p-12 min-h-screen">
    <div class="max-w-7xl mx-auto">
        <!-- TOP NAV -->
        <nav class="flex justify-between items-center mb-16">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center font-black text-2xl italic shadow-2xl shadow-blue-500/20">A</div>
                <div>
                    <h1 class="text-2xl font-black tracking-tighter uppercase italic leading-none mb-1">AxonAlgo <span class="text-blue-500">Pro</span></h1>
                    <p class="text-[10px] text-slate-500 mono uppercase tracking-[0.3em] font-bold">Institutional Alpha v1.0.4</p>
                </div>
            </div>
            <div class="flex items-center gap-8">
                <div class="hidden md:flex items-center gap-3 text-[10px] mono font-bold">
                    <span class="w-2 h-2 bg-emerald-500 rounded-full status-pulse"></span>
                    <span class="text-slate-500 uppercase">Latency:</span> <span class="text-emerald-400">0.04ms</span>
                </div>
                <a href="/logout" class="bg-white/5 hover:bg-red-500/10 border border-white/10 px-5 py-2 rounded-full text-[10px] uppercase font-black tracking-widest transition-all">Terminate Session</a>
            </div>
        </nav>

        <!-- PERFORMANCE GRID -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
            <div class="glass p-8 relative overflow-hidden group hover:neon-border transition-all">
                <div class="absolute -right-6 -bottom-6 text-white/5 text-9xl font-black italic select-none">W</div>
                <p class="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-3">Alpha Win Rate</p>
                <h2 class="text-6xl font-black tracking-tighter">{{ metrics.win_rate }}<span class="text-2xl text-blue-500 ml-1">%</span></h2>
            </div>
            <div class="glass p-8 relative overflow-hidden group hover:neon-border transition-all">
                <div class="absolute -right-6 -bottom-6 text-white/5 text-9xl font-black italic select-none">P</div>
                <p class="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-3">Net Realized Alpha</p>
                <h2 class="text-6xl font-black tracking-tighter text-emerald-400 italic">${{ metrics.total_pnl }}</h2>
            </div>
            <div class="glass p-8 relative overflow-hidden group hover:neon-border transition-all">
                <p class="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-4">Market Exposure</p>
                <div class="flex gap-2 flex-wrap relative z-10">
                    {% for sym in settings.SYMBOLS %}
                    <span class="px-3 py-1.5 bg-white/5 border border-white/5 rounded-lg text-[10px] mono font-bold text-blue-400">{{ sym }}</span>
                    {% endfor %}
                </div>
            </div>
            <div class="glass p-8 flex flex-col justify-center border-l-4 border-l-blue-600">
                <p class="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-2">Operational Status</p>
                <h3 class="text-2xl font-black tracking-tighter {{ 'text-emerald-400' if settings.TRADING_ENABLED else 'text-blue-500' }}">
                    {{ 'SYSTEM_LIVE' if settings.TRADING_ENABLED else 'CORE_STANDBY' }}
                </h3>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
            <!-- CONTROL CENTER -->
            <div class="lg:col-span-1 space-y-6">
                <div class="glass p-10">
                    <h3 class="text-sm font-black uppercase tracking-widest mb-10 flex items-center gap-3">
                        <span class="w-8 h-8 bg-blue-600/10 rounded-lg flex items-center justify-center text-blue-500 text-lg italic">⚙</span>
                        Global Parameters
                    </h3>
                    <form action="/update" method="POST" class="space-y-8">
                        <div class="space-y-3">
                            <label class="text-[10px] text-slate-500 uppercase font-black tracking-widest">Authorization Protocol</label>
                            <select name="trading_enabled" class="w-full p-5 rounded-2xl font-bold text-xs uppercase tracking-widest focus:ring-4 ring-blue-600/20">
                                <option value="True" {{ 'selected' if settings.TRADING_ENABLED }}>[LEVEL_1] LIVE_EXECUTION</option>
                                <option value="False" {{ 'selected' if not settings.TRADING_ENABLED }}>[LEVEL_0] SCAN_ONLY_MODE</option>
                            </select>
                        </div>
                        <div class="space-y-3">
                            <label class="text-[10px] text-slate-500 uppercase font-black tracking-widest">Equity Exposure (%)</label>
                            <input type="number" step="0.01" name="risk_pct" value="{{ settings.RISK_PER_TRADE }}" class="w-full p-5 rounded-2xl font-bold text-lg focus:ring-4 ring-blue-600/20">
                        </div>
                        <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-indigo-700 hover:scale-[1.02] active:scale-[0.98] p-5 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-2xl shadow-blue-500/20 transition-all">Update Core Memory</button>
                    </form>
                </div>
            </div>

            <!-- LIVE POSITION FEED -->
            <div class="lg:col-span-2 glass p-12 overflow-hidden relative">
                <div class="flex justify-between items-center mb-10">
                    <h3 class="text-sm font-black uppercase tracking-widest flex items-center gap-3">
                        <span class="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-400 text-lg italic">◈</span>
                        Order Flow Matrix
                    </h3>
                    <span class="text-[10px] mono text-slate-500">REALTIME_STREAM_v2.0</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left mono text-[11px]">
                        <thead>
                            <tr class="text-slate-500 border-b border-white/5">
                                <th class="pb-6 font-black uppercase tracking-widest">Asset</th>
                                <th class="pb-6 font-black uppercase tracking-widest">Bias</th>
                                <th class="pb-6 font-black uppercase tracking-widest">Size</th>
                                <th class="pb-6 font-black uppercase tracking-widest text-right">Yield</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5">
                            {% if positions %}
                                {% for pos in positions %}
                                <tr class="group hover:bg-white/5 transition-colors">
                                    <td class="py-5 font-black text-slate-200 uppercase">{{ pos.symbol }}</td>
                                    <td class="py-5">
                                        <span class="px-2 py-1 rounded {{ 'bg-blue-500/10 text-blue-400' if pos.type == 0 else 'bg-red-500/10 text-red-400' }} font-black">
                                            {{ 'BULLISH' if pos.type == 0 else 'BEARISH' }}
                                        </span>
                                    </td>
                                    <td class="py-5 text-slate-400 font-bold">{{ pos.volume }} Lots</td>
                                    <td class="py-5 text-right {{ 'text-emerald-400' if pos.profit > 0 else 'text-red-400' }} font-black text-sm">
                                        {{ '+' if pos.profit > 0 }}{{ pos.profit }}
                                    </td>
                                </tr>
                                {% endfor %}
                            {% else %}
                                <tr>
                                    <td colspan="4" class="py-20 text-center">
                                        <p class="text-slate-600 italic uppercase tracking-[0.3em] font-black text-xs mb-2">Neutral Exposure State</p>
                                        <p class="text-[9px] text-slate-700 uppercase tracking-widest">Waiting for Signal Penetration</p>
                                    </td>
                                </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer class="mt-16 py-8 border-t border-white/5 flex justify-between items-center text-[9px] text-slate-600 mono uppercase tracking-[0.4em] font-bold">
            <div>Institutional Command Terminal &copy; 2026 AXON ALGO</div>
            <div class="flex gap-8">
                <div>CORE_SYNC: <span class="text-emerald-500">100%</span></div>
                <div>UTC: <span id="utc-clock" class="text-slate-300">00:00:00</span></div>
            </div>
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
    <style>body { background: #010409; color: white; -webkit-font-smoothing: antialiased; }</style>
</head>
<body class="flex items-center justify-center h-screen bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-black to-black">
    <div class="w-full max-w-sm p-12 rounded-[2.5rem] bg-slate-900/40 border border-white/10 backdrop-blur-2xl shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50"></div>
        <div class="mb-12 text-center">
            <h1 class="text-3xl font-black italic tracking-tighter uppercase mb-2">Axon<span class="text-blue-500">Algo</span></h1>
            <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Secure Terminal Access</p>
        </div>
        <form action="/login" method="POST" class="space-y-8">
            <div class="relative group">
                <input type="password" name="password" required placeholder="PROTOCOL_KEY" class="w-full bg-black/60 border border-white/10 p-5 rounded-2xl text-center text-xl tracking-[0.5em] outline-none focus:border-blue-600 focus:ring-4 ring-blue-600/10 transition-all font-black">
            </div>
            <button class="w-full bg-blue-600 hover:bg-blue-500 p-5 rounded-2xl font-black text-[11px] uppercase tracking-[0.3em] shadow-2xl shadow-blue-500/20 active:scale-95 transition-all">Authorize Entry</button>
        </form>
        {% if error %}<p class="text-red-500 text-[10px] mt-8 text-center font-black uppercase tracking-[0.2em]">{{ error }}</p>{% endif %}
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
        return render_template_string(LOGIN_TEMPLATE, error="Invalid Access Protocol")
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
