import discord, json, os
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv

# Charge les variables depuis config/.env
basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, 'config/.env'))

TOKEN = os.getenv("DISCORD_TOKEN")
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

class MainView(ui.View):
    @ui.button(label="🟢 START", style=discord.ButtonStyle.green)
    async def start(self, interaction, button):
        d = get_state(); d["running"] = True; save_state(d)
        await interaction.response.send_message("🚀 Moteur enclenché !")

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

bot.run(TOKEN)
