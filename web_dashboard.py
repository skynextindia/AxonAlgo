from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from src.config import Config
from src.database import TradingDatabase
from src.mt5_connection import MT5Client
import MetaTrader5 as mt5
import os
import time
import sqlite3
import datetime
import urllib.request
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = TradingDatabase()

NEWS_CACHE = {"data": [], "last_fetch": 0}
EVENTS_CACHE = {"data": [], "last_fetch": 0}

def fetch_market_news():
    global NEWS_CACHE
    if time.time() - NEWS_CACHE["last_fetch"] < 300:
        return NEWS_CACHE["data"]
    try:
        req = urllib.request.Request('https://www.investing.com/rss/news_285.rss', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        news = []
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
            news.append({"title": title, "date": pubDate[:22]}) # truncate long date
        NEWS_CACHE["data"] = news
        NEWS_CACHE["last_fetch"] = time.time()
    except Exception as e:
        print("News error:", e)
    return NEWS_CACHE["data"]

# --- AXON STEALTH COMMAND CORE: V19.0 (MINIMAL HIGH-CONTRAST) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AXON STEALTH | Node 01</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #000000; --panel: #0a0a0a; --border: #1a1a1a; --accent: #3b82f6; --success: #10b981; --danger: #ef4444; }
        * { box-sizing: border-box; cursor: crosshair; }
        body { background: var(--bg); color: #888; font-family: 'Inter', sans-serif; height: 100vh; margin: 0; display: flex; overflow: hidden; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        
        /* SIDEBAR (STEALTH) */
        .sidebar { width: 64px; border-right: 1px solid var(--border); display: flex; flex-direction: column; align-items: center; padding: 2rem 0; flex-shrink: 0; }
        .nav-item { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: #444; margin-bottom: 1.5rem; transition: 0.1s; cursor: pointer; }
        .nav-item:hover { color: #fff; }
        .nav-item.active { color: var(--accent); }

        /* HEADER */
        header { height: 64px; border-bottom: 1px solid var(--border); display: flex; align-items: center; padding: 0 2rem; background: var(--bg); }
        .stat { border-right: 1px solid var(--border); padding-right: 2rem; margin-right: 2rem; }
        .stat-label { font-size: 10px; font-weight: 800; color: #444; text-transform: uppercase; letter-spacing: 0.1em; }
        .stat-value { font-size: 14px; font-weight: 700; color: #fff; margin-top: 2px; }

        /* GRID */
        main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
        .workspace { flex: 1; padding: 1.5rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1.5rem; }
        .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 4px; display: flex; flex-direction: column; }
        .panel-header { padding: 0.75rem 1.25rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #0c0c0c; }
        .panel-title { font-size: 10px; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.1em; }

        /* TICKER GRID */
        .ticker-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 1px; background: var(--border); border: 1px solid var(--border); }
        .ticker-item { background: var(--bg); padding: 1rem; transition: 0.1s; position: relative; }
        .ticker-item:hover { background: #0a0a0a; }
        .price-val { font-family: 'JetBrains Mono'; font-size: 12px; font-weight: 700; margin-top: 0.5rem; }
        .remove-btn { position: absolute; top: 4px; right: 4px; font-size: 10px; color: #333; opacity: 0; }
        .ticker-item:hover .remove-btn { opacity: 1; }
        .remove-btn:hover { color: var(--danger); }

        /* TABLES */
        .trade-row { padding: 1rem 1.25rem; border-bottom: 1px solid var(--border); display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; align-items: center; transition: 0.05s; }
        .trade-row:hover { background: #050505; }
        
        /* LOGS */
        #log-stream { padding: 1rem; font-family: 'JetBrains Mono'; font-size: 11px; line-height: 1.6; color: #444; overflow-y: auto; height: 300px; }
        .log-AUTHORIZED { color: var(--success); }
        .log-ERROR { color: var(--danger); }
        .log-WARNING { color: #f59e0b; }

        /* MODAL */
        .modal { position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 1000; display: none; align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-box { width: 800px; background: #050505; border: 1px solid #222; padding: 2rem; border-radius: 4px; }

        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <nav class="sidebar">
        <div class="nav-item active" onclick="switchTab('terminal', this)"><i data-lucide="terminal"></i></div>
        <div class="nav-item" onclick="switchTab('lab', this)"><i data-lucide="activity"></i></div>
        <div class="nav-item" onclick="switchTab('settings', this)"><i data-lucide="cpu"></i></div>
        <div class="mt-auto nav-item text-red-900 hover:text-red-500" onclick="location.href='/logout'"><i data-lucide="power"></i></div>
    </nav>

    <main>
        <header>
            <div class="stat"><div class="stat-label">Equity</div><div id="acc-equity" class="stat-value">$0.00</div></div>
            <div class="stat"><div class="stat-label">Net PnL</div><div id="acc-pnl" class="stat-value text-emerald-500">0.00</div></div>
            <div class="stat"><div class="stat-label">Neural Status</div><div class="stat-value text-blue-500">ACTIVE_SCAN</div></div>
            <div class="ml-auto mono text-[10px] text-gray-700">NODE_ID: AXON_01_SECURE</div>
        </header>

        <div class="workspace">
            <div id="tab-terminal" class="tab-content active space-y-6">
                <!-- TICKER -->
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">Asset Matrix</span>
                        <form action="/add_symbol" method="POST" class="flex gap-2">
                            <input type="text" name="symbol" placeholder="[+]" class="bg-black border border-white/5 px-2 py-1 text-[10px] font-bold uppercase text-white outline-none focus:border-blue-500">
                        </form>
                    </div>
                    <div id="ticker-grid" class="ticker-grid"></div>
                </div>

                <div class="grid grid-cols-12 gap-6">
                    <!-- TRADES -->
                    <div class="col-span-8 panel">
                        <div class="panel-header"><span class="panel-title">Live Execution Hub</span><span id="pos-count" class="mono text-[10px]">0_ACTIVE</span></div>
                        <div id="positions-list" class="flex-1"></div>
                    </div>
                    <!-- EVENTS -->
                    <div class="col-span-4 panel">
                        <div class="panel-header"><span class="panel-title">Macro Events & Sentiment</span></div>
                        <div id="events-stream" class="p-4 space-y-3 overflow-y-auto" style="height: 300px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <div id="scan-modal" class="modal" onclick="this.classList.remove('active')">
        <div class="modal-box" onclick="event.stopPropagation()" id="scan-content"></div>
    </div>

    <script>
        let lastPrices = {};
        
        async function updateHUD() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                
                document.getElementById('acc-equity').textContent = '$' + data.account.equity.toLocaleString();
                let pnl = data.positions.reduce((a, b) => a + b.profit, 0);
                document.getElementById('acc-pnl').textContent = (pnl >= 0 ? '+' : '') + pnl.toFixed(2);
                document.getElementById('acc-pnl').className = `stat-value ${pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`;

                // Ticker
                const ticker = document.getElementById('ticker-grid');
                ticker.innerHTML = data.live_data.map(s => {
                    let colorClass = 'text-white';
                    let bgClass = 'bg-black hover:bg-[#0a0a0a]';
                    let priceDiff = '';
                    
                    if (lastPrices[s.symbol]) {
                        if (s.price > lastPrices[s.symbol]) {
                            colorClass = 'text-emerald-500';
                            bgClass = 'bg-emerald-950/20 hover:bg-emerald-900/30 border-t border-emerald-500/20';
                            priceDiff = '▲';
                        } else if (s.price < lastPrices[s.symbol]) {
                            colorClass = 'text-red-500';
                            bgClass = 'bg-red-950/20 hover:bg-red-900/30 border-t border-red-500/20';
                            priceDiff = '▼';
                        } else {
                            colorClass = 'text-white';
                            bgClass = 'bg-black hover:bg-[#0a0a0a] border-t border-white/5';
                        }
                    }
                    lastPrices[s.symbol] = s.price;
                    
                    return `
                    <div class="ticker-item ${bgClass}" onclick="openScan('${s.symbol}')">
                        <a href="/remove_symbol/${s.symbol}" class="remove-btn" onclick="event.stopPropagation()">✕</a>
                        <div class="text-[10px] font-black text-gray-500 uppercase flex justify-between">
                            <span>${s.symbol}</span>
                            <span class="${colorClass}">${priceDiff}</span>
                        </div>
                        <div class="flex justify-between items-end mt-2">
                            <div class="price-val ${colorClass} m-0">${s.price.toFixed(5)}</div>
                            <div class="text-[9px] font-bold ${s.day_change > 0 ? 'text-emerald-500' : s.day_change < 0 ? 'text-red-500' : 'text-gray-600'}">${s.day_change > 0 ? '+' : ''}${s.day_change}%</div>
                        </div>
                    </div>
                    `;
                }).join('');

                // Trades
                const list = document.getElementById('positions-list');
                document.getElementById('pos-count').textContent = data.positions.length + '_ACTIVE';
                list.innerHTML = data.positions.map(p => `
                    <div class="trade-row">
                        <div class="text-xs font-black text-white uppercase">${p.symbol}</div>
                        <div class="mono text-[10px] text-gray-600">#${p.ticket}</div>
                        <div class="mono text-[10px] text-gray-400">${p.volume}L</div>
                        <div class="text-right font-black mono ${p.profit >= 0 ? 'text-emerald-500' : 'text-red-500'}">${p.profit >= 0 ? '+' : ''}${p.profit.toFixed(2)}</div>
                    </div>
                `).join('');

                // Events & News
                const eventsPanel = document.getElementById('events-stream');
                let html = '';
                
                if (data.news && data.news.length > 0) {
                    html += `<div class="text-[10px] text-gray-500 font-bold mb-2 uppercase">Global Market News</div>`;
                    html += data.news.map(n => `
                        <div class="border-l-2 border-emerald-500 pl-3 py-1 mb-3">
                            <div class="text-xs text-white font-medium leading-tight">${n.title}</div>
                            <div class="mono text-[9px] text-gray-500 mt-1">${n.date}</div>
                        </div>
                    `).join('');
                }
                
                html += `<div class="text-[10px] text-gray-500 font-bold mb-2 mt-4 uppercase">Calendar Events (Today)</div>`;
                if (data.events && data.events.length > 0) {
                    html += data.events.map(e => `
                        <div class="border-l-2 border-blue-500 pl-3 py-1 mb-2">
                            <div class="flex justify-between items-center mb-1">
                                <span class="text-[10px] font-black text-blue-500 uppercase">${e.curr}</span>
                                <span class="mono text-[9px] text-gray-500">${e.time_str}</span>
                            </div>
                            <div class="text-xs text-white font-medium">${e.name}</div>
                        </div>
                    `).join('');
                } else {
                    html += `<div class="text-xs text-gray-600 italic">No major calendar events.</div>`;
                }
                eventsPanel.innerHTML = html;

            } catch (e) { console.error("Sync_Fail", e); }
        }

        function switchTab(id, el) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById('tab-'+id)?.classList.add('active');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            el.classList.add('active');
        }

        async function openScan(sym) {
            const modal = document.getElementById('scan-modal');
            const content = document.getElementById('scan-content');
            modal.classList.add('active');
            content.innerHTML = `
                <div class="flex justify-between border-b border-white/5 pb-4 mb-6">
                    <h2 class="text-xl font-black text-white uppercase">${sym} :: Deep Scan</h2>
                    <button class="text-gray-600 hover:text-white" onclick="document.getElementById('scan-modal').classList.remove('active')">✕</button>
                </div>
                <div class="text-center py-8 text-gray-500 italic text-sm">Initiating Neural Probe...</div>
            `;
            
            try {
                const res = await fetch('/api/scan/' + sym);
                const data = await res.json();
                
                if (data.error) {
                    content.innerHTML = `
                        <div class="flex justify-between border-b border-white/5 pb-4 mb-6">
                            <h2 class="text-xl font-black text-white uppercase">${sym} :: Deep Scan</h2>
                            <button class="text-gray-600 hover:text-white" onclick="document.getElementById('scan-modal').classList.remove('active')">✕</button>
                        </div>
                        <div class="text-center py-8 text-red-500 italic text-sm">Error: ${data.error}</div>
                    `;
                    return;
                }

                content.innerHTML = `
                    <div class="flex justify-between border-b border-white/5 pb-4 mb-6">
                        <h2 class="text-xl font-black text-white uppercase">${sym} :: Deep Scan</h2>
                        <button class="text-gray-600 hover:text-white" onclick="document.getElementById('scan-modal').classList.remove('active')">✕</button>
                    </div>
                    <div class="grid grid-cols-2 gap-8 mb-8">
                        <div>
                            <span class="text-[9px] font-black text-gray-500 uppercase block mb-2">Neural Sentiment</span>
                            <div class="text-2xl font-black ${data.color} mono italic">${data.direction} [${data.alpha}%]</div>
                        </div>
                        <div>
                            <span class="text-[9px] font-black text-gray-500 uppercase block mb-2">Institutional Strength</span>
                            <div class="text-2xl font-black ${data.color} mono">${data.strength}</div>
                        </div>
                    </div>
                    <div class="p-6 bg-white/[0.02] border border-white/5 rounded">
                        <p class="text-xs text-gray-400 italic font-medium leading-relaxed">"${data.ai_text}"</p>
                    </div>
                `;
            } catch (err) {
                console.error(err);
            }
        }

        setInterval(updateHUD, 300);
        updateHUD();
        lucide.createIcons();
    </script>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string("""
    <!DOCTYPE html><html><body style="background:#000;color:white;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif">
    <div style="background:#0a0a0a;padding:50px;border-radius:4px;border:1px solid #111;text-align:center">
        <h1 style="text-transform:uppercase;margin-bottom:30px;letter-spacing:0.2em;font-weight:900;font-size:18px">Axon<span style="color:#3b82f6">Stealth</span></h1>
        <form action="/login" method="POST"><input type="password" name="password" style="background:#000;border:1px solid #222;padding:12px;color:white;text-align:center;width:200px" placeholder="AUTH_KEY"><br><br>
        <button style="background:#3b82f6;color:white;border:none;padding:12px;width:100%;font-weight:bold;cursor:pointer">INITIALIZE</button></form>
    </div></body></html>
    """)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    settings = db.get_system_settings()
    positions = []
    live_data = []
    account = {"equity": 0}
    if mt5.initialize():
        acc_info = mt5.account_info()
        if acc_info: account["equity"] = acc_info.equity
        symbols = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
        for s in symbols:
            exact_sym = MT5Client.resolve_symbol(s)
            mt5.symbol_select(exact_sym, True)
            tick = mt5.symbol_info_tick(exact_sym)
            sym_info = mt5.symbol_info(exact_sym)
            if tick and sym_info: 
                open_price = sym_info.session_open
                day_change = 0.0
                if open_price and open_price > 0:
                    day_change = ((tick.bid - open_price) / open_price) * 100
                live_data.append({"symbol": s, "price": tick.bid, "day_change": round(day_change, 2)})
            else: 
                live_data.append({"symbol": s, "price": 0.0, "day_change": 0.0})
        
        res = mt5.positions_get()
        if res:
            for p in res:
                positions.append({"ticket": p.ticket, "symbol": p.symbol, "volume": p.volume, "profit": round(p.profit, 2)})

    global EVENTS_CACHE
    if time.time() - EVENTS_CACHE["last_fetch"] < 300:
        events = EVENTS_CACHE["data"]
    else:
        events = []
        try:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            start_day = now_utc.replace(hour=0, minute=0, second=0)
            end_day = now_utc.replace(hour=23, minute=59, second=59)
            majors = ["USD", "EUR", "GBP", "JPY", "AUD"]
            for curr in majors:
                evs = mt5.calendar_events_get(
                    time_from=int(start_day.timestamp()),
                    time_to=int(end_day.timestamp()),
                    currency=curr,
                    importance=mt5.CALENDAR_IMPORTANCE_HIGH
                )
                if evs:
                    for e in evs:
                        events.append({"curr": curr, "time": e.time, "name": e.name})
            events.sort(key=lambda x: x["time"])
            # Format events time
            for e in events:
                dt_obj = datetime.datetime.fromtimestamp(e["time"], datetime.timezone.utc)
                e["time_str"] = dt_obj.strftime("%H:%M UTC")
            
            EVENTS_CACHE["data"] = events
            EVENTS_CACHE["last_fetch"] = time.time()
        except: pass
        events = EVENTS_CACHE["data"]

    return jsonify({"live_data": live_data, "positions": positions, "account": account, "events": events, "news": fetch_market_news()})

@app.route('/api/scan/<symbol>')
def scan_symbol(symbol):
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    exact_sym = MT5Client.resolve_symbol(symbol)
    if not mt5.initialize(): return jsonify({"error": "MT5 offline"})
    df = MT5Client.get_market_data(exact_sym, Config.TIMEFRAME)
    if df.empty:
        return jsonify({"error": "No market data available"})
        
    from src.engines.synergy_engine import SynergyEngine
    synergy = SynergyEngine()
    analysis = synergy.analyze(exact_sym, df)
    
    # Generate dynamic text based on alpha
    if analysis['alpha'] > 75:
        ai_text = "Strong momentum confirmed. High probability of continued trend continuation. Institutional accumulation detected."
        str_meter = "STRONG " + analysis['direction']
        color = "text-emerald-500" if analysis['direction'] == "BUY" else "text-red-500"
    elif analysis['alpha'] > 50:
        ai_text = "Moderate confluence. Market structure is establishing bias. Await further confirmation."
        str_meter = "NEUTRAL " + analysis['direction']
        color = "text-blue-500"
    else:
        ai_text = "Low confluence. Market is ranging or experiencing conflicting volume patterns. Safe mode active."
        str_meter = "FLAT_RANGING"
        color = "text-gray-500"

    return jsonify({
        "symbol": symbol,
        "direction": analysis['direction'],
        "alpha": analysis['alpha'],
        "breakdown": analysis['breakdown'],
        "strength": str_meter,
        "ai_text": ai_text,
        "color": color
    })

@app.route('/add_symbol', methods=['POST'])
def add_symbol():
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
    new_sym = request.form.get('symbol', '').strip()
    if new_sym and new_sym not in syms:
        syms.append(new_sym)
        db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

@app.route('/remove_symbol/<symbol>')
def remove_symbol(symbol):
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip() and s.strip().lower() != symbol.strip().lower()]
    db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
