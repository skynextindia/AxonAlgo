from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = TradingDatabase()

# --- NEXT LEVEL COMMAND CENTER UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AXON | Next Level Command</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;900&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #010409; --panel: rgba(13, 17, 23, 0.8); --border: rgba(255, 255, 255, 0.05); }
        body { background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }
        .glass { background: var(--panel); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 1rem; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .neon-glow { box-shadow: 0 0 20px rgba(59, 130, 246, 0.15); }
        .log-window { background: #000; border: 1px solid #161b22; height: 200px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 1rem; color: #8b949e; }
        .btn-action { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
        .btn-action:hover { transform: translateY(-2px); filter: brightness(1.2); }
    </style>
</head>
<body class="p-6 md:p-12">
    <div class="max-w-[1600px] mx-auto">
        <!-- HEADER -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
            <div class="flex items-center gap-5">
                <div class="w-14 h-14 bg-gradient-to-tr from-blue-700 to-indigo-800 rounded-2xl flex items-center justify-center font-black text-3xl italic shadow-2xl shadow-blue-500/20">A</div>
                <div>
                    <h1 class="text-3xl font-black tracking-tighter uppercase italic leading-none mb-2">AxonAlgo <span class="text-blue-500">NextGen</span></h1>
                    <div class="flex items-center gap-3 text-[10px] mono font-bold text-slate-500 uppercase tracking-widest">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        Neural Core Connected
                    </div>
                </div>
            </div>
            <div class="flex gap-4 w-full md:w-auto">
                <div class="glass px-6 py-3 flex flex-col justify-center">
                    <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Global PNL</span>
                    <span class="text-xl font-black text-emerald-400 italic">${{ metrics.total_pnl }}</span>
                </div>
                <a href="/logout" class="glass px-6 py-3 flex items-center justify-center text-[10px] font-black uppercase tracking-widest hover:bg-red-500/10 transition-colors">Exit</a>
            </div>
        </header>

        <div class="grid grid-cols-1 xl:grid-cols-4 gap-8">
            <!-- LEFT: CONTROLS -->
            <div class="xl:col-span-1 space-y-8">
                <div class="glass p-8 neon-glow">
                    <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-8 text-blue-500">Core Parameters</h3>
                    <form action="/update" method="POST" class="space-y-6">
                        <div>
                            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Trading State</label>
                            <select name="trading_enabled" class="w-full bg-black/50 border border-white/10 p-4 rounded-xl font-bold text-xs">
                                <option value="True" {{ 'selected' if settings.trading_enabled }}>AUTH_EXECUTE_LIVE</option>
                                <option value="False" {{ 'selected' if not settings.trading_enabled }}>AUTH_READ_ONLY</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Risk Exposure (%)</label>
                            <input type="number" step="0.1" name="risk_pct" value="{{ settings.risk_pct }}" class="w-full bg-black/50 border border-white/10 p-4 rounded-xl font-bold">
                        </div>
                        <input type="hidden" name="symbols" value="{{ settings.symbols }}">
                        <button type="submit" class="w-full bg-blue-600 p-4 rounded-xl font-black text-xs uppercase tracking-widest btn-action shadow-xl shadow-blue-500/20">Sync Global State</button>
                    </form>
                </div>

                <div class="glass p-8">
                    <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-6 text-slate-400">Asset Management</h3>
                    <div class="space-y-3 mb-6 max-h-[200px] overflow-y-auto pr-2">
                        {% for sym in active_symbols %}
                        <div class="flex justify-between items-center bg-white/5 p-3 rounded-lg group">
                            <span class="text-[11px] mono font-bold">{{ sym }}</span>
                            <a href="/remove_symbol/{{ sym }}" class="text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">✕</a>
                        </div>
                        {% endfor %}
                    </div>
                    <form action="/add_symbol" method="POST" class="flex gap-2">
                        <input type="text" name="symbol" placeholder="BTCUSDm..." class="flex-1 bg-black/50 border border-white/10 p-3 rounded-lg text-xs font-bold uppercase">
                        <button class="bg-white/10 px-4 rounded-lg font-black">+</button>
                    </form>
                </div>
            </div>

            <!-- CENTER: LIVE MATRIX -->
            <div class="xl:col-span-3 space-y-8">
                <!-- LIVE PRICE TILES -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {% for sym_data in live_data %}
                    <div class="glass p-6 relative overflow-hidden">
                        <div class="flex justify-between items-start mb-4">
                            <span class="text-xs font-black tracking-tighter text-blue-400 uppercase">{{ sym_data.symbol }}</span>
                            <span class="text-[9px] mono text-slate-600">LIVE_TICK</span>
                        </div>
                        <div class="flex items-end gap-2">
                            <span class="text-3xl font-black italic tracking-tighter">{{ sym_data.price }}</span>
                            <span class="text-[10px] mb-1 {{ 'text-emerald-400' if sym_data.spread < 20 else 'text-yellow-400' }}">S: {{ sym_data.spread }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <!-- ORDERS & LOGS -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="glass p-8">
                        <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-6 text-emerald-400">Execution Stream</h3>
                        <div class="overflow-x-auto">
                            <table class="w-full text-[10px] mono text-left">
                                <thead class="text-slate-600 border-b border-white/5">
                                    <tr>
                                        <th class="pb-3 uppercase">Ticket</th>
                                        <th class="pb-3 uppercase">Asset</th>
                                        <th class="pb-3 uppercase">Profit</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-white/5">
                                    {% for pos in positions %}
                                    <tr>
                                        <td class="py-3">#{{ pos.ticket }}</td>
                                        <td class="py-3 font-bold">{{ pos.symbol }}</td>
                                        <td class="py-3 text-right {{ 'text-emerald-400' if pos.profit > 0 else 'text-red-400' }} font-bold">
                                            {{ '+' if pos.profit > 0 }}{{ pos.profit }}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="glass p-8">
                        <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-6 text-slate-400">System Terminal</h3>
                        <div class="log-window" id="log-stream">
                            {% for log in logs %}
                            <p class="mb-1">{{ log }}</p>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-12 py-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center text-[10px] text-slate-600 mono font-black tracking-[0.3em] gap-4">
            <div>AXON ALGO NEXTGEN &copy; 2026 // NODE_ACTIVE</div>
            <div class="flex gap-10">
                <div class="flex items-center gap-2">
                    <span class="text-slate-700">MT5:</span> <span class="text-blue-500">ENCRYPTED_AUTH</span>
                </div>
                <div id="clock">00:00:00 UTC</div>
            </div>
        </footer>
    </div>

    <script>
        setInterval(() => {
            const now = new Date();
            document.getElementById('clock').textContent = now.toISOString().split('T')[1].split('.')[0] + ' UTC';
        }, 1000);
        
        // Auto-refresh data every 5 seconds
        setTimeout(() => { location.reload(); }, 5000);
        
        const logWindow = document.getElementById('log-stream');
        logWindow.scrollTop = logWindow.scrollHeight;
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
    settings = db.get_system_settings()
    active_symbols = settings['symbols'].split(',')
    
    # Live Data Matrix
    live_data = []
    positions = []
    if mt5.initialize():
        for sym in active_symbols:
            tick = mt5.symbol_info_tick(sym)
            info = mt5.symbol_info(sym)
            if tick and info:
                live_data.append({
                    "symbol": sym,
                    "price": tick.bid,
                    "spread": round((tick.ask - tick.bid) / (info.point * 10), 1)
                })
        
        res = mt5.positions_get()
        if res:
            for p in res:
                positions.append({"ticket": p.ticket, "symbol": p.symbol, "profit": round(p.profit, 2)})
    
    # Read last 20 logs
    logs = []
    if os.path.exists("axon_bot.log"):
        with open("axon_bot.log", "r") as f:
            logs = f.readlines()[-20:]
            
    return render_template_string(HTML_TEMPLATE, metrics=metrics, settings=settings, 
                                 active_symbols=active_symbols, live_data=live_data, 
                                 positions=positions, logs=logs)

@app.route('/update', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    db.update_system_settings(float(request.form['risk_pct']), request.form['trading_enabled'] == 'True', request.form['symbols'])
    return redirect(url_for('dashboard'))

@app.route('/add_symbol', methods=['POST'])
def add_symbol():
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = settings['symbols'].split(',')
    new_sym = request.form['symbol'].strip()
    if new_sym and new_sym not in syms:
        syms.append(new_sym)
        db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

@app.route('/remove_symbol/<symbol>')
def remove_symbol(symbol):
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = settings['symbols'].split(',')
    if symbol in syms:
        syms.remove(symbol)
        db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
