import os
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ------------------- Конфиг -------------------
TOKEN = "7980968906:AAHlFiJRX9K0dkeMZw3M87Qszgm68E4IdOI"  # твой токен уже вставлен
ADMIN_ID = 433698201
WEBHOOK_PATH = f"/webhook/{TOKEN}"  
WEBHOOK_URL = f"https://YOUR_CLOUD_RUN_URL{WEBHOOK_PATH}"  # <-- заменится после деплоя

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ------------------- клавиатуры -------------------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Консультация")],
        [KeyboardButton(text="🛠 Заказать проект")],
        [KeyboardButton(text="📞 Контакты")]
    ],
    resize_keyboard=True
)
cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отменить")]], resize_keyboard=True, one_time_keyboard=True)
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)],
              [KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True
)
confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Отправить")],
              [KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True
)

# ------------------- состояния -------------------
class Consultation(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_confirm = State()

class ProjectOrder(StatesGroup):
    waiting_for_description = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_confirm = State()

# ------------------- handlers -------------------
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! 👋 Я ваш помощник КИМ. Выберите ниже что вас интересует 👇", reply_markup=main_kb)

@router.message(F.text == "❌ Отменить")
async def cancel_any(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено ❌", reply_markup=main_kb)

# ✅ Консультация
@router.message(F.text == "✅ Консультация")
async def start_consultation(message: types.Message, state: FSMContext):
    await message.answer("Как вас зовут? ✍️", reply_markup=cancel_kb)
    await state.set_state(Consultation.waiting_for_name)

@router.message(Consultation.waiting_for_name)
async def consult_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{message.text}, Отправьте ваш номер телефона 📱", reply_markup=phone_kb)
    await state.set_state(Consultation.waiting_for_phone)

@router.message(F.contact, Consultation.waiting_for_phone)
async def consult_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_confirm(message, state, from_project=False)

@router.message(Consultation.waiting_for_phone)
async def consult_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await ask_confirm(message, state, from_project=False)

# 🛠 Заказать проект
@router.message(F.text == "🛠 Заказать проект")
async def start_project(message: types.Message, state: FSMContext):
    await message.answer("Расскажите, какой проект вас интересует 📐🛋", reply_markup=cancel_kb)
    await state.set_state(ProjectOrder.waiting_for_description)

@router.message(ProjectOrder.waiting_for_description)
async def project_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Как вас зовут? ✍️", reply_markup=cancel_kb)
    await state.set_state(ProjectOrder.waiting_for_name)

@router.message(ProjectOrder.waiting_for_name)
async def project_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{message.text}, Отправьте номер телефона 📱", reply_markup=phone_kb)
    await state.set_state(ProjectOrder.waiting_for_phone)

@router.message(F.contact, ProjectOrder.waiting_for_phone)
async def project_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_confirm(message, state, from_project=True)

@router.message(ProjectOrder.waiting_for_phone)
async def project_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await ask_confirm(message, state, from_project=True)

# ✅ Подтверждение
@router.message(F.text == "✅ Отправить")
async def confirm_submission(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state.startswith("Consultation"):
        await message.answer("Спасибо! Мы скоро с вами свяжемся. 🙌", reply_markup=main_kb)
        await bot.send_message(
            ADMIN_ID,
            f"📩 Новая заявка на консультацию:\n\n"
            f"👤 Имя: {data['name']}\n"
            f"📱 Телефон: {data['phone']}\n"
            f"🆔 От пользователя: @{message.from_user.username or 'без username'}"
        )
    else:
        await message.answer("Благодарим за заказ! Мы скоро с вами свяжемся. 🙌", reply_markup=main_kb)
        await bot.send_message(
            ADMIN_ID,
            f"📐 Новый заказ проекта:\n\n"
            f"📝 Проект: {data['description']}\n"
            f"👤 Имя: {data['name']}\n"
            f"📱 Телефон: {data['phone']}\n"
            f"🆔 От пользователя: @{message.from_user.username or 'без username'}"
        )
    await state.clear()

# подтверждение заявки
async def ask_confirm(message: types.Message, state: FSMContext, from_project: bool):
    data = await state.get_data()
    text = "Подтвердите отправку заявки 👇\n\n"
    if from_project:
        text += f"📝 Проект: {data['description']}\n👤 Имя: {data['name']}\n📱 Телефон: {data['phone']}"
        await state.set_state(ProjectOrder.waiting_for_confirm)
    else:
        text += f"👤 Имя: {data['name']}\n📱 Телефон: {data['phone']}"
        await state.set_state(Consultation.waiting_for_confirm)

    await message.answer(text, reply_markup=confirm_kb)

# 📞 Контакты
@router.message(F.text == "📞 Контакты")
async def send_contacts(message: types.Message):
    await message.answer("📧 Email: kimpromebel@gmail.com\n📩 Telegram: @mihailkuvila")

# fallback
@router.message()
async def fallback(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нажмите кнопку ниже 👇", reply_markup=main_kb)
    else:
        await message.answer("Завершите форму 📝 или ❌ Отмените", reply_markup=cancel_kb)

# ------------------- FastAPI -------------------
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}
