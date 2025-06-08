import asyncio
import json
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils import executor

TOKEN = '7830992096:AAHCS4EjW7lJiruLWDgxGVzzeB_BuhWhX3g'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = 'users.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

users = load_data()

def get_user(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "last_bonus": "2000-01-01T00:00:00",
            "last_case": "2000-01-01T00:00:00"
        }
        save_data(users)
    return users[uid]

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Открыть мини-приложение", web_app=WebAppInfo(url="https://your-domain.com/index.html"))
    )
    await message.answer(
        "Привет! Это кейс-бот с мини-приложением.\n"
        "Нажми кнопку ниже, чтобы открыть интерфейс внутри Telegram.",
        reply_markup=kb
    )

@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def webapp_data_handler(message: types.Message):
    data = message.web_app_data.data  # строка JSON из WebApp
    uid = str(message.from_user.id)
    user = get_user(uid)

    try:
        payload = json.loads(data)
    except Exception:
        await message.answer("Ошибка обработки данных.")
        return

    now = datetime.utcnow()

    if payload.get("action") == "get_bonus":
        last_bonus = datetime.fromisoformat(user["last_bonus"])
        if now - last_bonus >= timedelta(hours=1):
            user["balance"] += 3
            user["last_bonus"] = now.isoformat()
            save_data(users)
            await message.answer(f"Тебе начислено 3$! Баланс: {user['balance']}$")
        else:
            await message.answer("Бонус можно получить только 1 раз в час.")

    elif payload.get("action") == "open_case":
        last_case = datetime.fromisoformat(user["last_case"])
        if now - last_case < timedelta(hours=1):
            await message.answer("Кейс можно открывать раз в час. Подожди немного.")
            return
        prizes = [
            {"name": "0$", "amount": 0, "chance": 50},
            {"name": "1$", "amount": 1, "chance": 30},
            {"name": "5$", "amount": 5, "chance": 15},
            {"name": "50$", "amount": 50, "chance": 5},
        ]
        roll = random.randint(1, 100)
        acc = 0
        prize = None
        for p in prizes:
            acc += p["chance"]
            if roll <= acc:
                prize = p
                break
        user["balance"] += prize["amount"]
        user["last_case"] = now.isoformat()
        save_data(users)
        await message.answer(f"🎉 Ты открыл кейс и выиграл {prize['name']}! Баланс: {user['balance']}$")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
