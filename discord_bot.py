import discord
from discord.ext import commands
import json
import os

TOKEN = os.getev("DISCORD_TOKEN")

DRIVERS_FILE = "drivers.json"

# intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# загрузка базы
def load_data():
    try:
        with open(DRIVERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def get_tier(elo):

    if elo >= 1400:
        return "MAX"
    elif elo >= 1350:
        return "APEX"
    elif elo >= 1300:
        return "CHAMPION"
    elif elo >= 1200:
        return "PROFESSIONAL"
    elif elo >= 1150:
        return "TIER 1"
    elif elo >= 1100:
        return "TIER 2"
    elif elo >= 1050:
        return "TIER 3"
    elif elo >= 1000:
        return "TIER 4"
    elif elo >= 950:
        return "TIER 5"
    elif elo >= 900:
        return "TIER 6"
    else:
        return "TIER 7"

# старт
@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")


# команда !stat
@bot.command()
async def stat(ctx, pilot: str):

    data = load_data()

    if pilot not in data:
        await ctx.send("❌ Пилот не найден")
        return

    p = data[pilot]

    wins = p.get("wins", 0)
    runs = p.get("runs", 0)

    losses = runs - wins
    if losses < 0:
        losses = 0

    elo = p.get("elo", 1000)

    total = wins + losses

    if total > 0:
        winrate = round((wins / total) * 100, 1)
    else:
        winrate = 0

    text = (
        f"📊 Статистика {pilot}\n\n"
        f"🏆 Победы: {wins}\n"
        f"❌ Поражения: {losses}\n"
        f"📈 Винрейт: {winrate}%\n"
        f"⭐ ELO: {elo}"
    )

    await ctx.send(text)

@bot.command()
async def top(ctx):

    data = load_data()

    # создаём список пилотов
    pilots = []

    for name, p in data.items():
        elo = p.get("elo", 1000)
        pilots.append((name, elo))

    # сортировка по ELO
    pilots.sort(key=lambda x: x[1], reverse=True)

    # берём топ 10
    top_10 = pilots[:10]

    text = "🏆 ТОП 10 пилотов по ELO\n\n"

    place = 1

    for name, elo in top_10:
        text += f"{place}. {name} — {elo}\n"
        place += 1

    await ctx.send(text)

@bot.command()
async def h2h(ctx, pilot1: str, pilot2: str):

    data = load_data()

    if pilot1 not in data:
        await ctx.send(f"❌ Пилот {pilot1} не найден")
        return

    if pilot2 not in data:
        await ctx.send(f"❌ Пилот {pilot2} не найден")
        return

    h2h_data = data[pilot1].get("h2h", {})

    wins1 = h2h_data.get(pilot2, 0)

    h2h_data_2 = data[pilot2].get("h2h", {})

    wins2 = h2h_data_2.get(pilot1, 0)

    text = (
        "Личный счёт\n\n"
        f"{pilot1} 🆚 {pilot2}\n\n"
        f"🏆 {pilot1}: {wins1}\n"
        f"🏆 {pilot2}: {wins2}"
    )

    await ctx.send(text)

@bot.command()
async def megadiv(ctx):

    data = load_data()

    mega_tiers = ["MAX", "APEX", "PROFESSIONAL"]

    pilots = []

    for name, p in data.items():
        elo = p.get("elo", 1000)
        tier = get_tier(elo)

        if tier in mega_tiers:
            pilots.append((name, elo, tier))

    pilots.sort(key=lambda x: x[1], reverse=True)

    text = "🔥 MEGA DIVISION\n\n"

    for name, elo, tier in pilots:
        text += f"{name} — {elo} ({tier})\n"

    await ctx.send(text)

@bot.command()
async def prodiv(ctx):

    data = load_data()

    pro_tiers = [
        "TIER 1",
        "TIER 2",
        "TIER 3",
        "TIER 4"
    ]

    pilots = []

    for name, p in data.items():
        elo = p.get("elo", 1000)
        tier = get_tier(elo)

        if tier in pro_tiers:
            pilots.append((name, elo, tier))

    pilots.sort(key=lambda x: x[1], reverse=True)

    text = "⚡ PRO DIVISION\n\n"

    for name, elo, tier in pilots:
        text += f"{name} — {elo} ({tier})\n"

    await ctx.send(text)

@bot.command()
async def regulardiv(ctx):

    data = load_data()

    regular_tiers = [
        "TIER 5",
        "TIER 6",
        "TIER 7"
    ]

    pilots = []

    for name, p in data.items():
        elo = p.get("elo", 1000)
        tier = get_tier(elo)

        if tier in regular_tiers:
            pilots.append((name, elo, tier))

    pilots.sort(key=lambda x: x[1], reverse=True)

    text = "🏁 REGULAR DIVISION\n\n"

    for name, elo, tier in pilots:
        text += f"{name} — {elo} ({tier})\n"

    await ctx.send(text)

bot.run(TOKEN)
