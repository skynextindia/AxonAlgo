from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import os
import time

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
        body { background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass { background: var(--panel); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 1rem; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .neon-glow { box-shadow: 0 0 20px rgba(59, 130, 246, 0.15); }
        .log-window { background: #000; border: 1px solid #161b22; height: 250px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 1rem; color: #8b949e; }
        .price-up { color: #10b981; animation: pulse-up 0.5s ease-out; }
        .price-down { color: #ef4444; animation: pulse-down 0.5s ease-out; }
        @keyframes pulse-up { from { background: rgba(16, 185, 129, 0.1); } to { background: transparent; } }
        @keyframes pulse-down { from { background: rgba(239, 68, 68, 0.1); } to { background: transparent; } }
    </script>
</head>
<body class="p-6 md:p-12">
    <div class="max-w-[1600px] mx-auto">
        <!-- HEADER -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
            <div class="flex items-center gap-5">
                <div class="w-14 h-14 bg-gradient-to-tr from-blue-700 to-indigo-800 rounded-2xl flex items-center justify-center font-black text-3xl italic shadow-2xl shadow-blue-500/20">A</div>
                <div>
                    <h1 class="text-3xl font-black tracking-tighter uppercase italic leading-none mb-2">AxonAlgo <span class="text-blue-500 text-lg not-italic opacity-50 ml-2">PRO_CORE</span></h1>
                    <div class="flex items-center gap-3 text-[10px] mono font-bold text-slate-500 uppercase tracking-widest">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        Neural Connection: <span id="header-latency" class="text-emerald-400">0ms</span>
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-8">
                <div class="glass px-6 py-3 flex flex-col justify-center">
                    <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Global Account PNL</span>
                    <span id="global-pnl" class="text-xl font-black text-emerald-400 italic font-mono">$0.00</span>
                </div>
                <a href="/logout" class="bg-white/5 hover:bg-red-500/10 border border-white/10 px-6 py-3 rounded-xl text-[10px] uppercase font-black tracking-widest transition-all">Terminate Session</a>
            </div>
        </header>

        <div class="grid grid-cols-1 xl:grid-cols-4 gap-8">
            <!-- LEFT: CONTROLS -->
            <div class="xl:col-span-1 space-y-8">
                <div class="glass p-8 neon-glow border-t-2 border-blue-600">
                    <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-8 text-blue-500">Execution Parameters</h3>
                    <form action="/update" method="POST" class="space-y-6">
                        <div>
                            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">System State</label>
                            <select name="trading_enabled" class="w-full bg-black/50 border border-white/10 p-4 rounded-xl font-bold text-xs outline-none focus:border-blue-500 transition-all">
                                <option value="True" {{ 'selected' if settings.trading_enabled }}>AUTH_EXECUTE_LIVE</option>
                                <option value="False" {{ 'selected' if not settings.trading_enabled }}>AUTH_READ_ONLY</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Risk Exposure (%)</label>
                            <input type="number" step="0.1" name="risk_pct" value="{{ settings.risk_pct }}" class="w-full bg-black/50 border border-white/10 p-4 rounded-xl font-bold outline-none focus:border-blue-500 transition-all">
                        </div>
                        <input type="hidden" name="symbols" value="{{ settings.symbols }}">
                        <button type="submit" class="w-full bg-blue-600 p-4 rounded-xl font-black text-xs uppercase tracking-widest hover:brightness-110 active:scale-95 transition-all shadow-xl shadow-blue-500/20">Sync Global State</button>
                    </form>
                </div>

                <div class="glass p-8 border-t-2 border-white/5">
                    <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-8 text-slate-400">Portfolio Core</h3>
                    <div id="portfolio-list" class="space-y-4 mb-8 max-h-[300px] overflow-y-auto pr-2">
                        <!-- Portfolios injected via JS -->
                    </div>
                    <form action="/add_symbol" method="POST" class="space-y-4">
                        <input type="text" name="symbol" placeholder="ADD_SYMBOL..." class="w-full bg-black/60 border border-white/10 p-4 rounded-xl text-xs font-bold uppercase tracking-widest focus:border-blue-500 outline-none transition-all">
                        <button class="w-full bg-white/5 hover:bg-white/10 border border-white/10 p-4 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all">Add to Core</button>
                    </form>
                </div>
            </div>

            <!-- CENTER: LIVE MATRIX -->
            <div class="xl:col-span-3 space-y-8">
                <div id="price-matrix" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <!-- Price cards injected via JS -->
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="glass p-8 border-t-2 border-emerald-500/30">
                        <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-6 text-emerald-400">Execution Stream</h3>
                        <div class="overflow-x-auto">
                            <table class="w-full text-[10px] mono text-left">
                                <thead class="text-slate-600 border-b border-white/5">
                                    <tr><th class="pb-3 uppercase">Ticket</th><th class="pb-3 uppercase">Asset</th><th class="pb-3 uppercase text-right">Profit</th></tr>
                                </thead>
                                <tbody id="positions-body" class="divide-y divide-white/5">
                                    <!-- Positions injected via JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="glass p-8 border-t-2 border-slate-500/30">
                        <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-6 text-slate-400">System Terminal</h3>
                        <div class="log-window" id="log-stream">
                            <!-- Logs injected via JS -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-12 py-8 border-t border-white/5 flex justify-between items-center text-[10px] text-slate-600 mono font-black tracking-[0.3em]">
            <div>AXON PRO CORE &copy; 2026 // NODE_ACTIVE</div>
            <div id="clock">00:00:00 UTC</div>
        </footer>
    </div>

    <script>
        let lastPrices = {};

        async function updateDashboard() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();

                // Update Header
                document.getElementById('header-latency').textContent = data.latency + 'ms';
                document.getElementById('global-pnl').textContent = '$' + data.metrics.total_pnl;

                // Update Price Matrix
                const matrix = document.getElementById('price-matrix');
                let matrixHtml = '';
                
                // Add Live Cards
                data.live_data.forEach(sym => {
                    const priceClass = lastPrices[sym.symbol] < sym.price ? 'price-up' : (lastPrices[sym.symbol] > sym.price ? 'price-down' : '');
                    lastPrices[sym.symbol] = sym.price;
                    
                    matrixHtml += `
                        <div class="glass p-6 relative overflow-hidden border-b-2 border-b-blue-500/30">
                            <div class="flex justify-between items-start mb-4">
                                <span class="text-xs font-black tracking-tighter text-blue-400 uppercase">${sym.symbol}</span>
                                <span class="text-[9px] mono text-slate-600">LIVE_DATA</span>
                            </div>
                            <div class="flex items-end gap-2">
                                <span class="text-3xl font-black italic tracking-tighter ${priceClass}">${sym.price.toFixed(5)}</span>
                                <span class="text-[10px] mb-1 ${sym.spread < 20 ? 'text-emerald-400' : 'text-yellow-400'}">S: ${sym.spread}</span>
                            </div>
                        </div>
                    `;
                });

                // Add Offline Warnings
                data.active_symbols.forEach(sym => {
                    if (!data.live_data.find(d => d.symbol.toUpperCase() === sym.toUpperCase())) {
                        matrixHtml += `
                            <div class="glass p-6 border-2 border-dashed border-red-500/20 opacity-60">
                                <div class="flex justify-between items-start mb-4">
                                    <span class="text-xs font-black tracking-tighter text-red-400 uppercase">${sym}</span>
                                    <span class="text-[9px] mono text-red-500 font-bold">OFFLINE</span>
                                </div>
                                <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">NOT_FOUND_IN_MT5</div>
                            </div>
                        `;
                    }
                });
                matrix.innerHTML = matrixHtml;

                // Update Portfolio List
                const portList = document.getElementById('portfolio-list');
                portList.innerHTML = data.active_symbols.map(sym => `
                    <div class="flex justify-between items-center bg-white/5 border border-white/5 p-4 rounded-xl">
                        <div class="flex items-center gap-3">
                            <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                            <span class="text-[12px] mono font-bold">${sym}</span>
                        </div>
                        <a href="/remove_symbol/${sym}" class="bg-red-500/10 text-red-500 w-8 h-8 flex items-center justify-center rounded-lg font-bold hover:bg-red-500/20 transition-all">✕</a>
                    </div>
                `).join('');

                // Update Positions
                const posBody = document.getElementById('positions-body');
                posBody.innerHTML = data.positions.map(pos => `
                    <tr>
                        <td class="py-3">#${pos.ticket}</td>
                        <td class="py-3 font-bold">${pos.symbol}</td>
                        <td class="py-3 text-right ${pos.profit > 0 ? 'text-emerald-400' : 'text-red-400'} font-bold">
                            ${pos.profit > 0 ? '+' : ''}${pos.profit}
                        </td>
                    </tr>
                `).join('');

                // Update Logs
                const logStream = document.getElementById('log-stream');
                const atBottom = logStream.scrollHeight - logStream.scrollTop <= logStream.clientHeight + 10;
                logStream.innerHTML = data.logs.map(log => `<p class="mb-1">${log}</p>`).join('');
                if (atBottom) logStream.scrollTop = logStream.scrollHeight;

            } catch (e) { console.error("Sync Error", e); }
        }

        setInterval(updateDashboard, 500); // 500ms ultra-fast sync
        setInterval(() => {
            document.getElementById('clock').textContent = new Date().toISOString().split('T')[1].split('.')[0] + ' UTC';
        }, 1000);
        
        // Initial boot
        updateDashboard();
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
</head>
<body class="flex items-center justify-center h-screen bg-black text-white font-sans">
    <div class="w-full max-w-sm p-12 rounded-[2.5rem] bg-slate-900/40 border border-white/10 backdrop-blur-2xl text-center">
        <h1 class="text-3xl font-black italic tracking-tighter uppercase mb-2">Axon<span class="text-blue-500">Algo</span></h1>
        <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black mb-12">Security Terminal</p>
        <form action="/login" method="POST" class="space-y-8">
            <input type="password" name="password" required placeholder="PROTOCOL_KEY" class="w-full bg-black/60 border border-white/10 p-5 rounded-2xl text-center text-xl tracking-[0.5em] outline-none focus:border-blue-500 transition-all font-black">
            <button class="w-full bg-blue-600 p-5 rounded-2xl font-black text-[11px] uppercase tracking-[0.3em]">Authorize Entry</button>
        </form>
        {% if error %}<p class="text-red-500 text-[10px] mt-8 font-black uppercase">{{ error }}</p>{% endif %}
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
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    return render_template_string(HTML_TEMPLATE, settings=settings)

@app.route('/api/data')
def get_data():
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    
    start_time = time.time()
    settings = db.get_system_settings()
    active_symbols = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
    
    live_data = []
    positions = []
    
    if mt5.initialize():
        all_symbols = {s.name.upper(): s.name for s in mt5.symbols_get()}
        for sym in active_symbols:
            actual_name = all_symbols.get(sym.upper())
            if actual_name:
                tick = mt5.symbol_info_tick(actual_name)
                info = mt5.symbol_info(actual_name)
                if tick and info:
                    live_data.append({
                        "symbol": actual_name,
                        "price": tick.bid,
                        "spread": round((tick.ask - tick.bid) / (info.point * 10), 1)
                    })
        
        res = mt5.positions_get()
        if res:
            for p in res:
                positions.append({"ticket": p.ticket, "symbol": p.symbol, "profit": round(p.profit, 2)})
    
    logs = []
    if os.path.exists("axon_bot.log"):
        with open("axon_bot.log", "r") as f:
            logs = f.readlines()[-20:]
            
    return jsonify({
        "metrics": db.get_metrics(),
        "active_symbols": active_symbols,
        "live_data": live_data,
        "positions": positions,
        "logs": logs,
        "latency": round((time.time() - start_time) * 1000, 2)
    })

@app.route('/update', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    db.update_system_settings(float(request.form['risk_pct']), request.form['trading_enabled'] == 'True', request.form['symbols'])
    return redirect(url_for('dashboard'))

@app.route('/add_symbol', methods=['POST'])
def add_symbol():
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
    new_sym = request.form['symbol'].strip()
    if new_sym and new_sym not in syms:
        syms.append(new_sym)
        db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

@app.route('/remove_symbol/<symbol>')
def remove_symbol(symbol):
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
    if symbol in syms:
        syms.remove(symbol)
        db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
