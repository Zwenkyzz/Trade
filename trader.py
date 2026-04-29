import time, os, json, requests
from engine.data_collector import DataCollector
from engine.analyser import TJREngine

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/state.json")

def get_state():
    with open(STATE_FILE, "r") as f: return json.load(f)

def save_state(data):
    with open(STATE_FILE, "w") as f: json.dump(data, f)

def notify(msg):
    try: requests.post("http://127.0.0.1:8000/notify", json={"message": msg})
    except: pass

def run():
    print("🟢 Trader autonome lancé")
    while True:
        try:
            data = get_state()
            if not data.get("running", False):
                time.sleep(5); continue
            
            for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'PEPE/USDT', 'DOGE/USDT', 'ADA/USDT', 'BNB/USDT', 'DOT/USDT']:
                df = DataCollector().get_latest_candles(symbol, timeframe='15m', limit=50)
                engine = TJREngine(df)
                signal = engine.detect_signal()
                price = df.iloc[-1]['close']
                
                # Logic achat
                if signal == "STRONG_BUY" and symbol not in data['positions']:
                    size = (data['capital'] * 0.95) / price
                    if data['capital'] >= (price * size):
                        data['positions'][symbol] = {'size': size, 'entry': price, 'side': 'LONG'}
                        data['capital'] -= (price * size)
                        save_state(data)
                        notify(f"💎 **LONG {symbol}** | Prix: {price:.2f}$")
                
                # Logic vente
                elif symbol in data['positions']:
                    pos = data['positions'][symbol]
                    pnl = (price - pos['entry']) * pos['size']
                    if abs(pnl) > 5:
                        data['capital'] += (price * pos['size'] + pnl)
                        del data['positions'][symbol]
                        save_state(data)
                        notify(f"✅ **VENTE {symbol}** | PnL: {pnl:.2f}$ | Solde: {data['capital']:.2f}$")
        except Exception as e: print(f"Err: {e}")
        time.sleep(10)

if __name__ == "__main__": run()
