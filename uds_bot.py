import json
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)

TOKEN = "8666764220:AAEKM9ZCWHZTXyX91NSjQVKpXAkJx5UhI_k"

# Разрешённые чаты
ALLOWED_CHATS = [
    -1002207748202,
    -1002387577355
]

DATA_FILE = "drivers.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
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


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# 📥 Обработка RESULT сообщений
async def handle_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = None

    if update.channel_post:
        message = update.channel_post
    elif update.message:
        message = update.message
    else:
        return

    chat_id = message.chat.id

    # Проверка разрешённых чатов
    if chat_id not in ALLOWED_CHATS:
        return

    caption = message.caption or message.text

    if not caption:
        return

    if "RESULT:" not in caption:
        return

    try:

        driver1 = re.search(r"Driver1:\s*(.+)", caption).group(1)
        driver2 = re.search(r"Driver2:\s*(.+)", caption).group(1)
        winner = re.search(r"Winner:\s*(.+)", caption).group(1)

        data = load_data()

        for driver in [driver1, driver2]:

            if driver not in data:
                data[driver] = {
                    "wins": 0,
                    "runs": 0,
                    "elo": 1000,
                    "vs": {}
                }

        data[driver1]["runs"] += 1
        data[driver2]["runs"] += 1

        data[winner]["wins"] += 1
        loser = driver1 if winner == driver2 else driver2
        # создаём записи если их нет

        if winner not in data[loser]["vs"]:
            data[loser]["vs"][winner] = 0

        if loser not in data[winner]["vs"]:
            data[winner]["vs"][loser] = 0

        # увеличиваем счёт

        data[winner]["vs"][loser] += 1

        data[winner]["elo"] += 25
        data[loser]["elo"] -= 15

        if data[loser]["elo"] < 0:
            data[loser]["elo"] = 0

        save_data(data)

        print(f"Saved: {driver1} vs {driver2}")

    except Exception as e:
        print("Error:", e)


# 📊 Команда /stat
async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat.id not in ALLOWED_CHATS:
        return

    if not context.args:
        await update.message.reply_text(
            "Используй: /stat Ник"
        )
        return

    driver = context.args[0]

    data = load_data()

    if driver not in data:
        await update.message.reply_text(
            "Пилот не найден"
        )
        return

    wins = data[driver]["wins"]
    runs = data[driver]["runs"]
    elo = data[driver].get("elo", 1000)
    tier = get_tier(elo)

    winrate = 0

    if runs > 0:
        winrate = round((wins / runs) * 100, 2)

    text = (
        f"{driver}\n\n"
        f"ELO: {elo}\n"
        f"Wins: {wins}\n"
        f"Runs: {runs}\n"
        f"Winrate: {winrate}%"
        f"🏆 Tier: {tier}\n"
    )

    await update.message.reply_text(text)

async def h2h_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat.id

    if chat_id not in ALLOWED_CHATS:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Используй: /h2h Pilot1 Pilot2"
        )
        return

    driver1 = context.args[0]
    driver2 = context.args[1]

    data = load_data()

    if driver1 not in data or driver2 not in data:
        await update.message.reply_text(
            "Один из пилотов не найден"
        )
        return

    wins1 = 0
    wins2 = 0

    if "vs" in data[driver1]:
        wins1 = data[driver1]["vs"].get(driver2, 0)

    if "vs" in data[driver2]:
        wins2 = data[driver2]["vs"].get(driver1, 0)

    if wins1 == 0 and wins2 == 0:
        await update.message.reply_text(
            "Они ещё не встречались"
        )
        return

    text = (
        f"⚔️ Head-to-Head\n\n"
        f"{driver1} vs {driver2}\n\n"
        f"{driver1} wins: {wins1}\n"
        f"{driver2} wins: {wins2}"
    )

    await update.message.reply_text(text)

async def nemesis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat.id

    if chat_id not in ALLOWED_CHATS:
        return

    if len(context.args) < 1:
        await update.message.reply_text(
            "Используй: /nemesis Pilot"
        )
        return

    driver = context.args[0]

    data = load_data()

    if driver not in data:
        await update.message.reply_text(
            "Пилот не найден"
        )
        return

    worst_opponent = None
    max_losses = 0

    for opponent in data:

        if opponent == driver:
            continue

        losses = data[opponent].get("vs", {}).get(driver, 0)

        if losses > max_losses:

            max_losses = losses
            worst_opponent = opponent

    if worst_opponent is None:

        await update.message.reply_text(
            "У пилота пока нет поражений"
        )
        return

    text = (
        f"😈 Nemesis\n\n"
        f"{driver}\n\n"
        f"Most difficult opponent:\n"
        f"{worst_opponent} ({max_losses} losses)"
    )

    await update.message.reply_text(text)

async def favorite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat.id

    if chat_id not in ALLOWED_CHATS:
        return

    if len(context.args) < 1:
        await update.message.reply_text(
            "Используй: /favorite Pilot"
        )
        return

    driver = context.args[0]

    data = load_data()

    if driver not in data:
        await update.message.reply_text(
            "Пилот не найден"
        )
        return

    best_opponent = None
    max_wins = 0

    for opponent, wins in data[driver].get("vs", {}).items():

        if wins > max_wins:

            max_wins = wins
            best_opponent = opponent

    if best_opponent is None:

        await update.message.reply_text(
            "У пилота пока нет побед"
        )
        return

    text = (
        f"😎 Favorite Opponent\n\n"
        f"{driver}\n\n"
        f"Best against:\n"
        f"{best_opponent} ({max_wins} wins)"
    )

    await update.message.reply_text(text)

# 🏁 Команда /result (только админы)

async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if chat_id not in ALLOWED_CHATS:
        return

    # Проверка админа
    member = await context.bot.get_chat_member(
        chat_id,
        user_id
    )

    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text(
            "Только админы могут добавлять результаты"
        )
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Используй: /result Driver1 Driver2 Winner"
        )
        return

    driver1 = context.args[0]
    driver2 = context.args[1]
    winner = context.args[2]

    if winner not in [driver1, driver2]:
        await update.message.reply_text(
            "Winner должен быть одним из пилотов"
        )
        return

    data = load_data()

    for driver in [driver1, driver2]:

        if driver not in data:
            data[driver] = {
                "wins": 0,
                "runs": 0,
                "elo": 1000,
                "vs": {}
            }

    data[driver1]["runs"] += 1
    data[driver2]["runs"] += 1

    data[winner]["wins"] += 1

    loser = driver1 if winner == driver2 else driver2

    if winner not in data[loser]["vs"]:
        data[loser]["vs"][winner] = 0

    if loser not in data[winner]["vs"]:
        data[winner]["vs"][loser] = 0

    data[winner]["vs"][loser] += 1

    data[winner]["elo"] += 25
    data[loser]["elo"] -= 15

    if data[loser]["elo"] < 0:
        data[loser]["elo"] = 0

    save_data(data)

    await update.message.reply_text(
        f"✔ Saved: {driver1} vs {driver2}\nWinner: {winner}"
    )
# 🏆 ТОП по ELO

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat.id

    if chat_id not in ALLOWED_CHATS:
        return

    data = load_data()

    if not data:
        await update.message.reply_text("База пуста")
        return

    # Сортировка по ELO
    sorted_drivers = sorted(
        data.items(),
        key=lambda x: x[1].get("elo", 1000),
        reverse=True
    )

    message = "🏆 TOP ELO\n\n"

    top_count = 30  # можно менять

    for i, (driver, stats) in enumerate(sorted_drivers[:top_count]):

        elo = stats.get("elo", 1000)

        tier = get_tier(elo)

        message += f"{i+1}. {driver} — {elo}({tier})\n"

    await update.message.reply_text(message)
async def megadiv_command(update, context):

    data = load_data()

    mega_list = []

    for name, stats in data.items():

        elo = stats["elo"]
        tier = get_tier(elo)

        if tier in ["MAX", "APEX", "PROFESSIONAL"]:

            mega_list.append((name, elo, tier))

    mega_list.sort(key=lambda x: x[1], reverse=True)

    if not mega_list:
        await update.message.reply_text("Нет пилотов в MEGA Division")
        return

    text = "🏆 MEGA Division\n\n"

    for i, (name, elo, tier) in enumerate(mega_list, start=1):

        text += f"{i}. {name} — {elo} ({tier})\n"

    await update.message.reply_text(text)
async def prodiv_command(update, context):

    data = load_data()

    pro_list = []

    for name, stats in data.items():

        elo = stats["elo"]
        tier = get_tier(elo)

        if tier in ["TIER 1", "TIER 2", "TIER 3", "TIER 4"]:

            pro_list.append((name, elo, tier))

    pro_list.sort(key=lambda x: x[1], reverse=True)

    if not pro_list:
        await update.message.reply_text("Нет пилотов в PRO Division")
        return

    text = "🥇 PRO Division\n\n"

    for i, (name, elo, tier) in enumerate(pro_list, start=1):

        text += f"{i}. {name} — {elo} ({tier})\n"

    await update.message.reply_text(text)
async def standarddiv_command(update, context):

    data = load_data()

    standard_list = []

    for name, stats in data.items():

        elo = stats["elo"]
        tier = get_tier(elo)

        if tier in ["TIER 5", "TIER 6", "TIER 7"]:

            standard_list.append((name, elo, tier))

    standard_list.sort(key=lambda x: x[1], reverse=True)

    if not standard_list:
        await update.message.reply_text("Нет пилотов в STANDARD Division")
        return

    text = "🥈 STANDARD Division\n\n"

    for i, (name, elo, tier) in enumerate(standard_list, start=1):

        text += f"{i}. {name} — {elo} ({tier})\n"

    await update.message.reply_text(text)

app = ApplicationBuilder().token(TOKEN).build()

# RESULT обработчик
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_post
    )
)

# Команда /stat
app.add_handler(
    CommandHandler(
        "stat",
        stat_command
    )
)
app.add_handler(
    CommandHandler(
        "h2h",
        h2h_command
    )
)
app.add_handler(
    CommandHandler(
        "nemesis",
        nemesis_command
    )
)
app.add_handler(
    CommandHandler(
        "favorite",
        favorite_command
    )
)
app.add_handler(
    CommandHandler(
        "result",
        result_command
    )
)
app.add_handler(
    CommandHandler(
        "top",
        top_command
    )
)
app.add_handler(
    CommandHandler(
        "megadiv",
        megadiv_command
    )
)
app.add_handler(
    CommandHandler(
        "prodiv",
        prodiv_command
    )
)
app.add_handler(
    CommandHandler(
        "standarddiv",
        standarddiv_command
    )
)

print("Bot started...")

app.run_polling()
