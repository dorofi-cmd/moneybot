import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import os

TOKEN = os.getenv("BOT_TOKEN")  # 🔐 токен будет храниться в Render ENV vars

bot = Bot(token=TOKEN)
dp = Dispatcher()

# === Кнопки ===
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Заработано"), KeyboardButton(text="💸 Потрачено")],
        [KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True
)

# === Создание таблицы ===
async def init_db():
    async with aiosqlite.connect("money.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            date TEXT
        )""")
        await db.commit()

# === Обработчики ===
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я твой финансовый помощник 💼", reply_markup=main_kb)

@dp.message(lambda msg: msg.text in ["💰 Заработано", "💸 Потрачено"])
async def choose_type(message: types.Message):
    t = "income" if message.text == "💰 Заработано" else "expense"
    await message.answer(f"Введите сумму ({'доход' if t=='income' else 'расход'}):")
    dp["last_type"] = t  # сохраняем тип временно

@dp.message(lambda msg: msg.text.replace('.', '', 1).isdigit())
async def add_record(message: types.Message):
    if "last_type" not in dp:
        return await message.answer("Сначала выберите 💰 Заработано или 💸 Потрачено.")
    amount = float(message.text)
    t = dp["last_type"]
    date = datetime.now().strftime("%Y-%m-%d")

    async with aiosqlite.connect("money.db") as db:
        await db.execute("INSERT INTO records (type, amount, date) VALUES (?, ?, ?)", (t, amount, date))
        await db.commit()

    if t == "income":
        await message.answer(f"✅ Добавлено: заработал {amount} zł")
    else:
        await message.answer(f"💸 Добавлено: потратил {amount} zł")

    dp.pop("last_type")

@dp.message(lambda msg: msg.text == "📊 Статистика")
async def stats(message: types.Message):
    async with aiosqlite.connect("money.db") as db:
        async with db.execute("SELECT type, SUM(amount) FROM records GROUP BY type") as cursor:
            data = await cursor.fetchall()

    income = next((d[1] for d in data if d[0] == "income"), 0)
    expense = next((d[1] for d in data if d[0] == "expense"), 0)
    balance = (income or 0) - (expense or 0)

    text = (f"📊 Статистика:\n\n"
            f"💰 Заработано: {income:.2f} zł\n"
            f"💸 Потрачено: {expense:.2f} zł\n"
            f"💵 Баланс: {balance:.2f} zł")
    await message.answer(text)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
