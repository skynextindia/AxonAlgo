from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import json
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import mplfinance as mpf
import io
from flask import Response
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;400;600;900&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #08090d; --panel: #11141d; --border: rgba(255, 255, 255, 0.03); --accent: #3b82f6; }
        body { background-color: var(--bg); color: #e2e8f0; font-family: 'Outfit', sans-serif; overflow-x: hidden; letter-spacing: -0.01em; }
        .glass { background: var(--panel); border: 1px solid var(--border); border-radius: 1.25rem; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .neon-blue { box-shadow: 0 0 30px rgba(59, 130, 246, 0.1); border-top: 2px solid var(--accent); }
        .log-window { background: #000; border: 1px solid #1a1d26; height: 280px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 1.25rem; color: #64748b; line-height: 1.6; }
        .price-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border-left: 2px solid transparent; }
        .price-card:hover { transform: translateY(-4px); background: #161a27; border-left-color: var(--accent); }
        .price-up { color: #10b981; }
        .price-down { color: #f43f5e; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    </style>
</head>
<body class="p-6 md:p-12">
    <!-- CHART MODAL -->
    <div id="chart-modal" class="fixed inset-0 bg-black/95 flex items-center justify-center z-50 hidden p-4 sm:p-12">
        <div class="glass w-full h-full max-w-7xl relative overflow-hidden flex flex-col border-white/5">
            <div class="flex justify-between items-center p-6 border-b border-white/5 bg-[#11141d]">
                <div class="flex items-center gap-6">
                    <div class="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                        <i data-lucide="candlestick-chart" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <h2 id="chart-title" class="text-sm font-black text-white uppercase tracking-[0.2em]">MT5_QUANTUM_STREAM</h2>
                        <p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Direct Terminal Node // 1:1 Execution Mirror</p>
                    </div>
                </div>
                <button class="w-12 h-12 flex items-center justify-center rounded-2xl hover:bg-red-500/10 text-slate-500 hover:text-red-500 transition-all" onclick="closeChart()">
                    <i data-lucide="x" class="w-6 h-6"></i>
                </button>
            </div>
            <div class="flex-1 bg-black flex items-center justify-center p-8 overflow-hidden">
                <img id="mt5-chart-img" class="w-full h-full object-contain rounded-xl shadow-2xl" src="">
            </div>
            <div class="p-4 bg-[#11141d] border-t border-white/5 flex justify-between items-center px-10">
                <div class="flex items-center gap-8">
                    <div class="flex items-center gap-3">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        <span class="text-[10px] mono text-slate-400 font-bold uppercase">Uptime: Stable</span>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                        <span class="text-[10px] mono text-slate-400 font-bold uppercase">Source: MT5_BRIDGE</span>
                    </div>
                </div>
                <div class="flex gap-6">
                    <span class="text-[10px] mono text-blue-400 font-black tracking-widest bg-blue-500/5 px-4 py-2 rounded-lg">POSITIONS_VISIBLE</span>
                </div>
            </div>
        </div>
    </div>

    <div class="max-w-[1700px] mx-auto">
        <!-- HEADER -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-16 gap-8">
            <div class="flex items-center gap-6">
                <div class="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[1.5rem] flex items-center justify-center shadow-2xl shadow-blue-500/20 group cursor-pointer">
                    <i data-lucide="zap" class="text-white w-8 h-8 group-hover:scale-110 transition-transform"></i>
                </div>
                <div>
                    <h1 class="text-4xl font-black tracking-tighter uppercase italic leading-none mb-3 bg-gradient-to-r from-white to-slate-500 bg-clip-text text-transparent">AxonAlgo <span class="text-blue-500 text-xl not-italic opacity-40 ml-2">v3.0</span></h1>
                    <div class="flex items-center gap-4 text-[10px] mono font-bold text-slate-500 uppercase tracking-widest">
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                            Latency: <span id="header-latency" class="text-emerald-400">0ms</span>
                        </div>
                        <div class="w-px h-3 bg-white/10"></div>
                        <div class="flex items-center gap-2">
                            <i data-lucide="activity" class="w-3 h-3 text-blue-500"></i>
                            Engine: <span class="text-blue-400">Quantum_Active</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-6">
                <div class="glass px-8 py-4 flex flex-col items-end">
                    <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Global Net PnL</span>
                    <span id="global-pnl" class="text-2xl font-black text-emerald-400 italic font-mono tracking-tighter">$0.00</span>
                </div>
                <a href="/logout" class="bg-red-500/5 hover:bg-red-500/10 border border-red-500/20 px-8 py-5 rounded-2xl text-[10px] uppercase font-black tracking-widest text-red-400 transition-all flex items-center gap-3">
                    <i data-lucide="power" class="w-4 h-4"></i>
                    Terminate
                </a>
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
        let activeChartSymbol = null;
        let chartInterval = null;

        async function updateDashboard() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();

                document.getElementById('header-latency').textContent = data.latency + 'ms';
                document.getElementById('global-pnl').textContent = '$' + data.metrics.total_pnl;

                const matrix = document.getElementById('price-matrix');
                if (matrix) {
                    let matrixHtml = '';
                    if (data.live_data) {
                        data.live_data.forEach(sym => {
                            const priceClass = lastPrices[sym.symbol] < sym.price ? 'price-up' : (lastPrices[sym.symbol] > sym.price ? 'price-down' : '');
                            lastPrices[sym.symbol] = sym.price;
                            matrixHtml += `
                                <div class="glass p-8 relative overflow-hidden price-card cursor-pointer" onclick="openChart('${sym.symbol}')">
                                    <div class="flex justify-between items-start mb-6">
                                        <div class="flex items-center gap-3">
                                            <div class="w-8 h-8 rounded-lg bg-blue-500/5 flex items-center justify-center text-blue-500">
                                                <i data-lucide="trending-up" class="w-4 h-4"></i>
                                            </div>
                                            <span class="text-sm font-black tracking-tighter text-white uppercase">${sym.symbol}</span>
                                        </div>
                                        <span class="text-[9px] mono text-emerald-500 bg-emerald-500/5 px-2 py-1 rounded">LIVE_FEED</span>
                                    </div>
                                    <div class="flex items-baseline gap-3">
                                        <span class="text-3xl font-black italic tracking-tighter ${priceClass}">${sym.price.toFixed(5)}</span>
                                        <span class="text-[10px] mono ${sym.spread < 20 ? 'text-blue-400' : 'text-yellow-500'} font-bold">SPR: ${sym.spread}</span>
                                    </div>
                                    <div class="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-blue-500/30 w-2/3"></div>
                                    </div>
                                </div>
                            `;
                        });
                    }
                    
                    if (data.active_symbols) {
                        data.active_symbols.forEach(sym => {
                            if (!data.live_data.find(d => d.symbol.toUpperCase() === sym.toUpperCase())) {
                                matrixHtml += `
                                    <div class="glass p-8 border-2 border-dashed border-red-500/10 opacity-60">
                                        <div class="flex justify-between items-start mb-4">
                                            <span class="text-xs font-black tracking-tighter text-red-400 uppercase">${sym}</span>
                                            <span class="text-[9px] mono text-red-500 font-bold uppercase tracking-widest">OFFLINE</span>
                                        </div>
                                        <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">NOT_FOUND_IN_MT5</div>
                                    </div>
                                `;
                            }
                        });
                    }
                    matrix.innerHTML = matrixHtml;
                    lucide.createIcons();
                }

                const portList = document.getElementById('portfolio-list');
                if (portList && data.active_symbols) {
                    portList.innerHTML = data.active_symbols.map(sym => `
                        <div class="flex justify-between items-center bg-white/5 border border-white/5 p-4 rounded-xl">
                            <div class="flex items-center gap-3">
                                <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                                <span class="text-[12px] mono font-bold">${sym}</span>
                            </div>
                            <a href="/remove_symbol/${sym}" class="bg-red-500/10 text-red-500 w-8 h-8 flex items-center justify-center rounded-lg font-bold">✕</a>
                        </div>
                    `).join('');
                }

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

                const logStream = document.getElementById('log-stream');
                const atBottom = logStream.scrollHeight - logStream.scrollTop <= logStream.clientHeight + 10;
                logStream.innerHTML = data.logs.map(log => `<p class="mb-1">${log}</p>`).join('');
                if (atBottom) logStream.scrollTop = logStream.scrollHeight;

            } catch (e) { console.error("Sync Error", e); }
        }

        window.openChart = function(symbol) {
            activeChartSymbol = symbol;
            document.getElementById('chart-modal').classList.remove('hidden');
            document.getElementById('chart-title').textContent = symbol + " // LIVE_MT5_STREAM";
            refreshChartImage();
            if (chartInterval) clearInterval(chartInterval);
            chartInterval = setInterval(refreshChartImage, 1000);
        };

        window.closeChart = function() {
            document.getElementById('chart-modal').classList.add('hidden');
            if (chartInterval) clearInterval(chartInterval);
            activeChartSymbol = null;
        };

        function refreshChartImage() {
            if (!activeChartSymbol) return;
            const img = document.getElementById('mt5-chart-img');
            img.src = `/chart_render/${activeChartSymbol}?t=` + new Date().getTime();
        }

        setInterval(updateDashboard, 500);
        setInterval(() => {
            document.getElementById('clock').textContent = new Date().toISOString().split('T')[1].split('.')[0] + ' UTC';
        }, 1000);
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

@app.route('/chart_render/<symbol>')
def chart_render(symbol):
    """Render a professional MT5-style chart image with live positions."""
    try:
        if not mt5.initialize():
            print("[MT5] Initialization failed for chart render")
            return "MT5 Init Error", 500
        
        # Case-insensitive lookup
        all_symbols = {s.name.upper(): s.name for s in mt5.symbols_get()}
        actual_name = all_symbols.get(symbol.upper(), symbol)
        
        # Get data
        rates = mt5.copy_rates_from_pos(actual_name, mt5.TIMEFRAME_M5, 0, 100)
        if rates is None or len(rates) == 0:
            print(f"[MT5] No rates data found for {actual_name}")
            return "No Data", 404
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Style: Professional MT5 Dark
        mc = mpf.make_marketcolors(up='#10b981', down='#f43f5e', edge='inherit', wick='inherit', volume='inherit', ohlc='inherit')
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, facecolor='#000000', gridcolor='#11141d', edgecolor='#1e293b')
        
        # Add Live Positions as Horizontal Lines
        hlines = []
        hcolors = []
        positions = mt5.positions_get(symbol=actual_name)
        if positions:
            for p in positions:
                hlines.append(p.price_open)
                hcolors.append('#3b82f6') # Entry Blue
                if p.sl > 0:
                    hlines.append(p.sl)
                    hcolors.append('#f43f5e') # SL Red
                if p.tp > 0:
                    hlines.append(p.tp)
                    hcolors.append('#10b981') # TP Green
        
        # Render to Buffer
        buf = io.BytesIO()
        if hlines:
            mpf.plot(df, type='candle', style=s, hlines=dict(hlines=hlines, colors=hcolors, linestyle='dashed', linewidths=1.2), 
                     figsize=(14, 8), tight_layout=True, savefig=buf, closeplot=True)
        else:
            mpf.plot(df, type='candle', style=s, figsize=(14, 8), tight_layout=True, savefig=buf, closeplot=True)
        
        buf.seek(0)
        return Response(buf.read(), mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Chart Render failed: {e}")
        return f"Render Error: {str(e)}", 500

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
