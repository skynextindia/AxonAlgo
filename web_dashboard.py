from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, Response
import json
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
import threading

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
    <title>FINTER | Node 01</title>
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
        /* Living UI Animations */
        @keyframes pulse-blue {
            0% { text-shadow: 0 0 5px rgba(59,130,246,0.2); opacity: 0.8; }
            50% { text-shadow: 0 0 15px rgba(59,130,246,0.6); opacity: 1; }
            100% { text-shadow: 0 0 5px rgba(59,130,246,0.2); opacity: 0.8; }
        }
        .pulse-status { animation: pulse-blue 2s infinite ease-in-out; }
        
        @keyframes grid-glow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        body {
            background: radial-gradient(circle at 50% 50%, #050505 0%, #000000 100%);
            overflow-x: hidden; height: 100vh; margin: 0; display: flex;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(45deg, transparent 48%, rgba(59,130,246,0.02) 50%, transparent 52%);
            background-size: 200% 200%;
            animation: grid-glow 15s infinite linear;
            pointer-events: none;
            z-index: -1;
        }

        .stat-value { font-family: 'JetBrains Mono', monospace; font-weight: 800; letter-spacing: -0.05em; }
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

        .led-pulse {
            animation: led-blink 1s infinite;
        }
        @keyframes led-blink {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
            100% { opacity: 1; transform: scale(1); }
        }
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
            <div class="stat"><div class="stat-label">Neural Status</div><div id="bot-action" class="stat-value text-blue-500 pulse-status">INITIALIZING...</div></div>
            <div class="stat"><div class="stat-label">Current Target</div><div id="bot-symbol" class="stat-value text-white">NONE</div></div>
            <div class="flex items-center ml-4 h-full">
                <canvas id="neural-wave" width="100" height="30" class="opacity-50"></canvas>
            </div>
            <div class="ml-auto mono text-[10px] text-gray-700">NODE_ID: FINTER_01_SECURE</div>
        </header>

        <div class="workspace">
            <!-- TERMINAL TAB -->
            <div id="tab-terminal" class="tab-content active space-y-6">
                <!-- TICKER -->
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">Asset Matrix</span>
                        <form action="/add_symbol" method="POST" class="flex gap-2">
                            <input type="text" name="symbol" placeholder="SYMBOL" class="bg-black border border-white/5 px-2 py-1 text-[10px] font-bold uppercase text-white outline-none focus:border-blue-500">
                            <button type="submit" class="bg-blue-600 text-white px-2 text-[10px] font-bold">+</button>
                        </form>
                    </div>
                    <div id="ticker-grid" class="ticker-grid"></div>
                </div>

                <div class="grid grid-cols-12 gap-6">
                    <!-- STRATEGY MATRIX -->
                    <div class="col-span-4 panel">
                        <div class="panel-header"><span class="panel-title">Neural Strategy Alignment Matrix</span></div>
                        <div id="strategy-matrix" class="p-4 grid grid-cols-3 gap-3">
                            <!-- Layer 1 -->
                            <div id="layer-L1_TREND" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-600 uppercase tracking-widest">L1: Daily Trend</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[13px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 2 -->
                            <div id="layer-L2_STRUCTURE" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L2: SMC Zone</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 3 -->
                            <div id="layer-L3_EMA" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L3: EMA 50</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 4 -->
                            <div id="layer-L4_MOMENTUM" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L4: RSI Pullback</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 5 -->
                            <div id="layer-L5_CANDLE" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L5: Candle Pattern</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 6 -->
                            <div id="layer-L6_VOLATILITY" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L6: ATR Volatility</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 7 -->
                            <div id="layer-L7_SPREAD" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L7: Spread</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 8 -->
                            <div id="layer-L8_NEWS" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L8: News Filter</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                            <!-- Layer 9 -->
                            <div id="layer-L9_RR" class="flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg opacity-40">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">L9: Risk/Reward</span>
                                    <div class="dot w-2 h-2 rounded-full bg-gray-700"></div>
                                </div>
                                <div class="val text-[11px] font-black text-gray-700 mono tracking-tighter">---</div>
                                <div class="status text-[8px] font-bold text-gray-800 uppercase mt-1">STATUS: PENDING</div>
                            </div>
                        </div>
                    </div>
                    <!-- TRADES -->
                    <div class="col-span-5 panel">
                        <div class="panel-header"><span class="panel-title">Execution Hub</span><span id="pos-count" class="mono text-[10px]">0_ACTIVE</span></div>
                        <div id="positions-list" class="flex-1 p-4 space-y-2"></div>
                    </div>
                    <!-- LOGS / EVENTS -->
                    <div class="col-span-3 space-y-6">
                        <div class="panel">
                            <div class="panel-header"><span class="panel-title">Internal Planning</span></div>
                            <div id="planning-log" class="p-4 space-y-3 overflow-y-auto" style="height: 120px;"></div>
                        </div>
                        <div class="panel">
                            <div class="panel-header"><span class="panel-title">Macro Sentiment</span></div>
                            <div id="events-stream" class="p-4 space-y-3 overflow-y-auto" style="height: 150px;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- LAB TAB -->
            <div id="tab-lab" class="tab-content space-y-6">
                <div class="grid grid-cols-3 gap-6">
                    <div class="panel p-4 text-center">
                        <div class="stat-label">Neural Win Rate</div>
                        <div id="stat-winrate" class="text-2xl font-black text-emerald-500 mono">0.0%</div>
                    </div>
                    <div class="panel p-4 text-center">
                        <div class="stat-label">Total Probations</div>
                        <div id="stat-total" class="text-2xl font-black text-white mono">0</div>
                    </div>
                    <div class="panel p-4 text-center">
                        <div class="stat-label">Avg Neural Edge</div>
                        <div id="stat-avg" class="text-2xl font-black text-blue-500 mono">0.00</div>
                    </div>
                </div>
                <div class="panel">
                    <div class="panel-header"><span class="panel-title">Neural Observations (Rejected Trades)</span></div>
                    <div class="p-4">
                        <p class="text-xs text-gray-500 mb-4">Trades blocked by Finy.AI due to insufficient alpha or macro-conflicts.</p>
                        <div id="observations-list" class="space-y-2"></div>
                    </div>
                </div>
            </div>

            <!-- SETTINGS TAB -->
            <div id="tab-settings" class="tab-content space-y-6">
                <div class="panel max-w-md mx-auto mt-10">
                    <div class="panel-header"><span class="panel-title">Core System Settings</span></div>
                    <form action="/update_settings" method="POST" class="p-6 space-y-6">
                        <div>
                            <label class="block text-[10px] font-bold text-gray-500 uppercase mb-2">Trading Enabled</label>
                            <select name="trading_enabled" class="w-full bg-black border border-white/10 p-2 text-white outline-none">
                                <option value="1">ACTIVE (LIVE TRADING)</option>
                                <option value="0">SAFE MODE (SCAN ONLY)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-gray-500 uppercase mb-2">Min Alpha Score (Confidence)</label>
                            <input type="number" step="0.01" name="min_alpha" class="w-full bg-black border border-white/10 p-2 text-white outline-none" placeholder="e.g. 0.75">
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-gray-500 uppercase mb-2">Risk Per Trade (%)</label>
                            <input type="number" step="0.01" name="risk_pct" class="w-full bg-black border border-white/10 p-2 text-white outline-none" placeholder="e.g. 1.0">
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs py-3 uppercase tracking-widest transition-colors">Apply Settings</button>
                    </form>
                </div>
            </div>
        </div>
    </main>

    <!-- FINY.AI SIDEBAR -->
    <aside class="sidebar" style="width: 280px; border-right: none; border-left: 1px solid var(--border); padding: 1.5rem; justify-content: flex-start; align-items: flex-start;">
        <div class="flex items-center gap-2 mb-6 w-full border-b border-white/10 pb-4">
            <i data-lucide="brain" class="text-emerald-500"></i>
            <span class="text-[11px] font-black text-white uppercase tracking-widest">Finy.AI Assistant</span>
            <div class="ml-auto w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
        </div>
        <p id="finy-thought-container" class="text-[11px] text-gray-400 italic leading-relaxed mb-6">"Monitoring live order flow and macroeconomic confluences across all node assets. Standing by."</p>
        
        <div class="w-full">
            <span class="text-[9px] font-bold text-gray-500 uppercase mb-2 block">System Settings</span>
            <div id="finy-settings-status" class="text-[10px] mono text-blue-400 mb-6 bg-white/[0.02] p-2 rounded border border-white/5">LOADING...</div>
            
            <span class="text-[9px] font-bold text-gray-500 uppercase mb-2 block">Quick Demo Execution</span>
            <div class="bg-white/[0.02] border border-white/5 p-3 rounded mb-6">
                <select id="demo-symbol-select" class="w-full bg-black border border-white/10 text-[10px] text-white p-2 mb-2 outline-none">
                    <option value="XAUUSDm">XAUUSD (Gold)</option>
                    <option value="EURUSDm">EURUSD (Euro)</option>
                    <option value="BTCUSDm">BTCUSD (Bitcoin)</option>
                </select>
                <button onclick="if(confirm('WARNING: This will execute a LIVE test order (0.01 lots) on your MT5 terminal. Proceed?')) triggerDemo(document.getElementById('demo-symbol-select').value)" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[9px] py-2 uppercase tracking-widest transition-all mb-2">Execute Test Order</button>
                <button onclick="closeAllTrades()" class="w-full bg-red-600/20 hover:bg-red-600/40 text-red-500 font-bold text-[9px] py-2 uppercase tracking-widest transition-all border border-red-500/30">Close All Positions</button>
            </div>

            <span class="text-[9px] font-bold text-gray-500 uppercase mb-2 block">Live AI Feed</span>
            <div id="finy-stream" class="space-y-3 overflow-y-auto mb-6" style="max-height: 250px;">
                <!-- Live insights injected here -->
            </div>

            <!-- CHAT INTERFACE -->
            <div class="border-t border-white/10 pt-4 mt-auto">
                <span class="text-[9px] font-bold text-gray-500 uppercase mb-2 block">Chat with Finy.AI</span>
                <div id="chat-box" class="h-32 overflow-y-auto text-[10px] space-y-2 mb-3 mono text-gray-400">
                    <div>Finy.AI: System online. How can I help?</div>
                </div>
                <div class="flex gap-2">
                    <input type="text" id="chat-input" placeholder="Type message..." class="flex-1 bg-black border border-white/10 p-2 text-[10px] text-white outline-none focus:border-blue-500">
                    <button onclick="sendChat()" class="bg-blue-600 px-3 text-[10px] text-white font-bold">SEND</button>
                </div>
            </div>
        </div>
    </aside>

    <div id="scan-modal" class="modal" onclick="this.classList.remove('active')">
        <div class="modal-box" onclick="event.stopPropagation()" id="scan-content"></div>
    </div>

    <script>
        let selectedSymbol = 'BTCUSDm';
        let lastPrices = {};

        function selectSymbol(sym) {
            selectedSymbol = sym;
            updateHUD();
        }

        async function updateHUD() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                
                document.getElementById('acc-equity').textContent = '$' + data.account.equity.toLocaleString();
                let pnl = data.positions.reduce((a, b) => a + b.profit, 0);
                document.getElementById('acc-pnl').textContent = (pnl >= 0 ? '+' : '') + pnl.toFixed(2);
                document.getElementById('acc-pnl').className = `stat-value ${pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`;

                // Ticker (Only if changed to prevent flicker)
                const ticker = document.getElementById('ticker-grid');
                const newTickerHTML = data.live_data.map(s => {
                    let isScanning = (data.bot_status && data.bot_status.current_symbol === s.symbol);
                    let isSelected = (selectedSymbol === s.symbol);
                    let borderClass = isSelected ? 'border-2 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'border-t border-white/5';
                    let bgClass = isSelected ? 'bg-blue-900/10' : 'bg-black';
                    let colorClass = 'text-white';
                    let priceDiff = '';
                    
                    if (lastPrices[s.symbol]) {
                        if (s.price > lastPrices[s.symbol]) {
                            colorClass = 'text-emerald-500';
                            bgClass = isSelected ? 'bg-emerald-900/20' : 'bg-emerald-950/20 hover:bg-emerald-900/30';
                            priceDiff = '▲';
                        } else if (s.price < lastPrices[s.symbol]) {
                            colorClass = 'text-red-500';
                            bgClass = isSelected ? 'bg-red-900/20' : 'bg-red-950/20 hover:bg-red-900/30';
                            priceDiff = '▼';
                        }
                    }
                    lastPrices[s.symbol] = s.price;
                    
                    return `
                    <div class="ticker-item ${bgClass} ${borderClass} cursor-pointer" onclick="selectSymbol('${s.symbol}')">
                        <a href="/remove_symbol/${s.symbol}" class="remove-btn" onclick="event.stopPropagation()">✕</a>
                        <div class="text-[10px] font-black text-gray-500 uppercase flex justify-between">
                            <span>${s.symbol}</span>
                            <span class="${colorClass}">${priceDiff} ${isScanning ? '● SCANNING' : ''}</span>
                        </div>
                        <div class="flex justify-between items-end mt-2">
                            <div class="price-val ${colorClass} m-0">${s.price.toFixed(5)}</div>
                            <div class="text-[9px] font-bold ${s.day_change > 0 ? 'text-emerald-500' : s.day_change < 0 ? 'text-red-500' : 'text-gray-600'}">${s.day_change}%</div>
                        </div>
                    </div>
                    `;
                }).join('');
                
                if (ticker.innerHTML !== newTickerHTML) {
                    ticker.innerHTML = newTickerHTML;
                }

                // Trades
                const list = document.getElementById('positions-list');
                document.getElementById('pos-count').textContent = data.positions.length + '_ACTIVE';
                list.innerHTML = data.positions.map(p => `
                    <div class="p-2 mb-1 bg-white/[0.02] border border-white/5 rounded flex flex-col gap-1">
                        <div class="flex justify-between items-center">
                            <div class="flex items-center gap-2">
                                <span class="text-[8px] font-black px-1 rounded ${p.type === 'BUY' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}">${p.type}</span>
                                <span class="text-[10px] font-black text-white uppercase">${p.symbol}</span>
                            </div>
                            <div class="text-[11px] font-black mono ${p.profit >= 0 ? 'text-emerald-500' : 'text-red-500'}">
                                ${p.profit >= 0 ? '+' : ''}${p.profit.toFixed(2)}
                            </div>
                        </div>
                        <div class="flex justify-between items-center text-[8px] mono text-gray-600">
                            <span>ENTRY: ${p.price_open.toFixed(5)}</span>
                            <span>SL: ${p.sl > 0 ? p.sl.toFixed(5) : 'NONE'}</span>
                            <span>TP: ${p.tp > 0 ? p.tp.toFixed(5) : 'NONE'}</span>
                        </div>
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

                // Finy Settings Status
                if (data.settings) {
                    const statusStr = (data.settings.trading_enabled == 1) ? '<span class="text-emerald-500">LIVE</span>' : '<span class="text-red-500">SAFE MODE</span>';
                    document.getElementById('finy-settings-status').innerHTML = `MODE: ${statusStr} | RISK: ${data.settings.risk_pct}%`;
                    const riskInput = document.querySelector('input[name="risk_pct"]');
                    if(document.activeElement !== riskInput) riskInput.value = data.settings.risk_pct;
                    const modeSelect = document.querySelector('select[name="trading_enabled"]');
                    if(document.activeElement !== modeSelect) modeSelect.value = data.settings.trading_enabled;
                    const alphaInput = document.querySelector('input[name="min_alpha"]');
                    if(document.activeElement !== alphaInput) alphaInput.value = data.settings.min_alpha_score;
                }

                // Finy Observations
                if (data.observations) {
                    const obsHTML = data.observations.map(o => `
                        <div class="border border-white/5 bg-white/[0.02] p-3 rounded mb-2">
                            <div class="flex justify-between mb-1">
                                <span class="text-[10px] font-black uppercase text-${o.direction === 'BUY' ? 'emerald' : 'red'}-500">${o.symbol} ${o.direction}</span>
                                <span class="text-[9px] mono text-blue-400">FINY.AI: ${o.finy}</span>
                            </div>
                            <div class="text-[10px] text-gray-400 font-medium">REJECT: ${o.reason}</div>
                            <div class="text-[9px] text-gray-600 mono mt-1">${o.time}</div>
                        </div>
                    `).join('');
                    document.getElementById('observations-list').innerHTML = obsHTML || '<div class="text-xs text-gray-600 italic">No rejected trades.</div>';
                    document.getElementById('finy-stream').innerHTML = obsHTML || '<div class="text-xs text-gray-600 italic">No neural insights.</div>';
                }

                // Stats & Thoughts
                if (data.stats) {
                    document.getElementById('stat-winrate').textContent = (data.stats.win_rate || 0) + '%';
                    document.getElementById('stat-total').textContent = data.stats.total_trades || 0;
                    document.getElementById('stat-avg').textContent = (data.stats.avg_profit || 0).toFixed(2);
                }
                if (data.finy_thought) {
                    document.getElementById('finy-thought-container').innerHTML = `"${data.finy_thought}"`;
                }

                // Bot Status & Strategy Alignment
                if (data.bot_status) {
                    const statusEl = document.getElementById('bot-action');
                    statusEl.textContent = data.bot_status.current_action;
                    document.getElementById('bot-symbol').textContent = data.bot_status.current_symbol;
                    
                    const planningEl = document.getElementById('planning-log');
                    planningEl.innerHTML = `
                        <div class="border-l-2 border-emerald-500 pl-3 py-1">
                            <div class="text-[10px] text-white font-bold uppercase">${data.bot_status.current_action}</div>
                            <div class="text-[11px] text-gray-400 mt-1">${data.bot_status.planning_notes}</div>
                            <div class="text-[9px] text-gray-600 mt-1 mono">${data.bot_status.last_updated}</div>
                        </div>
                    `;

                    // Update Strategy Matrix (Fine-grained to prevent flicker)
                    if (data.bot_status.strategy_alignment) {
                        try {
                            const alignment = JSON.parse(data.bot_status.strategy_alignment);
                            const indicators = data.bot_status.current_indicators ? JSON.parse(data.bot_status.current_indicators) : {};
                            const isSelectedScanning = (selectedSymbol.toLowerCase() === data.bot_status.current_symbol.toLowerCase());
                            
                            const layerMap = {
                                "L1_TREND": "TREND",
                                "L2_STRUCTURE": "SMC",
                                "L3_EMA": "EMA",
                                "L4_MOMENTUM": "RSI",
                                "L5_CANDLE": "PA",
                                "L6_VOLATILITY": "ATR",
                                "L7_SPREAD": "SPREAD",
                                "L8_NEWS": "NEWS",
                                "L9_RR": "RR"
                            };
                            
                            for (let [layerId, indKey] of Object.entries(layerMap)) {
                                const el = document.getElementById(`layer-${layerId}`);
                                if (!el) continue;
                                
                                const status = isSelectedScanning ? (alignment[layerId] || "PENDING") : "STALE";
                                const dot = el.querySelector('.dot');
                                const val = el.querySelector('.val');
                                const statusTxt = el.querySelector('.status');
                                
                                // Update Visuals
                                if (status === 'PASS') {
                                    dot.className = 'dot w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]';
                                    val.className = 'val text-[13px] font-black text-blue-400 mono tracking-tighter';
                                    statusTxt.className = 'status text-[8px] font-bold text-emerald-600 uppercase mt-1';
                                    el.className = 'flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg transition-all duration-300';
                                } else if (status === 'FAIL') {
                                    dot.className = 'dot w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]';
                                    val.className = 'val text-[13px] font-black text-blue-400 mono tracking-tighter';
                                    statusTxt.className = 'status text-[8px] font-bold text-red-900 uppercase mt-1';
                                    el.className = 'flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg transition-all duration-300';
                                } else {
                                    dot.className = 'dot w-2 h-2 rounded-full bg-gray-700';
                                    val.className = 'val text-[13px] font-black text-gray-700 mono tracking-tighter';
                                    statusTxt.className = 'status text-[8px] font-bold text-gray-800 uppercase mt-1';
                                    el.className = 'flex flex-col p-3 bg-white/[0.01] opacity-40 border border-white/10 rounded-lg';
                                }

                                const indVal = (isSelectedScanning && indKey && indicators[indKey]) ? indicators[indKey] : '---';
                                if (val.textContent !== String(indVal)) val.textContent = indVal;
                                if (statusTxt.textContent !== `STATUS: ${status}`) statusTxt.textContent = `STATUS: ${status}`;
                            }
                        } catch (e) { console.error("Alignment parse fail", e); }
                    }
                }

            } catch (e) { console.error("Sync_Fail", e); }
        }

        document.getElementById('chat-input')?.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendChat();
        });

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const box = document.getElementById('chat-box');
            const msg = input.value.trim();
            if(!msg) return;
            
            box.innerHTML += `<div class="text-white">You: ${msg}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                box.innerHTML += `<div class="text-emerald-500">Finy.AI: ${data.response}</div>`;
                box.scrollTop = box.scrollHeight;
            } catch (e) { console.error(e); }
        }

        function switchTab(id, el) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            const target = document.getElementById('tab-'+id);
            if(target) target.classList.add('active');
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
                    content.innerHTML = `<div class="p-4 text-red-500">Error: ${data.error}</div>`;
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
                        <p class="text-xs text-gray-400 italic font-medium leading-relaxed mb-6">"${data.ai_text}"</p>
                        <button onclick="triggerDemo('${sym}')" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] py-3 uppercase tracking-widest transition-all">Trigger Neural Execution [DEMO]</button>
                    </div>
                `;
            } catch (err) { console.error(err); }
        }

        async function triggerDemo(sym) {
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = "EXECUTING...";
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/trigger_demo/' + sym);
                const data = await res.json();
                if(data.success) {
                    btn.innerText = "SUCCESS: " + data.message;
                    btn.className = "w-full bg-emerald-500 text-white font-bold text-[10px] py-3 uppercase tracking-widest";
                } else {
                    btn.innerText = "FAILED: " + data.error;
                    btn.className = "w-full bg-red-600 text-white font-bold text-[10px] py-3 uppercase tracking-widest";
                }
            } catch (e) { 
                btn.innerText = "ERROR";
            } finally {
                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.disabled = false;
                    btn.className = "w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] py-3 uppercase tracking-widest";
                }, 3000);
            }
        }

        async function closeAllTrades() {
            if(!confirm('This will CLOSE ALL active positions. Are you sure?')) return;
            try {
                const res = await fetch('/api/close_all');
                const data = await res.json();
                alert(data.message || data.error);
                updateHUD();
            } catch (e) { console.error(e); }
        }

        // SSE Real-Time Stream (Institutional Grade)
        const source = new EventSource('/stream');
        
        source.onmessage = function(event) {
            const data = JSON.parse(event.data);
            processUpdate(data);
        };

        function processUpdate(data) {
            try {
                document.getElementById('acc-equity').textContent = '$' + data.account.equity.toLocaleString();
                let pnl = data.positions.reduce((a, b) => a + b.profit, 0);
                document.getElementById('acc-pnl').textContent = (pnl >= 0 ? '+' : '') + pnl.toFixed(2);
                document.getElementById('acc-pnl').className = `stat-value ${pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`;

                // Bot Status Bar
                document.getElementById('bot-action').textContent = data.bot_status.current_action;
                document.getElementById('bot-symbol').textContent = data.bot_status.current_symbol;

                // Ticker (Fine-Grained)
                const tickerGrid = document.getElementById('ticker-grid');
                data.live_data.forEach(s => {
                    let item = document.getElementById(`ticker-item-${s.symbol}`);
                    const botSym = (data.bot_status.current_symbol || "").trim().toLowerCase();
                    const curSym = (s.symbol || "").trim().toLowerCase();
                    const selSym = (selectedSymbol || "").trim().toLowerCase();
                    
                    let isScanning = (botSym === curSym && botSym !== "none" && botSym !== "");
                    let isSelected = (selSym === curSym);
                    
                    if (!item) {
                        // Create item if missing
                        const div = document.createElement('div');
                        div.id = `ticker-item-${s.symbol}`;
                        div.onclick = () => selectSymbol(s.symbol);
                        div.className = `ticker-item cursor-pointer bg-black border-t border-white/5`;
                        div.innerHTML = `
                            <a href="/remove_symbol/${s.symbol}" class="remove-btn" onclick="event.stopPropagation()">✕</a>
                            <div class="text-[10px] font-black text-gray-500 uppercase flex justify-between items-center">
                                <div class="flex items-center gap-2">
                                    <span>${s.symbol}</span>
                                    <span id="ticker-change-${s.symbol}" class="text-[8px] font-bold">0.00%</span>
                                </div>
                                <div id="ticker-scan-${s.symbol}" class="w-1.5 h-1.5 rounded-full bg-gray-800"></div>
                            </div>
                            <div class="flex justify-between items-end mt-2">
                                <div class="flex items-center gap-1">
                                    <span id="ticker-arrow-${s.symbol}" class="text-[8px] w-2"></span>
                                    <div id="ticker-price-${s.symbol}" class="price-val text-white m-0">0.00000</div>
                                </div>
                            </div>
                        `;
                        tickerGrid.appendChild(div);
                        item = div;
                    }

                    // Update values
                    const priceEl = document.getElementById(`ticker-price-${s.symbol}`);
                    const changeEl = document.getElementById(`ticker-change-${s.symbol}`);
                    const scanEl = document.getElementById(`ticker-scan-${s.symbol}`);
                    const arrowEl = document.getElementById(`ticker-arrow-${s.symbol}`);
                    
                    let colorClass = 'text-white';
                    let priceDiff = '';
                    let dotColor = 'bg-gray-800';
                    let bgClass = isSelected ? 'bg-blue-900/10' : 'bg-black';
                    
                    if (lastPrices[s.symbol]) {
                        if (s.price > lastPrices[s.symbol]) { 
                            colorClass = 'text-emerald-400'; 
                            priceDiff = '▲'; 
                            dotColor = isScanning ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-gray-800';
                            bgClass = isSelected ? 'bg-emerald-900/30' : 'bg-emerald-950/20';
                        }
                        else if (s.price < lastPrices[s.symbol]) { 
                            colorClass = 'text-red-400'; 
                            priceDiff = '▼'; 
                            dotColor = isScanning ? 'bg-red-500 shadow-[0_0_5px_#ef4444]' : 'bg-gray-800';
                            bgClass = isSelected ? 'bg-red-900/30' : 'bg-red-950/20';
                        }
                    } else if (isScanning) {
                        dotColor = 'bg-blue-500 shadow-[0_0_5px_#3b82f6]';
                    }
                    lastPrices[s.symbol] = s.price;

                    if (priceEl.textContent !== s.price.toFixed(5)) {
                        priceEl.textContent = s.price.toFixed(5);
                        priceEl.className = `price-val ${colorClass} m-0`;
                    }
                    if (arrowEl.textContent !== priceDiff) {
                        arrowEl.textContent = priceDiff;
                        arrowEl.className = `text-[8px] w-2 ${colorClass}`;
                    }
                    if (changeEl.textContent !== s.day_change + '%') {
                        changeEl.textContent = s.day_change + '%';
                        changeEl.className = `text-[8px] font-bold ${s.day_change > 0 ? 'text-emerald-500' : s.day_change < 0 ? 'text-red-500' : 'text-gray-600'}`;
                    }
                    
                    const scanClass = `w-1.5 h-1.5 rounded-full ${dotColor} ${isScanning ? 'led-pulse' : ''}`;
                    if (scanEl.className !== scanClass) {
                        scanEl.className = scanClass;
                    }

                    // Highlight Selection & Directional BG
                    let borderClass = isSelected ? 'border-2 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'border-t border-white/5';
                    if (item.className !== `ticker-item cursor-pointer ${bgClass} ${borderClass}`) {
                        item.className = `ticker-item cursor-pointer ${bgClass} ${borderClass}`;
                    }
                });

                // Strategy Matrix (Persistent per Asset)
                let targetStatus = null;
                if (data.symbol_statuses) {
                    const sel = (selectedSymbol || "").trim().toLowerCase();
                    const key = Object.keys(data.symbol_statuses).find(k => k.toLowerCase() === sel);
                    if (key) targetStatus = data.symbol_statuses[key];
                }

                if (targetStatus) {
                    const alignment = JSON.parse(targetStatus.strategy_alignment || "{}");
                    const indicators = targetStatus.current_indicators ? JSON.parse(targetStatus.current_indicators) : {};
                    const botSym = (data.bot_status.current_symbol || "").trim().toLowerCase();
                    const isScanning = (botSym === (selectedSymbol || "").toLowerCase());
                    
                    const layerMap = {
                        "L1_TREND": "TREND", "L2_STRUCTURE": "SMC", "L3_EMA": "EMA",
                        "L4_MOMENTUM": "RSI", "L5_CANDLE": "PA", "L6_VOLATILITY": "ATR",
                        "L7_SPREAD": "SPREAD", "L8_NEWS": "NEWS", "L9_RR": "RR"
                    };
                    
                    for (let [layerId, indKey] of Object.entries(layerMap)) {
                        const el = document.getElementById(`layer-${layerId}`);
                        if (!el) continue;
                        const status = alignment[layerId] || "PENDING";
                        const dot = el.querySelector('.dot');
                        const val = el.querySelector('.val');
                        const statusTxt = el.querySelector('.status');
                        
                        if (status === 'PASS') {
                            dot.className = 'dot w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]';
                            val.className = 'val text-[13px] font-black text-blue-400 mono tracking-tighter';
                            statusTxt.className = 'status text-[8px] font-bold text-emerald-600 uppercase mt-1';
                            el.className = 'flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg transition-all duration-300';
                        } else if (status === 'FAIL') {
                            dot.className = 'dot w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]';
                            val.className = 'val text-[13px] font-black text-blue-400 mono tracking-tighter';
                            statusTxt.className = 'status text-[8px] font-bold text-red-900 uppercase mt-1';
                            el.className = 'flex flex-col p-3 bg-white/[0.02] border border-white/10 rounded-lg transition-all duration-300';
                        } else {
                            dot.className = 'dot w-2 h-2 rounded-full bg-gray-700';
                            val.className = 'val text-[13px] font-black text-gray-700 mono tracking-tighter';
                            statusTxt.className = 'status text-[8px] font-bold text-gray-800 uppercase mt-1';
                            el.className = 'flex flex-col p-3 bg-white/[0.01] opacity-40 border border-white/10 rounded-lg';
                        }
                        const indVal = (indKey && indicators[indKey]) ? indicators[indKey] : '---';
                        if (val.textContent !== String(indVal)) val.textContent = indVal;
                        if (statusTxt.textContent !== `STATUS: ${status}`) statusTxt.textContent = `STATUS: ${status}`;
                    }
                }

                // Internal Planning (Only if changed)
                const planningLog = document.getElementById('planning-log');
                const logEntry = `
                    <div class="flex flex-col gap-1 border-l-2 border-blue-500 pl-3 bg-blue-900/5 p-2 rounded">
                        <span class="text-[10px] font-black text-blue-400 uppercase">${data.bot_status.current_action}</span>
                        <span class="text-[9px] text-gray-400">${data.bot_status.planning_notes}</span>
                        <span class="text-[8px] text-gray-600">${new Date().toLocaleTimeString()}</span>
                    </div>
                `;
                if (planningLog.dataset.lastAction !== data.bot_status.current_action) {
                    planningLog.innerHTML = logEntry + planningLog.innerHTML;
                    planningLog.dataset.lastAction = data.bot_status.current_action;
                }

                // Positions
                if (data.positions) {
                    const posList = document.getElementById('positions-list');
                    posList.innerHTML = data.positions.map(p => `
                        <div class="flex justify-between items-center bg-white/[0.03] border border-white/5 p-3 rounded hover:bg-white/[0.05] transition-all">
                            <div>
                                <div class="text-[10px] font-black text-white">${p.symbol} <span class="${p.type.includes('BUY') ? 'text-emerald-500' : 'text-red-500'}">${p.type}</span></div>
                                <div class="text-[9px] text-gray-500">Price: ${p.price_open.toFixed(5)} | SL: ${p.sl.toFixed(5)}</div>
                            </div>
                            <div class="text-xs font-black mono ${p.profit >= 0 ? 'text-emerald-500' : 'text-red-500'}">${p.profit >= 0 ? '+' : ''}${p.profit.toFixed(2)}</div>
                        </div>
                    `).join('');
                    document.getElementById('pos-count').textContent = `${data.positions.length}_ACTIVE`;
                }

                // Observations
                if (data.observations) {
                    const obsList = document.getElementById('observations-list');
                    obsList.innerHTML = data.observations.map(o => `
                        <div class="flex justify-between items-center bg-white/[0.02] border border-white/5 p-2 rounded opacity-80">
                            <div class="text-[9px]">
                                <span class="font-bold text-blue-400">${o.symbol}</span> 
                                <span class="text-gray-500">${o.reason.substring(0, 30)}...</span>
                            </div>
                            <div class="text-[9px] font-black text-gray-600">${o.finy} ALPHA</div>
                        </div>
                    `).join('');
                }

                // Macro Feed
                if (data.news) {
                    const eventsStream = document.getElementById('events-stream');
                    eventsStream.innerHTML = data.news.map(n => `
                        <div class="border-l border-white/10 pl-3 py-1">
                            <div class="text-[10px] text-gray-300 font-bold leading-tight">${n.title}</div>
                            <div class="text-[8px] text-gray-600 mt-1">${n.published}</div>
                        </div>
                    `).join('');
                }

                // Stats
                if (data.stats) {
                    document.getElementById('stat-winrate').textContent = (data.stats.win_rate || 0) + '%';
                    document.getElementById('stat-total').textContent = data.stats.total_trades || 0;
                    document.getElementById('stat-avg').textContent = (data.stats.avg_profit || 0).toFixed(2);
                }

                // Settings Panel
                if (data.settings) {
                    const statusText = data.settings.trading_enabled ? 'LIVE' : 'SAFE MODE';
                    const statusColor = data.settings.trading_enabled ? 'text-emerald-500' : 'text-blue-500';
                    const settingsHTML = `
                        <div class="p-3 bg-white/[0.02] border border-white/5 rounded mt-4">
                            <div class="text-[9px] font-bold text-gray-600 uppercase">System Context</div>
                            <div class="text-[11px] font-black ${statusColor} mt-1">${statusText} | RISK: ${data.settings.risk_pct}%</div>
                        </div>
                    `;
                    const container = document.getElementById('settings-context-box') || document.createElement('div');
                    container.id = 'settings-context-box';
                    container.innerHTML = settingsHTML;
                    if (!document.getElementById('settings-context-box')) {
                        document.querySelector('.sidebar').appendChild(container);
                    }
                }

            } catch (e) { console.error("Stream process fail", e); }
        }
        updateHUD();
        lucide.createIcons();
        // Neural Wave Animation
        const canvas = document.getElementById('neural-wave');
        const ctx = canvas.getContext('2d');
        let waveStep = 0;
        
        function animateWave() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.beginPath();
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#3b82f6';
            
            const isActive = document.getElementById('bot-action').textContent !== 'AWAITING_PULSE';
            const speed = isActive ? 0.2 : 0.05;
            const amplitude = isActive ? 10 : 3;
            
            for (let x = 0; x < canvas.width; x++) {
                const y = 15 + Math.sin(x * 0.1 + waveStep) * amplitude;
                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            
            ctx.stroke();
            waveStep += speed;
            requestAnimationFrame(animateWave);
        }
        animateWave();
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
        <h1 style="text-transform:uppercase;margin-bottom:30px;letter-spacing:0.2em;font-weight:900;font-size:18px">Finter<span style="color:#3b82f6">.AI</span></h1>
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

# Caching for high-frequency stream
STREAM_CACHE = {
    "news": [], "stats": {}, "observations": [], "last_heavy_fetch": 0
}

def background_fetcher():
    """Heavy data fetcher running in a background thread."""
    global STREAM_CACHE
    while True:
        try:
            # 1. Fetch News
            STREAM_CACHE["news"] = fetch_market_news()
            
            # 2. Fetch DB Stats
            conn = sqlite3.connect("axon_trading.db")
            c = conn.cursor()
            c.execute("SELECT COUNT(*), SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END), AVG(pnl) FROM trades")
            row = c.fetchone()
            if row and row[0]:
                STREAM_CACHE["stats"] = {
                    "total_trades": int(row[0]),
                    "win_rate": round((float(row[1] or 0) / float(row[0])) * 100, 1),
                    "avg_profit": round(float(row[2] or 0), 2)
                }
            # 3. Fetch Observations
            c.execute("SELECT symbol, direction, entry_price, finy_score, reason, timestamp FROM observations ORDER BY timestamp DESC LIMIT 10")
            STREAM_CACHE["observations"] = [{
                "symbol": r[0], "direction": r[1], "price": r[2], "finy": r[3], "reason": r[4], "time": r[5]
            } for r in c.fetchall()]
            conn.close()
        except Exception as e:
            print("Background Fetcher Error:", e)
        time.sleep(30) # Refresh every 30s in background

# Start background thread
threading.Thread(target=background_fetcher, daemon=True).start()

def get_data_bundle():
    global STREAM_CACHE
    settings_row = db.get_system_settings()
    settings = dict(settings_row)
    positions = []
    live_data = []
    account = {"equity": 0}
    
    # 1. Market Data
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
                positions.append({
                    "ticket": p.ticket, "symbol": p.symbol, "volume": p.volume, 
                    "profit": round(p.profit, 2), "price_open": p.price_open,
                    "sl": p.sl, "tp": p.tp, "type": "BUY" if p.type == 0 else "SELL"
                })

    bot_status_row = db.get_bot_status()
    bot_status = dict(bot_status_row) if bot_status_row else None
    all_symbol_statuses = db.get_all_symbol_statuses()

    return {
        "live_data": live_data, 
        "positions": positions, 
        "account": account, 
        "bot_status": bot_status,
        "symbol_statuses": all_symbol_statuses,
        "settings": settings,
        "news": STREAM_CACHE["news"],
        "stats": STREAM_CACHE["stats"],
        "observations": STREAM_CACHE["observations"]
    }

@app.route('/stream')
def stream():
    if not session.get('logged_in'): return "Unauthorized", 401
    def event_stream():
        while True:
            data = get_data_bundle()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.3)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    msg = request.json.get('message', '').lower()
    settings = dict(db.get_system_settings())
    
    if "status" in msg or "running" in msg:
        resp = f"Core systems operational. Neural scans active on {settings['symbols']}."
    elif "profit" in msg or "pnl" in msg:
        resp = "PNL is tracked in real-time. Neural focus is on trend-confluence for optimization."
    elif "market" in msg:
        resp = "Sentiment is mixed. Volatility levels are fluctuating. Higher probability setups in indices currently."
    elif "who are you" in msg or "finy" in msg:
        resp = "I am Finy.AI, your Neural Trading Assistant. I monitor institutional flows and macroeconomic vectors."
    else:
        resp = "Neural engine processing query. Recommendation: Maintain strict risk management and monitor institutional strength."
        
    return jsonify({"response": resp})

@app.route('/api/close_all')
def api_close_all():
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    if not mt5.initialize(): return jsonify({"error": "MT5 offline"}), 500
    
    positions = mt5.positions_get()
    closed_count = 0
    if positions:
        for p in positions:
            tick = mt5.symbol_info_tick(p.symbol)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": p.ticket,
                "price": tick.bid if p.type == 0 else tick.ask,
                "magic": 123456,
                "comment": "Neural Force Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            res = mt5.order_send(request)
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
    
    return jsonify({"success": True, "message": f"Successfully closed {closed_count} positions."})

@app.route('/api/trigger_demo/<symbol>')
def trigger_demo(symbol):
    if not session.get('logged_in'): return jsonify({"error": "unauthorized"}), 401
    
    from src.engines.synergy_engine import SynergyEngine
    from src.executor import TradeExecutor
    from src.mt5_connection import MT5Client
    
    exact_sym = MT5Client.resolve_symbol(symbol)
    if not mt5.initialize(): return jsonify({"error": "MT5 offline"}), 500
    
    # 1. Get Market Data
    df = MT5Client.get_market_data(exact_sym, Config.TIMEFRAME)
    if df.empty: return jsonify({"error": "No market data"}), 400
    
    # 2. Run Synergy Engine
    synergy = SynergyEngine()
    analysis = synergy.analyze(exact_sym, df)
    
    # 3. Forced Test Execution with Broker-Safe Stops
    tick = mt5.symbol_info_tick(exact_sym)
    if not tick: return jsonify({"error": "Price feed error"}), 500
    
    symbol_info = mt5.symbol_info(exact_sym)
    if not symbol_info: return jsonify({"error": "Symbol info unavailable"}), 500
    
    point = symbol_info.point
    # Use 1000 points for SL and 2000 points for TP to ensure we bypass 'Stop Levels'
    sl_dist = 1000 * point
    tp_dist = 2000 * point
    
    price = tick.ask if analysis['direction'] == 'BUY' else tick.bid
    sl = price - sl_dist if analysis['direction'] == 'BUY' else price + sl_dist
    tp = price + tp_dist if analysis['direction'] == 'BUY' else price - tp_dist
    
    success, msg = TradeExecutor.open_position(
        exact_sym, 
        analysis['direction'], 
        0.01, 
        sl, 
        tp, 
        reason=f"Finter Neural Demo Trigger ({analysis['alpha']}% Alpha)",
        criteria="Manual Neural Override"
    )
    
    if success:
        return jsonify({"success": True, "message": msg})
    else:
        return jsonify({"success": False, "error": msg})

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

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    risk_pct = request.form.get('risk_pct')
    trading_enabled = request.form.get('trading_enabled')
    min_alpha = request.form.get('min_alpha')
    settings = db.get_system_settings()
    
    if risk_pct is not None:
        try: risk_pct = float(risk_pct)
        except: risk_pct = settings['risk_pct']
    else: risk_pct = settings['risk_pct']
    
    if min_alpha is not None:
        try: min_alpha = float(min_alpha)
        except: min_alpha = settings['min_alpha_score']
    else: min_alpha = settings['min_alpha_score']

    if trading_enabled is not None:
        trading_enabled = int(trading_enabled)
    else: trading_enabled = settings['trading_enabled']
    
    db.update_system_settings(risk_pct, trading_enabled, settings['symbols'], min_alpha)
    return redirect(url_for('dashboard'))

@app.route('/add_symbol', methods=['POST'])
def add_symbol():
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip()]
    new_sym = request.form.get('symbol', '').strip()
    if new_sym and new_sym not in syms:
        syms.append(new_sym)
        db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms), settings['min_alpha_score'])
    return redirect(url_for('dashboard'))

@app.route('/remove_symbol/<symbol>')
def remove_symbol(symbol):
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = db.get_system_settings()
    syms = [s.strip() for s in settings['symbols'].split(',') if s.strip() and s.strip().lower() != symbol.strip().lower()]
    db.update_system_settings(settings['risk_pct'], settings['trading_enabled'], ",".join(syms), settings['min_alpha_score'])
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
