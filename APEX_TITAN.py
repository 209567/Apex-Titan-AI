import customtkinter as ctk
import yfinance as yf
import pandas as pd
import threading
import time
import matplotlib
import requests
import feedparser
import webbrowser
import json
import os
import sys

# CRITICAL: Backend for charts to prevent UI freeze
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
import ollama

# --- CONFIGURATION ---
APP_NAME = "APEX TITAN"
VERSION = "2.0 (Stable)"
COLOR_BG = "#202020"
COLOR_SURFACE = "#2C2C2C"
COLOR_ACCENT = "#60CDFF"
COLOR_GREEN = "#00CC6A"
COLOR_RED = "#FF453A"
COLOR_TEXT_MAIN = "#FFFFFF"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- DATA & ASSETS ---
ASSET_LIBRARY = {
    "Crypto": [("Bitcoin", "BTC-USD"), ("Ethereum", "ETH-USD"), ("Solana", "SOL-USD"), ("Dogecoin", "DOGE-USD")],
    "Stocks (US)": [("Apple", "AAPL"), ("Tesla", "TSLA"), ("Nvidia", "NVDA"), ("Microsoft", "MSFT")],
    "Stocks (Ind)": [("Reliance", "RELIANCE.NS"), ("Tata Motors", "TATAMOTORS.NS"), ("HDFC Bank", "HDFCBANK.NS")],
    "Forex": [("Gold", "GC=F"), ("Silver", "SI=F"), ("USD/INR", "INR=X"), ("EUR/USD", "EURUSD=X")]
}

# --- ENGINE ---
class DataEngine:
    def __init__(self):
        self.screener_list = ["BTC-USD", "AAPL", "RELIANCE.NS"]
        self.ai_available = self.check_ollama()

    def check_ollama(self):
        try:
            ollama.list()
            return True
        except:
            return False

    def fetch_data(self, ticker):
        try:
            # 1. Get History
            stock = yf.Ticker(ticker)
            # Fetch with minimal period to save data, auto_adjust for accuracy
            hist = stock.history(period="6mo", auto_adjust=True)
            
            if hist.empty: 
                return None

            # 2. Get Info (Handle missing data gracefully)
            try:
                info = stock.info
                name = info.get('shortName', info.get('longName', ticker))
            except:
                name = ticker

            current = hist['Close'].iloc[-1]
            
            # 3. Calculate Indicators
            # RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Trend (SMA 50)
            sma = hist['Close'].rolling(50).mean().iloc[-1]
            trend = "UPTREND" if current > sma else "DOWNTREND"
            
            # Score logic
            score = 50
            if rsi < 30: score += 20
            elif rsi > 70: score -= 20
            if current > sma: score += 15
            
            decision = "NEUTRAL"
            if score >= 65: decision = "BUY ZONE"
            if score <= 40: decision = "SELL ZONE"
            
            return {
                "symbol": ticker,
                "name": name,
                "price": round(current, 2),
                "rsi": round(rsi, 2),
                "trend": trend,
                "score": int(score),
                "decision": decision,
                "history": hist
            }
        except Exception as e:
            print(f"DEBUG: Data fetch error for {ticker}: {e}")
            return None

    def get_ai_analysis(self, data):
        """Generator for streaming AI response"""
        if not self.ai_available:
            yield "⚠️ AI ERROR: Ollama is not running or 'phi3.5' is not installed.\nPlease install Ollama and run 'ollama run phi3.5' in terminal."
            return

        try:
            prompt = (f"Analyze {data['name']} ({data['symbol']}). "
                      f"Price: {data['price']}, RSI: {data['rsi']}, Trend: {data['trend']}. "
                      f"Give a strict financial verdict in under 50 words.")
            
            stream = ollama.chat(
                model='phi3.5',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            for chunk in stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"⚠️ AI Connection Interrupted: {e}"

    def get_news(self, query):
        items = []
        try:
            term = query.replace(".NS", " India").replace("-USD", " Crypto")
            url = f"https://news.google.com/rss/search?q={term}+finance&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                items.append({"title": entry.title, "link": entry.link})
        except Exception as e:
            items.append({"title": f"⚠️ Connection Error: Could not fetch news.", "link": ""})
        return items

# --- GUI ---
class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("400x450")
        self.title("Login")
        self.configure(fg_color=COLOR_BG)
        self.parent = parent
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.parent.destroy)

        ctk.CTkLabel(self, text="🦅", font=("Arial", 60)).pack(pady=(40,10))
        ctk.CTkLabel(self, text="APEX TITAN", font=("Segoe UI", 24, "bold"), text_color=COLOR_ACCENT).pack()
        
        self.key_entry = ctk.CTkEntry(self, placeholder_text="License Key", width=220, justify="center")
        self.key_entry.pack(pady=(40, 10))
        
        ctk.CTkButton(self, text="UNLOCK SYSTEM", width=220, fg_color=COLOR_ACCENT, text_color="black", 
                      command=self.validate).pack(pady=10)
        
        self.status = ctk.CTkLabel(self, text="Enter Key: TITAN-KEY-2025", text_color="gray")
        self.status.pack(pady=20)

    def validate(self):
        if self.key_entry.get().strip() == "TITAN-KEY-2025":
            self.destroy()
            self.parent.deiconify()
        else:
            self.status.configure(text="❌ Invalid Key", text_color=COLOR_RED)

class ApexApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1280x800")
        self.configure(fg_color=COLOR_BG)
        
        self.engine = DataEngine()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_sidebar()
        self.setup_pages()
        
        self.after(100, lambda: LoginWindow(self))

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLOR_SURFACE)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text=APP_NAME, font=("Segoe UI", 22, "bold"), text_color=COLOR_ACCENT).pack(pady=40)
        
        self.nav_buttons = {}
        pages = [("Dashboard", "dash"), ("Asset Library", "lib"), ("Risk Calc", "risk"), ("News Feed", "news")]
        
        for name, key in pages:
            btn = ctk.CTkButton(self.sidebar, text=name, fg_color="transparent", text_color="white", 
                                anchor="w", height=50, command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

    def setup_pages(self):
        self.page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.page_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.frames = {}
        self.frames["dash"] = self.create_dashboard()
        self.frames["lib"] = self.create_library()
        self.frames["risk"] = self.create_risk()
        self.frames["news"] = self.create_news()
        
        self.show_page("dash")

    def show_page(self, key):
        for k, f in self.frames.items(): f.pack_forget()
        self.frames[key].pack(fill="both", expand=True)
        for k, b in self.nav_buttons.items(): b.configure(fg_color="transparent")
        self.nav_buttons[key].configure(fg_color="#3A3A3A")

    # --- DASHBOARD ---
    def create_dashboard(self):
        frame = ctk.CTkFrame(self.page_container, fg_color="transparent")
        
        head = ctk.CTkFrame(frame, fg_color="transparent")
        head.pack(fill="x", pady=(0,20))
        self.dash_search = ctk.CTkEntry(head, placeholder_text="Ticker (e.g. AAPL)", width=300)
        self.dash_search.pack(side="left", padx=(0,10))
        # Enter key also triggers search
        self.dash_search.bind("<Return>", lambda e: self.run_analysis())
        ctk.CTkButton(head, text="ANALYZE", command=self.run_analysis, width=100, fg_color=COLOR_ACCENT, text_color="black").pack(side="left")

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        self.chart_frame = ctk.CTkFrame(content, fg_color=COLOR_SURFACE)
        self.chart_frame.pack(side="left", fill="both", expand=True, padx=(0,10))
        self.chart_ph = ctk.CTkLabel(self.chart_frame, text="CHART DISPLAY", text_color="gray")
        self.chart_ph.place(relx=0.5, rely=0.5, anchor="center")
        
        panel = ctk.CTkFrame(content, width=300, fg_color=COLOR_SURFACE)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)
        
        ctk.CTkLabel(panel, text="METRICS", text_color="gray", font=("Arial", 12)).pack(pady=10)
        self.lbl_price = self.make_metric(panel, "$0.00", COLOR_GREEN)
        self.lbl_score = self.make_metric(panel, "Score: --", "white")
        self.lbl_trend = self.make_metric(panel, "Trend: --", "gray")
        
        ctk.CTkLabel(panel, text="AI ANALYSIS", text_color="gray", font=("Arial", 12)).pack(pady=(20,10))
        self.txt_ai = ctk.CTkTextbox(panel, fg_color="#222", text_color="#ddd")
        self.txt_ai.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        return frame

    def make_metric(self, parent, text, color):
        lbl = ctk.CTkLabel(parent, text=text, font=("Segoe UI", 20, "bold"), text_color=color)
        lbl.pack(pady=5)
        return lbl

    def run_analysis(self, ticker=None):
        t = ticker if ticker else self.dash_search.get()
        if not t: return
        
        self.lbl_price.configure(text="Loading...")
        self.txt_ai.delete("0.0", "end")
        if not self.engine.ai_available:
            self.txt_ai.insert("0.0", "⚠️ OLLAMA NOT DETECTED.\nAI features disabled.")
        
        threading.Thread(target=self._process_data, args=(t,)).start()

    def _process_data(self, ticker):
        data = self.engine.fetch_data(ticker)
        if not data:
            self.after(0, lambda: self.lbl_price.configure(text="NOT FOUND"))
            return
            
        self.after(0, lambda: self._update_ui(data))

    def _update_ui(self, data):
        self.lbl_price.configure(text=f"${data['price']}")
        self.lbl_score.configure(text=f"Score: {data['score']}/100")
        self.lbl_trend.configure(text=data['trend'])
        
        # CLEANUP: Crucial to prevent memory leak
        for w in self.chart_frame.winfo_children(): w.destroy()
        plt.close('all') 
        
        # Plotting
        fig, ax = mpf.plot(data['history'], type='candle', volume=False, style='nightclouds', returnfig=True, figsize=(5,4))
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        threading.Thread(target=self._stream_ai, args=(data,)).start()

    def _stream_ai(self, data):
        for chunk in self.engine.get_ai_analysis(data):
            self.txt_ai.insert("end", chunk)
            self.txt_ai.see("end")

    # --- ASSET LIBRARY ---
    def create_library(self):
        frame = ctk.CTkFrame(self.page_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="📚 Quick Asset Library", font=("Segoe UI", 20)).pack(anchor="w", pady=10)
        
        tabs = ctk.CTkTabview(frame)
        tabs.pack(fill="both", expand=True)
        
        for cat, items in ASSET_LIBRARY.items():
            t = tabs.add(cat)
            for name, ticker in items:
                row = ctk.CTkFrame(t, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"{name} ({ticker})", anchor="w").pack(side="left", padx=10)
                ctk.CTkButton(row, text="Load", width=60, height=25, 
                              command=lambda x=ticker: self.load_from_lib(x)).pack(side="right")
        return frame

    def load_from_lib(self, ticker):
        self.show_page("dash")
        self.dash_search.delete(0, "end")
        self.dash_search.insert(0, ticker)
        self.run_analysis(ticker)

    # --- RISK CALCULATOR ---
    def create_risk(self):
        frame = ctk.CTkFrame(self.page_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="🛡️ Risk Calculator", font=("Segoe UI", 20)).pack(anchor="w", pady=10)
        
        p = ctk.CTkFrame(frame, fg_color=COLOR_SURFACE)
        p.pack(fill="x", pady=10)
        
        self.r_bal = self.add_input(p, "Balance ($):")
        self.r_risk = self.add_input(p, "Risk %:")
        self.r_entry = self.add_input(p, "Entry Price:")
        self.r_stop = self.add_input(p, "Stop Loss:")
        
        ctk.CTkButton(frame, text="CALCULATE", fg_color=COLOR_ACCENT, text_color="black", command=self.calc_risk).pack(pady=10)
        
        self.r_result = ctk.CTkLabel(frame, text="", font=("Consolas", 14), justify="left")
        self.r_result.pack(pady=10)
        return frame

    def add_input(self, parent, text):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", expand=True, padx=5, pady=10)
        ctk.CTkLabel(f, text=text).pack()
        e = ctk.CTkEntry(f, width=80)
        e.pack()
        return e

    def calc_risk(self):
        try:
            bal = float(self.r_bal.get())
            risk = float(self.r_risk.get())
            entry = float(self.r_entry.get())
            stop = float(self.r_stop.get())
            
            risk_amt = bal * (risk/100)
            diff = abs(entry - stop)
            if diff == 0: raise ValueError
            qty = risk_amt / diff
            
            self.r_result.configure(text=f"RISK AMOUNT: ${risk_amt:.2f}\nPOSITION SIZE: {int(qty)} units\nTOTAL CAPITAL: ${qty*entry:.2f}")
        except:
            self.r_result.configure(text="Invalid Input")

    # --- NEWS ---
    def create_news(self):
        frame = ctk.CTkFrame(self.page_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="📰 Latest Financial News", font=("Segoe UI", 20)).pack(anchor="w", pady=10)
        
        ctrl = ctk.CTkFrame(frame, fg_color="transparent")
        ctrl.pack(fill="x")
        self.news_q = ctk.CTkEntry(ctrl, placeholder_text="Topic (e.g. Bitcoin)", width=300)
        self.news_q.pack(side="left", padx=10)
        # Enter key triggers news fetch
        self.news_q.bind("<Return>", lambda e: self.fetch_news())
        ctk.CTkButton(ctrl, text="Fetch", width=80, command=self.fetch_news).pack(side="left")
        
        self.news_box = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.news_box.pack(fill="both", expand=True, pady=10)
        return frame

    def fetch_news(self):
        q = self.news_q.get()
        if not q: return
        for w in self.news_box.winfo_children(): w.destroy()
        
        threading.Thread(target=self._thread_news, args=(q,)).start()

    def _thread_news(self, q):
        items = self.engine.get_news(q)
        self.after(0, lambda: self._show_news(items))

    def _show_news(self, items):
        if not items:
            ctk.CTkLabel(self.news_box, text="No news found.").pack()
            return
            
        for i in items:
            f = ctk.CTkFrame(self.news_box, fg_color=COLOR_SURFACE)
            f.pack(fill="x", pady=2)
            
            # IMPROVEMENT: Wraplength ensures text stays on screen
            ctk.CTkLabel(f, text=i['title'], anchor="w", wraplength=600, justify="left").pack(side="left", padx=10, pady=5)
            
            if i['link']:
                ctk.CTkButton(f, text="Read", width=50, command=lambda l=i['link']: webbrowser.open(l)).pack(side="right", padx=10)

if __name__ == "__main__":
    app = ApexApp()
    app.mainloop()
