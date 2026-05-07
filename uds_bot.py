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

def calculate_elo_change(rating_winner, rating_loser, k_factor=32):
    """Вычисляет дельту по классической формуле Эло"""
    # Ожидаемый результат для победителя
    expected_winner = 1 / (1 + 10 ** ((rating_loser - rating_winner) / 400))
    # Изменение рейтинга (округляем)
    change = round(k_factor * (1 - expected_winner))
    # Гарантируем, что за победу дадут хотя бы 1 балл
    return max(change, 1)


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
                    "vs": {},
                    "streak": 0,
                    "active": True

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

        # --- НОВЫЙ БЛОК ЭЛО ---
        elo_change = calculate_elo_change(data[winner]["elo"], data[loser]["elo"])
        data[winner]["elo"] += elo_change
        data[loser]["elo"] -= elo_change
        # ----------------------

        if data[loser]["elo"] < 0:
            data[loser]["elo"] = 0

# --- ОБНОВЛЕНИЕ СТРИКОВ ---
        # Победитель
        w_streak = data[winner].get("streak", 0)
        if w_streak >= 0:
            data[winner]["streak"] = w_streak + 1
        else:
            data[winner]["streak"] = 1  # Прервал серию поражений

        # Проигравший
        l_streak = data[loser].get("streak", 0)
        if l_streak <= 0:
            data[loser]["streak"] = l_streak - 1
        else:
            data[loser]["streak"] = -1  # Прервал серию побед
        # --------------------------

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
                "vs": {},
                "streak": 0,
                "active": True

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

     # --- НОВЫЙ БЛОК ЭЛО ---
    elo_change = calculate_elo_change(data[winner]["elo"], data[loser]["elo"])
    data[winner]["elo"] += elo_change
    data[loser]["elo"] -= elo_change
    # ----------------------
    
    if data[loser]["elo"] < 0:
        data[loser]["elo"] = 0

# --- ОБНОВЛЕНИЕ СТРИКОВ ---
        # Победитель
    w_streak = data[winner].get("streak", 0)
    if w_streak >= 0:
        data[winner]["streak"] = w_streak + 1
    else:
        data[winner]["streak"] = 1  # Прервал серию поражений

    # Проигравший
    l_streak = data[loser].get("streak", 0)
    if l_streak <= 0:
        data[loser]["streak"] = l_streak - 1
    else:
        data[loser]["streak"] = -1  # Прервал серию побед
        # --------------------------

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
        # ПРОПУСКАЕМ, если актив равен False
        if not stats.get("active", True):
            continue

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
        # ПРОПУСКАЕМ, если актив равен False
        if not stats.get("active", True):
            continue

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
        # ПРОПУСКАЕМ, если актив равен False
        if not stats.get("active", True):
            continue

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

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    if chat_id not in ALLOWED_CHATS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Используй: /predict Пилот1 Пилот2")
        return

    p1, p2 = context.args[0], context.args[1]
    data = load_data()

    if p1 not in data or p2 not in data:
        await update.message.reply_text("Один из пилотов не найден в базе")
        return

    # 1. БАЗОВАЯ ВЕРОЯТНОСТЬ (ЭЛО)
    r1, r2 = data[p1].get("elo", 1000), data[p2].get("elo", 1000)
    prob1 = 1 / (1 + 10 ** ((r2 - r1) / 400))

    # 2. КОРРЕКТИРОВКА ПО H2H (Личные встречи)
    h2h_w1 = data[p1].get("vs", {}).get(p2, 0)
    h2h_w2 = data[p2].get("vs", {}).get(p1, 0)
    total_h2h = h2h_w1 + h2h_w2
    
    h2h_bonus = 0
    if total_h2h > 0:
        # Если один доминирует в личках, даем бонус до 10%
        h2h_bonus = ((h2h_w1 / total_h2h) - 0.5) * 0.2

    # 3. КОРРЕКТИРОВКА ПО ФОРМЕ (Стрики)
    s1, s2 = data[p1].get("streak", 0), data[p2].get("streak", 0)
    # За каждую победу в стрике +2%, за поражение -2% (макс бонус 10%)
    streak_bonus = (max(min(s1, 5), -5) * 0.02) - (max(min(s2, 5), -5) * 0.02)

    # ИТОГОВЫЙ ШАНС
    final_prob = max(min(prob1 + h2h_bonus + streak_bonus, 0.98), 0.02)
    
    # ТЕКСТОВОЕ ОБОСНОВАНИЕ
    def get_form_label(s):
        if s >= 5: return "Успех"
        if s >= 3: return "📈 На подъеме"
        if s <= -5: return "Провал"
        if s <= -3: return "📉 На спаде"
        return "Стабилен"

    chance1 = round(final_prob * 100)
    chance2 = 100 - chance1

    report = (
        f"📊 АНАЛИТИКА МАТЧА\n"
        f"🏎 {p1} vs {p2}\n"
        f"──────────────────\n"
        f"Шансы на победу:\n"
        f"● {p1}: {chance1}%\n"
        f"● {p2}: {chance2}%\n\n"
        f"Состояние пилотов:\n"
        f"👤 {p1}: {get_form_label(s1)} (Стрик: {s1})\n"
        f"👤 {p2}: {get_form_label(s2)} (Стрик: {s2})\n\n"
        f"Личные встречи: {h2h_w1}:{h2h_w2}\n"
        f"──────────────────\n"
        f"💡 _Прогноз учитывает рейтинг, историю встреч и текущую форму_"
    )

    await update.message.reply_text(report, parse_mode="Markdown")

async def set_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if chat_id not in ALLOWED_CHATS:
        return

    # Твоя проверка на админа (как в /result)
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("Эта команда только для администрации.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Используй: /setstatus Имя 0 (инактив) или 1 (актив)")
        return

    name = context.args[0]
    # Если ввели 1 — активен, если 0 — инактивен
    is_active = context.args[1] == "1"
    
    data = load_data()
    if name in data:
        data[name]["active"] = is_active
        save_data(data)
        status_text = "АКТИВЕН" if is_active else "ИНАКТИВЕН"
        await update.message.reply_text(f"✅ Статус пилота {name} изменен на {status_text}")
    else:
        await update.message.reply_text("Пилот не найден в базе.")

async def infopilot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id not in ALLOWED_CHATS:
        return

    if not context.args:
        await update.message.reply_text("Используй: /infopilot Имя")
        return

    name = context.args[0]
    data = load_data()

    if name not in data:
        await update.message.reply_text("Пилот не найден")
        return

    p = data[name]
    status = "🟢 Активен" if p.get("active", True) else "🔴 Инактив"
    
    text = (
        f"📋 **ИНФО: {name}**\n"
        f"Статус: {status}\n"
        f"Рейтинг: {p.get('elo', 1000)} ELO\n"
        f"Стрик: {p.get('streak', 0)}\n"
        f"Всего заездов: {p['runs']}\n"
        f"──────────────────\n"
        f"⚔️ **ЛИЧНЫЕ ВСТРЕЧИ:**\n"
    )

    history = p.get("vs", {})
    if not history:
        text += "История пуста."
    else:
        for opp, wins in history.items():
            # Чтобы найти поражения, смотрим победы оппонента над нами
            losses = data.get(opp, {}).get("vs", {}).get(name, 0)
            text += f"vs {opp} — {wins}:{losses}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def inactives_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    inactive_list = [name for name, s in data.items() if not s.get("active", True)]

    if not inactive_list:
        await update.message.reply_text("Неактивных пилотов нет.")
        return

    text = "💤 **СПИСОК ИНАКТИВОВ:**\n\n"
    for i, name in enumerate(inactive_list, 1):
        text += f"{i}. {name}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

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
app.add_handler(
    CommandHandler(
        "predict",
        predict_command
    )
)
app.add_handler(
    CommandHandler(
        "setstatus",
        set_status_command
    )
)
app.add_handler(
    CommandHandler(
        "infopilot",
        infopilot_command
    )
)
app.add_handler(
    CommandHandler(
        "inactives",
        inactives_command
    )
)

print("Bot started...")

app.run_polling()
