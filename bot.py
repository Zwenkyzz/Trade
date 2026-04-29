import discord, json, os, asyncio
from discord.ext import commands, tasks
from discord import ui
from engine.data_collector import DataCollector
from engine.analyser import TJREngine
from dotenv import load_dotenv

# Charge les variables depuis config/.env
basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, 'config/.env'))

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
STATE_FILE = os.path.join(basedir, "data/state.json")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_state():
    if not os.path.exists(STATE_FILE): 
        data = {"running": False, "capital": 500.0, "positions": {}}
        with open(STATE_FILE, "w") as f: json.dump(data, f)
        return data
    with open(STATE_FILE, "r") as f: 
        try: return json.load(f)
        except: return {"running": False, "capital": 500.0, "positions": {}}

def save_state(data):
    with open(STATE_FILE, "w") as f: json.dump(data, f)

@tasks.loop(seconds=20)
async def trading_loop():
    data = get_state()
    if not data.get("running", False): return
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'PEPE/USDT', 'DOGE/USDT', 'ADA/USDT', 'BNB/USDT', 'DOT/USDT']:
        try:
            collector = DataCollector()
            df = collector.get_latest_candles(symbol, timeframe='15m', limit=50)
            engine = TJREngine(df)
            signal = engine.detect_signal()
            price = df.iloc[-1]['close']
            
            if signal == "STRONG_BUY" and symbol not in data['positions']:
                size = (data['capital'] * 0.95) / price
                if data['capital'] >= (price * size):
                    data['positions'][symbol] = {'size': size, 'entry': price, 'side': 'LONG'}
                    data['capital'] -= (price * size)
                    save_state(data)
                    await channel.send(f"💎 **LONG {symbol}** | Prix: {price:.2f}$")

            elif symbol in data['positions']:
                pos = data['positions'][symbol]
                pnl = (price - pos['entry']) * pos['size']
                if abs(pnl) > 5:
                    data['capital'] += (price * pos['size'] + pnl)
                    del data['positions'][symbol]
                    save_state(data)
                    await channel.send(f"✅ **VENTE {symbol}** | PnL: {pnl:.2f}$ | Solde: {data['capital']:.2f}$")
        except Exception as e: print(f"Err {symbol}: {e}")

@bot.command()
async def price(ctx, symbol: str):
    try:
        p = DataCollector().get_price(f"{symbol.upper()}/USDT")
        await ctx.send(f"📈 {symbol.upper()} : {p:.4f} $")
    except: await ctx.send("❌ Actif non trouvé ou erreur API.")

class MainView(ui.View):
    @ui.button(label="🟢 START", style=discord.ButtonStyle.green)
    async def start(self, interaction, button):
        d = get_state(); d["running"] = True; save_state(d)
        await interaction.response.send_message("🚀 Trading Actif")
    @ui.button(label="🔴 STOP", style=discord.ButtonStyle.red)
    async def stop(self, interaction, button):
        d = get_state(); d["running"] = False; save_state(d)
        await interaction.response.send_message("🛑 Trading Arrêté")
    @ui.button(label="📊 STATS", style=discord.ButtonStyle.blurple)
    async def stats(self, interaction, button):
        await interaction.response.defer(ephemeral=False)
        d = get_state()
        msg = f"💰 **Wallet: {d['capital']:.2f}$** | Actif: {d['running']}"
        pos_list = d.get('positions', {})
        if pos_list:
            msg += "\n🚀 **POSITIONS :**\n" + "\n".join([f"📈 `{s}` : Taille `{p['size']:.4f}`" for s, p in pos_list.items()])
        else: msg += "\n💤 Aucune position."
        await interaction.followup.send(msg)

@bot.command()
async def trade(ctx):
    await ctx.send("🤖 **NEBULA CONTROL**", view=MainView())

@bot.event
async def on_ready():
    print(f"✅ Bot prêt : {bot.user}")
    trading_loop.start()

bot.run(TOKEN)
