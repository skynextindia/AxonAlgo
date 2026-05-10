from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from src.config import Config
from src.database import TradingDatabase
import MetaTrader5 as mt5
import json
import os
import time
from datetime import datetime, timedelta
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = TradingDatabase()

# --- ENTERPRISE AI HUB: V13.0 (FINY COMMAND) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AXON | Intelligence Core</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #020305; --panel: #090c14; --border: #161c2b; --accent: #3b82f6; --finy: #a855f7; }
        body { background: var(--bg); color: #94a3b8; font-family: 'Outfit', sans-serif; height: 100vh; overflow: hidden; margin: 0; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 1rem; }
        
        /* RAIL */
        .sidebar-rail { width: 70px; background: #05070a; border-right: 1px solid var(--border); height: 100vh; flex-shrink: 0; display: flex; flex-direction: column; align-items: center; padding: 1.5rem 0; z-index: 50; }
        .nav-btn { width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 0.75rem; margin-bottom: 1rem; color: #334155; cursor: pointer; transition: all 0.2s; }
        .nav-btn:hover { color: white; background: rgba(255,255,255,0.03); }
        .nav-btn.active { color: white; background: var(--accent); box-shadow: 0 0 20px rgba(59, 130, 246, 0.2); }
        .nav-btn.finy-btn { color: var(--finy); border: 1px solid rgba(168, 85, 247, 0.2); }
        .nav-btn.finy-btn.active { background: var(--finy); color: white; box-shadow: 0 0 20px rgba(168, 85, 247, 0.3); }

        /* HUD */
        .hud-stat { border-right: 1px solid var(--border); padding: 0 2rem; }
        .hud-stat:last-child { border-right: none; }
        
        /* TICKER */
        .asset-tile { position: relative; min-width: 120px; border: 1px solid var(--border); border-radius: 0.6rem; padding: 0.8rem; background: rgba(255,255,255,0.01); display: flex; flex-direction: column; gap: 0.5rem; transition: all 0.2s; }
        .asset-tile:hover { border-color: var(--accent); background: rgba(255,255,255,0.03); }
        .remove-trigger { position: absolute; top: 6px; right: 6px; width: 16px; height: 16px; background: rgba(244, 63, 94, 0.1); color: #f43f5e; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 8px; opacity: 0; cursor: pointer; border: 1px solid rgba(244, 63, 94, 0.1); }
        .asset-tile:hover .remove-trigger { opacity: 0.6; }
        .price-sq { padding: 4px; border-radius: 4px; font-size: 13px; font-weight: 800; text-align: center; font-family: 'JetBrains Mono'; }
        .sq-up { background: rgba(16, 185, 129, 0.15); color: #10b981; }
        .sq-down { background: rgba(244, 63, 94, 0.15); color: #f43f5e; }
        
        /* CHAT INTERFACE */
        .finy-drawer { position: fixed; right: 0; top: 0; width: 450px; height: 100vh; background: #070a0f; border-left: 1px solid var(--border); transform: translateX(100%); transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1); z-index: 100; display: flex; flex-direction: column; box-shadow: -30px 0 60px rgba(0,0,0,0.6); }
        .finy-drawer.open { transform: translateX(0); }
        .chat-area { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; }
        .chat-msg { max-width: 90%; padding: 1rem; border-radius: 1rem; font-size: 0.9rem; line-height: 1.6; }
        .msg-finy { background: rgba(168, 85, 247, 0.05); border: 1px solid rgba(168, 85, 247, 0.1); color: #e9d5ff; align-self: flex-start; }
        .msg-user { background: var(--accent); color: white; align-self: flex-end; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.2); }
        
        .activity-card { background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem; margin-top: 0.5rem; }
        .dive-btn { background: var(--finy); color: white; padding: 0.6rem 1.2rem; border-radius: 0.5rem; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; transition: all 0.2s; margin-top: 0.75rem; }
        .dive-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }

        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    </style>
</head>
<body class="flex">
    <!-- ICON RAIL -->
    <aside class="sidebar-rail">
        <div class="w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center mb-10 shadow-lg shadow-blue-500/30">
            <i data-lucide="zap" class="text-white w-6 h-6"></i>
        </div>
        <div class="nav-btn active" onclick="switchTab('terminal', this)"><i data-lucide="layout-dashboard" class="w-5 h-5"></i></div>
        <div class="nav-btn" onclick="switchTab('settings', this)"><i data-lucide="settings" class="w-5 h-5"></i></div>
        
        <div class="mt-auto space-y-4">
            <div id="finy-toggle" class="nav-btn finy-btn" onclick="toggleFiny()"><i data-lucide="bot" class="w-6 h-6"></i></div>
            <a href="/logout" class="nav-btn text-red-500/40 hover:text-red-500 transition-colors"><i data-lucide="power" class="w-5 h-5"></i></a>
        </div>
    </aside>

    <main class="flex-1 flex flex-col overflow-hidden">
        <!-- COMMAND HUD -->
        <header class="h-24 border-b border-white/5 flex items-center px-10 bg-[#07090f]/90 backdrop-blur-xl">
            <div class="flex flex-1 items-center">
                <div class="hud-stat"><span class="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Equity Exposure</span><span id="account-equity" class="text-xl font-bold text-white mono">$0.00</span></div>
                <div class="hud-stat"><span class="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Margin Strength</span><span id="margin-level" class="text-xl font-bold text-emerald-500 mono">0%</span></div>
                <div class="hud-stat"><span class="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Floating Intel</span><span id="live-pnl" class="text-xl font-black mono italic text-white">$0.00</span></div>
            </div>
            <div class="flex items-center gap-2 px-6 py-2 bg-emerald-500/5 rounded-full border border-emerald-500/10">
                <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                <span class="text-[10px] font-black text-emerald-500/80 uppercase tracking-widest">Core Synchronized</span>
            </div>
        </header>

        <div class="flex-1 overflow-y-auto p-8 space-y-8">
            <!-- ASSET RAIL -->
            <div class="panel p-5 flex items-center gap-5">
                <form action="/add_symbol" method="POST" class="pr-5 border-r border-white/10">
                    <input type="text" name="symbol" placeholder="+" class="w-16 bg-black border border-white/5 px-2 py-3 rounded-lg text-xs font-black outline-none focus:border-blue-500 text-center uppercase">
                </form>
                <div class="flex flex-wrap items-center gap-4" id="asset-rail"></div>
            </div>

            <div class="grid grid-cols-12 gap-8">
                <!-- EXECUTION STREAM -->
                <div class="col-span-12 lg:col-span-9">
                    <div class="panel">
                        <div class="px-8 py-6 border-b border-white/5 flex justify-between items-center bg-white/[0.01]">
                            <h3 class="text-xs font-black uppercase tracking-widest text-slate-500">Institutional Execution Stream</h3>
                            <span id="pos-count" class="text-xs font-bold text-blue-500 mono">0 ACTIVE</span>
                        </div>
                        <div id="positions-list" class="flex flex-col"></div>
                        <div id="no-positions" class="hidden py-40 text-center opacity-10"><i data-lucide="layers" class="w-20 h-20 mx-auto mb-6"></i><p class="text-sm font-black uppercase tracking-widest">Awaiting Institutional Entry Profile</p></div>
                    </div>
                </div>
                
                <div class="col-span-12 lg:col-span-3">
                    <div class="panel flex-1 max-h-[500px] flex flex-col">
                        <div class="px-8 py-5 border-b border-white/5"><h3 class="text-[10px] font-black uppercase tracking-widest text-slate-500">Core Telemetry</h3></div>
                        <div id="log-stream" class="p-6 flex-1 mono text-[11px] text-slate-600 overflow-y-auto space-y-2"></div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- FINY COPILOT CONSOLE -->
    <div id="finy-drawer" class="finy-drawer">
        <div class="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.03]">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center text-purple-400">
                    <i data-lucide="bot" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-base font-black text-white uppercase tracking-widest">Finy Copilot</h4>
                    <span class="text-[10px] font-bold text-purple-400 uppercase mono">Neural Sync: Active</span>
                </div>
            </div>
            <button onclick="toggleFiny()" class="text-slate-500 hover:text-white transition-colors"><i data-lucide="x" class="w-6 h-6"></i></button>
        </div>
        
        <div class="chat-area" id="finy-chat">
            <!-- Initial Message -->
            <div class="chat-msg msg-finy">
                Hi, I am your <b>Finy Agent</b>. I've finished synchronizing with your portfolio telemetry. Would you like to <b>dive into the markets</b> to see my real-time operations?
                <br>
                <button class="dive-btn" onclick="diveDeep()">Dive In</button>
            </div>
        </div>

        <div class="p-6 bg-[#030406] border-t border-white/5">
            <div class="flex gap-3">
                <input type="text" id="chat-input" placeholder="Query Finy Intelligence..." class="flex-1 bg-black/50 border border-white/10 p-4 rounded-xl text-sm text-white outline-none focus:border-purple-500/50">
                <button onclick="sendMessage()" class="bg-purple-600 px-5 rounded-xl text-white shadow-lg shadow-purple-500/20 hover:brightness-110 transition-all"><i data-lucide="send" class="w-5 h-5"></i></button>
            </div>
        </div>
    </div>

    <script>
        let expanded = new Set();
        let lastPrices = {};
        let finyOpen = false;

        function toggleFiny() {
            finyOpen = !finyOpen;
            document.getElementById('finy-drawer').classList.toggle('open', finyOpen);
            document.getElementById('finy-toggle').classList.toggle('active', finyOpen);
            lucide.createIcons();
        }

        function diveDeep() {
            const chat = document.getElementById('finy-chat');
            const diveMsg = document.createElement('div');
            diveMsg.className = 'chat-msg msg-finy w-full';
            diveMsg.innerHTML = `
                <span class="text-[10px] font-black uppercase text-purple-400 block mb-3">Live Intelligence Stream</span>
                <div class="activity-card mono text-[10px] text-slate-500 space-y-2">
                    <p class="text-emerald-500">[SYNC] MT5 Node Connected...</p>
                    <p>[SCAN] XAUUSDM: MTF Confluence Found (H1/M15)</p>
                    <p>[SCAN] EURUSDM: Neutral Sentiment detected</p>
                    <p class="text-purple-400">[RISK] Account Margin: 495,139% (STABLE)</p>
                    <p>[AUDIT] Live Position #83882 Audited by Finy Brain</p>
                </div>
            `;
            chat.appendChild(diveMsg);
            chat.scrollTop = chat.scrollHeight;
        }

        function sendMessage() {
            const input = document.getElementById('chat-input');
            const chat = document.getElementById('finy-chat');
            if(!input.value.trim()) return;
            
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-msg msg-user';
            userMsg.textContent = input.value;
            chat.appendChild(userMsg);
            
            setTimeout(() => {
                const finyMsg = document.createElement('div');
                finyMsg.className = 'chat-msg msg-finy';
                finyMsg.innerHTML = "I am processing your query against live market data. Current Portfolio Health is at 98%. Volatility on Gold is increasing—I am widening my scan parameters.";
                chat.appendChild(finyMsg);
                chat.scrollTop = chat.scrollHeight;
            }, 800);
            
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
        }

        async function updateData() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                
                let floatingPnL = data.positions.reduce((acc, p) => acc + p.profit, 0);
                const pnlEl = document.getElementById('live-pnl');
                pnlEl.textContent = (floatingPnL >= 0 ? '+' : '') + floatingPnL.toFixed(2);
                pnlEl.className = `text-xl font-black mono italic ${floatingPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`;

                if (data.account) {
                    document.getElementById('account-equity').textContent = '$' + data.account.equity.toLocaleString();
                    const mLvl = document.getElementById('margin-level');
                    mLvl.textContent = data.account.margin_level.toFixed(0) + '%';
                }

                const rail = document.getElementById('asset-rail');
                rail.innerHTML = data.live_data.map(sym => {
                    const diff = sym.price - (lastPrices[sym.symbol] || sym.price);
                    const pc = diff > 0 ? 'sq-up' : (diff < 0 ? 'sq-down' : 'sq-neutral');
                    lastPrices[sym.symbol] = sym.price;
                    return `
                        <div class="asset-tile">
                            <a href="/remove_symbol/${sym.symbol}" class="remove-trigger">✕</a>
                            <div class="flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full ${sym.price > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}"></span>
                                <span class="text-[11px] font-black text-white uppercase mono tracking-tight">${sym.symbol}</span>
                            </div>
                            <div class="price-sq ${pc}">${sym.price.toFixed(5)}</div>
                        </div>
                    `;
                }).join('');

                const posList = document.getElementById('positions-list');
                document.getElementById('pos-count').textContent = data.positions.length + ' ACTIVE';
                if (data.positions.length === 0) {
                    posList.innerHTML = '';
                    document.getElementById('no-positions').classList.remove('hidden');
                } else {
                    document.getElementById('no-positions').classList.add('hidden');
                    posList.innerHTML = data.positions.map(pos => `
                        <div class="pos-row p-6 flex justify-between items-center cursor-pointer" onclick="toggleLogic(${pos.ticket})">
                            <div class="flex items-center gap-10">
                                <div class="flex flex-col"><span class="text-sm font-black text-white uppercase tracking-tight">${pos.symbol}</span><span class="text-[10px] font-bold text-slate-600 mono">#${pos.ticket.toString().slice(-5)}</span></div>
                                <div class="flex flex-col"><span class="text-[10px] font-black text-slate-600 uppercase mb-1">Volume</span><span class="text-xs font-bold text-slate-300 mono">${pos.volume}L</span></div>
                                <div class="flex flex-col"><span class="text-[10px] font-black text-slate-600 uppercase mb-1">Risk Bounds</span><span class="text-xs font-bold text-slate-500 mono">${pos.sl} / ${pos.tp}</span></div>
                            </div>
                            <div class="text-right">
                                <span class="text-2xl font-black mono italic ${pos.profit > 0 ? 'text-emerald-400' : 'text-red-400'}">${pos.profit > 0 ? '+' : ''}${pos.profit.toFixed(2)}</span>
                            </div>
                            <div id="logic-${pos.ticket}" class="${expanded.has(pos.ticket) ? '' : 'hidden'} px-10 pb-8 pt-4">
                                <div class="grid grid-cols-12 gap-10 border-t border-white/5 pt-6">
                                    <div class="col-span-7">
                                        <div class="flex items-center gap-2 mb-4 text-purple-400"><i data-lucide="brain-circuit" class="w-5 h-5"></i><span class="text-[10px] font-black uppercase tracking-widest">Finy Audit Dossier</span></div>
                                        <p class="text-sm italic text-slate-300 leading-relaxed font-medium">"${pos.reason}"</p>
                                    </div>
                                    <div class="col-span-5 border-l border-white/5 pl-10">
                                        <h5 class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Autonomous Confluence</h5>
                                        <div class="mono text-xs text-blue-400 leading-loose">${pos.criteria}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');
                }

                const logs = document.getElementById('log-stream');
                logs.innerHTML = data.logs.map(l => `<p>${l}</p>`).join('');
                logs.scrollTop = logs.scrollHeight;

            } catch (e) { console.error("HUD Sync Failed", e); }
        }

        function toggleLogic(t) {
            if(expanded.has(t)) expanded.delete(t);
            else expanded.add(t);
            updateData();
            lucide.createIcons();
        }

        setInterval(updateData, 1000);
        updateData();
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
    <!DOCTYPE html><html><body style="background:#020305;color:white;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif">
    <div style="background:#090c14;padding:60px;border-radius:16px;border:1px solid #161c2b;text-align:center">
        <h1 style="text-transform:uppercase;margin-bottom:40px;letter-spacing:0.1em;font-weight:900">Axon<span style="color:#3b82f6">Algo</span></h1>
        <form action="/login" method="POST"><input type="password" name="password" style="background:black;border:1px solid #161c2b;padding:15px;color:white;border-radius:8px;text-align:center;width:250px" placeholder="AUTH_KEY"><br><br>
        <button style="background:#3b82f6;color:white;border:none;padding:15px 40px;border-radius:8px;font-weight:bold;cursor:pointer;width:100%">AUTHORIZE</button></form>
    </div></body></html>
    """)

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
    positions = []
    live_data = []
    account = None
    if mt5.initialize():
        acc_info = mt5.account_info()
        if acc_info:
            account = {"equity": acc_info.equity, "margin_level": acc_info.margin_level if acc_info.margin_level else 0.0}
        symbols = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
        for s in symbols:
            tick = mt5.symbol_info_tick(s)
            if tick: live_data.append({"symbol": s, "price": tick.bid})
        res = mt5.positions_get()
        if res:
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                for p in res:
                    db_trade = cursor.execute("SELECT reason, criteria FROM trades WHERE symbol = ? AND status = 'OPEN' ORDER BY id DESC LIMIT 1", (p.symbol,)).fetchone()
                    positions.append({
                        "ticket": p.ticket, "symbol": p.symbol, "volume": p.volume, "sl": p.sl, "tp": p.tp, "profit": round(p.profit, 2),
                        "reason": db_trade['reason'] if db_trade else "Direct Market Entry.",
                        "criteria": db_trade['criteria'] if db_trade else "MANUAL_EXECUTION"
                    })
    logs = []
    if os.path.exists("axon_bot.log"):
        with open("axon_bot.log", "r") as f:
            logs = f.readlines()[-20:]
    return jsonify({"metrics": db.get_metrics(), "live_data": live_data, "positions": positions, "account": account, "logs": logs})

@app.route('/update', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    db.update_system_settings(float(request.form['risk_pct']), request.form['trading_enabled'] == 'True', db.get_system_settings()['symbols'])
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
    target = symbol.strip()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip() and s.strip() != target]
    db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
