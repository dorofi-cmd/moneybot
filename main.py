import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "money.db"


async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.commit()


@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="💰 Заработано")
    kb.button(text="💸 Потрачено")
    kb.button(text="📊 Статистика")
    await message.answer("Выбери действие:", reply_markup=kb.as_markup(resize_keyboard=True))


@dp.message(lambda m: m.text in ["💰 Заработано", "💸 Потрачено"])
async def choose_type(message: types.Message):
    record_type = "earned" if "Заработано" in message.text else "spent"
    await message.answer(f"Введи сумму ({'+' if record_type == 'earned' else '-'})")
    dp['record_type'] = record_type


@dp.message(lambda m: m.text.replace('.', '', 1).isdigit())
async def enter_amount(message: types.Message):
    record_type = dp.get('record_type', None)
    if not record_type:
        return await message.answer("Сначала выбери действие в меню.")
    
    amount = float(message.text)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO records (type, amount) VALUES (?, ?)", (record_type, amount))
        await db.commit()
    await message.answer(f"✅ Записано: {amount} zł ({'заработано' if record_type == 'earned' else 'потрачено'})")


@dp.message(lambda m: m.text == "📊 Статистика")
async def show_stats(message: types.Message):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT type, SUM(amount) FROM records GROUP BY type
        """)
        rows = await cursor.fetchall()
    
    earned = next((r[1] for r in rows if r[0] == "earned"), 0)
    spent = next((r[1] for r in rows if r[0] == "spent"), 0)
    balance = (earned or 0) - (spent or 0)

    await message.answer(
        f"📅 Статистика:\n"
        f"💰 Заработано: {earned or 0:.2f} zł\n"
        f"💸 Потрачено: {spent or 0:.2f} zł\n"
        f"📈 Баланс: {balance:.2f} zł"
    )


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
