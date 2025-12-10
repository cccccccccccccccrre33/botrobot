import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопки
button_form = KeyboardButton("Оставить заявку")
keyboard = ReplyKeyboardMarkup(keyboard=[[button_form]], resize_keyboard=True)

# JSON файл для заявок
DATA_FILE = "requests.json"

# Проверка существования файла
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# Старт и помощь
@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    await message.answer(
        "Привет! Чтобы оставить заявку, нажми кнопку 'Оставить заявку'.",
        reply_markup=keyboard
    )

@dp.message(Command(commands=["help"]))
async def help_command(message: types.Message):
    await message.answer("Используй кнопку 'Оставить заявку', чтобы отправить данные.")

# Показ заявок админом
@dp.message(Command(commands=["show"]))
async def show_requests(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа.")
        return
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if not data:
        await message.answer("Заявок пока нет.")
        return
    text = ""
    for i, req in enumerate(data, 1):
        text += f"{i}. Имя: {req['name']}\nТелефон: {req['phone']}\nКомментарий: {req['comment']}\nДата: {req['date']}\n\n"
    await message.answer(text)

# Хендлер для кнопки "Оставить заявку"
user_data = {}

@dp.message(lambda message: message.text == "Оставить заявку")
async def ask_name(message: types.Message):
    await message.answer("Как вас зовут?")
    user_data[message.from_user.id] = {}

@dp.message()
async def process_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return  # Не в процессе заявки

    data = user_data[user_id]

    if "name" not in data:
        data["name"] = message.text
        await message.answer("Укажи номер телефона:")
    elif "phone" not in data:
        data["phone"] = message.text
        await message.answer("Комментарий (необязательно):")
    elif "comment" not in data:
        data["comment"] = message.text
        data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Сохраняем в файл
        with open(DATA_FILE, "r") as f:
            requests_list = json.load(f)
        requests_list.append(data)
        with open(DATA_FILE, "w") as f:
            json.dump(requests_list, f, ensure_ascii=False, indent=4)
        # Уведомляем админа
        await bot.send_message(
            ADMIN_ID,
            f"Новая заявка!\nИмя: {data['name']}\nТелефон: {data['phone']}\nКомментарий: {data['comment']}\nДата: {data['date']}"
        )
        await message.answer("Спасибо! Ваша заявка принята.")
        # Убираем пользователя из процесса
        user_data.pop(user_id)
