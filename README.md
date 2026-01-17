# 🦅 "A Privacy-First Financial Analysis Terminal. (Not related to the video game Apex Legends)."

<!-- UPLOAD A SCREENSHOT OF THE DASHBOARD HERE -->
![Apex Titan Dashboard](https://github.com/Zeros-CodeXD/Apex-Titan-AI/blob/main/dashboard.png)

**Apex Titan** is a professional-grade desktop financial terminal built to solve the privacy crisis in trading tools. Unlike web apps that track your data, Apex runs **100% Locally** using quantized Large Language Models (LLMs).

## ⚡ Key Features

### 🔒 1. Local AI Analyst
Integrated with **Ollama (Phi-3.5)**, the system analyzes RSI, MACD, and Trend data in real-time.
- **Zero Data Leakage:** Your financial queries never leave your machine.
- **Instant Verdicts:** Generates "Buy/Sell/Hold" ratings with strict financial reasoning.

### 📊 2. Institutional Interface
Designed with **CustomTkinter** to mimic high-end Bloomberg Terminals.
- Dark Mica Theme.
- Real-time Candlestick Charting (mplfinance).
- Multi-Asset Library (Crypto, Forex, NSE, NASDAQ).

### 🛡️ 3. Risk & Volatility Engine
Built-in calculator that adjusts position sizing based on account balance and stop-loss width.
- Prevents emotional trading.
- Calculates 1:2 and 1:3 Risk-to-Reward targets automatically.

## 🛠️ Tech Stack
- **Core:** Python 3.10+
- **GUI:** CustomTkinter (Modern Tkinter)
- **AI/LLM:** Ollama (running Phi-3.5)
- **Data:** yFinance (Yahoo Finance API)
- **Charting:** Matplotlib & Mplfinance

## 📦 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Zeros-CodeXD/Apex-Titan-AI.git
   cd Apex-Titan-AI
   ```[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2FZeros-CodeXD%2FApex-Titan-AI)]

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2FZeros-CodeXD%2FApex-Titan-AI)]

3. **⚡ IMPORTANT: Setup AI Engine**
   This app uses **Ollama** for local intelligence.[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2FZeros-CodeXD%2FApex-Titan-AI)]
   - Download Ollama from [ollama.com](https://ollama.com)[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2FZeros-CodeXD%2FApex-Titan-AI)]
   - Open your terminal and run:
     ```bash
     ollama run phi3.5
     ```
   *(Without this step, the AI Analyst feature will not work)*[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2FZeros-CodeXD%2FApex-Titan-AI)]

4. **Launch the Terminal**
   ```bash
   python APEX_TITAN.py

## 🔐 Demo License Key:
To test the application, use the developer key: TITAN-KEY-2025
