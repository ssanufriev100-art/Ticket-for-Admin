import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# ==========================
# НАСТРОЙКИ
# ==========================

TOKEN = "ваш токен "
OWNER_ID =   # Ваш Telegram ID

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ==========================
# ХРАНЕНИЕ ЗАЯВОК
# ==========================

applications = {}

# ==========================
# СОСТОЯНИЯ
# ==========================

class Form(StatesGroup):
    name = State()
    age = State()
    position = State()
    why = State()
    username = State()

# ==========================
# ГЛАВНОЕ МЕНЮ
# ==========================

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Подать заявку")],
        [KeyboardButton(text="📋 Статус заявки")]
    ],
    resize_keyboard=True
)

# ==========================
# /start
# ==========================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать!\n\nВыберите действие:",
        reply_markup=menu
    )

# ==========================
# ПОДАТЬ ЗАЯВКУ
# ==========================

@dp.message(F.text == "📝 Подать заявку")
async def application(message: Message, state: FSMContext):

    if message.from_user.id in applications:
        await message.answer(
            f"❌ Вы уже подали заявку.\n\nСтатус: <b>{applications[message.from_user.id]['status']}</b>"
        )
        return

    await state.set_state(Form.name)
    await message.answer("👤 Введите ваше имя:")

# ==========================
# ИМЯ
# ==========================

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("🎂 Введите ваш возраст:")

# ==========================
# ВОЗРАСТ
# ==========================

@dp.message(Form.age)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.position)
    await message.answer("💼 Введите должность:")

# ==========================
# ДОЛЖНОСТЬ
# ==========================

@dp.message(Form.position)
async def get_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    await state.set_state(Form.why)
    await message.answer("📝 Почему именно вы?")
    # ==========================
# ПОЧЕМУ ИМЕННО ВЫ
# ==========================

@dp.message(Form.why)
async def get_why(message: Message, state: FSMContext):
    await state.update_data(why=message.text)
    await state.set_state(Form.username)
    await message.answer(
        "Введите ваш Telegram username.\n"
        "Например: @username"
    )

# ==========================
# USERNAME
# ==========================

@dp.message(Form.username)
async def get_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)

    data = await state.get_data()

    applications[message.from_user.id] = {
        "name": data["name"],
        "age": data["age"],
        "position": data["position"],
        "why": data["why"],
        "username": data["username"],
        "status": "🟡 На рассмотрении"
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"accept:{message.from_user.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отказать",
                    callback_data=f"reject:{message.from_user.id}"
                )
            ]
        ]
    )

    await bot.send_message(
        OWNER_ID,
        f"""📩 <b>Новая заявка</b>

👤 Имя: {data['name']}
🎂 Возраст: {data['age']}
💼 Должность: {data['position']}

📝 Почему именно вы:
{data['why']}

📱 Username: {data['username']}
🆔 ID: {message.from_user.id}
""",
        reply_markup=keyboard
    )

    await message.answer(
        "✅ Ваша заявка отправлена!\n\n"
        "Ожидайте решения администрации.",
        reply_markup=menu
    )

    await state.clear()
    # ==========================
# СТАТУС ЗАЯВКИ
# ==========================

@dp.message(F.text == "📋 Статус заявки")
async def status(message: Message):

    app = applications.get(message.from_user.id)

    if not app:
        await message.answer("❌ У вас нет поданной заявки.")
        return

    await message.answer(
        f"""
📋 <b>Ваша заявка</b>

👤 Имя: {app['name']}
🎂 Возраст: {app['age']}
💼 Должность: {app['position']}

📝 Почему именно вы:
{app['why']}

📱 Username:
{app['username']}

━━━━━━━━━━━━━━━

<b>Статус:</b>
{app['status']}
"""
    )

# ==========================
# ОДОБРИТЬ
# ==========================

@dp.callback_query(F.data.startswith("accept:"))
async def accept(callback: CallbackQuery):

    user_id = int(callback.data.split(":")[1])

    if user_id not in applications:
        await callback.answer("Заявка не найдена.")
        return

    applications[user_id]["status"] = "🟢 Одобрена"

    await bot.send_message(
        user_id,
        "🎉 Поздравляем! Ваша заявка была одобрена."
    )

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer("Заявка одобрена.")

# ==========================
# ОТКАЗАТЬ
# ==========================

@dp.callback_query(F.data.startswith("reject:"))
async def reject(callback: CallbackQuery):

    user_id = int(callback.data.split(":")[1])

    if user_id not in applications:
        await callback.answer("Заявка не найдена.")
        return

    applications[user_id]["status"] = "🔴 Отказана"

    await bot.send_message(
        user_id,
        "❌ К сожалению, ваша заявка была отклонена."
    )

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer("Заявка отклонена.")
   # ==========================
# ЗАПУСК БОТА
# ==========================

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
