import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")

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

def get_win_probability(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

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
        f"📊 Stat {pilot}\n\n"
        f"🏆 Wins: {wins}\n"
        f"❌ Defeats: {losses}\n"
        f"📈 Winrate: {winrate}%\n"
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

    text = "🏆 Top 10 pilots by ELO\n\n"

    place = 1

    for name, elo in top_10:
        text += f"{place}. {name} — {elo}\n"
        place += 1

    await ctx.send(text)

@bot.command()
async def h2h(ctx, pilot1: str, pilot2: str):

    data = load_data()

    if pilot1 not in data:
        await ctx.send(f"❌ Pilot {pilot1} not found")
        return

    if pilot2 not in data:
        await ctx.send(f"❌ Pilot {pilot2} not found")
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
        if not p.get("active", True): continue # ПРОПУСКАЕМ СКРЫТЫХ
        elo = p.get("elo", 1000)
        tier = get_tier(elo)

        if tier in mega_tiers:
            pilots.append((name, elo, tier))

    pilots.sort(key=lambda x: x[1], reverse=True)

    text = "MEGA DIVISION\n\n"

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
        if not p.get("active", True): continue # ПРОПУСКАЕМ СКРЫТЫХ
        elo = p.get("elo", 1000)
        tier = get_tier(elo)

        if tier in pro_tiers:
            pilots.append((name, elo, tier))

    pilots.sort(key=lambda x: x[1], reverse=True)

    text = "PRO DIVISION\n\n"

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
        if not p.get("active", True): continue # ПРОПУСКАЕМ СКРЫТЫХ
        elo = p.get("elo", 1000)
        tier = get_tier(elo)

        if tier in regular_tiers:
            pilots.append((name, elo, tier))

    pilots.sort(key=lambda x: x[1], reverse=True)

    text = "REGULAR DIVISION\n\n"

    for name, elo, tier in pilots:
        text += f"{name} — {elo} ({tier})\n"

    await ctx.send(text)

@bot.command()
async def infopilot(ctx, name: str):
    data = load_data()
    if name not in data:
        await ctx.send(f"❌ Pilot **{name}** not found.")
        return

    p = data[name]
    elo = p.get("elo", 1000)
    streak = p.get("streak", 0)
    status = "🟢 Active" if p.get("active", True) else "🔴 Inactive"
    
    # Создаем красивое окно (Embed)
    embed = discord.Embed(title=f"Профиль пилота: {name}", color=discord.Color.blue())
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Rating", value=f"{elo} ELO ({get_tier(elo)})", inline=True)
    embed.add_field(name="Streak", value=f"{'🔥 ' if streak >= 3 else ''}{streak}", inline=True)
    embed.add_field(name="Races", value=p.get("runs", 0), inline=True)
    embed.add_field(name="Wins", value=p.get("wins", 0), inline=True)

    # Личные встречи
    h2h_text = ""
    vs_data = p.get("vs", {})
    if vs_data:
        for opp, wins in vs_data.items():
            losses = data.get(opp, {}).get("vs", {}).get(name, 0)
            h2h_text += f"⚔️ vs **{opp}** — {wins}:{losses}\n"
    else:
        h2h_text = "The history of duels is empty"
    
    embed.add_field(name="Личные встречи", value=h2h_text, inline=False)
    embed.set_footer(text="Данные синхронизированы с TG ботом")
    
    await ctx.send(embed=embed)

@bot.command()
async def predict(ctx, p1: str, p2: str):
    data = load_data()
    if p1 not in data or p2 not in data:
        await ctx.send("❌ One of the pilots has not been found.")
        return

    # Расчет вероятности (копируем логику из ТГ)
    r1, r2 = data[p1].get("elo", 1000), data[p2].get("elo", 1000)
    prob1 = get_win_probability(r1, r2)

    h2h_w1 = data[p1].get("vs", {}).get(p2, 0)
    h2h_w2 = data[p2].get("vs", {}).get(p1, 0)
    total_h2h = h2h_w1 + h2h_w2
    h2h_bonus = ((h2h_w1 / total_h2h) - 0.5) * 0.2 if total_h2h > 0 else 0

    s1, s2 = data[p1].get("streak", 0), data[p2].get("streak", 0)
    streak_bonus = (max(min(s1, 5), -5) * 0.02) - (max(min(s2, 5), -5) * 0.02)

    final_prob = max(min(prob1 + h2h_bonus + streak_bonus, 0.98), 0.02)
    chance1, chance2 = round(final_prob * 100), 100 - round(final_prob * 100)

    # Визуализация в Дискорде
    embed = discord.Embed(title="🔮 Прогноз на заезд", color=discord.Color.gold())
    embed.add_field(name=f"🏎 {p1}", value=f"**{chance1}%**\n(ELO: {r1})", inline=True)
    embed.add_field(name="VS", value="⚡", inline=True)
    embed.add_field(name=f"🏎 {p2}", value=f"**{chance2}%**\n(ELO: {r2})", inline=True)
    
    # Добавляем инфо по форме
    embed.add_field(name="Форма", value=f"{p1}: {s1} | {p2}: {s2}", inline=False)
    embed.add_field(name="H2H", value=f"Счёт встреч: {h2h_w1}:{h2h_w2}", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def inactives(ctx):
    data = load_data()
    # Собираем список тех, у кого active равно False
    inactive_list = [name for name, p in data.items() if not p.get("active", True)]

    if not inactive_list:
        await ctx.send("There are no inactive ones.")
        return

    embed = discord.Embed(
        title="List of inactive pilots", 
        description="These players are hidden from general divisions.",
        color=discord.Color.light_grey()
    )

    # Формируем список строкой
    list_text = ""
    for i, name in enumerate(inactive_list, 1):
        elo = data[name].get("elo", 1000)
        list_text += f"{i}. **{name}** — {elo} ELO\n"

    embed.add_field(name="Pilots:", value=list_text, inline=False)
    embed.set_footer(text="Управление статусом доступно через TG бота")

    await ctx.send(embed=embed)

bot.run(TOKEN)
