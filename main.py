import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ------------------- Конфиг -------------------
TOKEN = os.getenv("7980968906:AAHlFiJRX9K0dkeMZw3M87Qszgm68E4IdOI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "433698201"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # пусто при первом деплое
WEBHOOK_PATH = f"/webhook/{TOKEN}"

if not TOKEN:
    raise ValueError("Установите переменную окружения BOT_TOKEN")

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

@router.message(F.text == "✅ Консультация")
async def start_consultation(message: types.Message, state: FSMContext):
    await message.answer("Как вас зовут? ✍️", reply_markup=cancel_kb)
    await state.set_state(Consultation.waiting_for_name)

@router.message(Consultation.waiting_for_name)
async def consult_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отправьте ваш номер телефона 📱", reply_markup=phone_kb)
    await state.set_state(Consultation.waiting_for_phone)

@router.message(F.contact, Consultation.waiting_for_phone)
async def consult_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_confirm(message, state, from_project=False)

@router.message(Consultation.waiting_for_phone)
async def consult_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await ask_confirm(message, state, from_project=False)

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
    await message.answer("Отправьте номер телефона 📱", reply_markup=phone_kb)
    await state.set_state(ProjectOrder.waiting_for_phone)

@router.message(F.contact, ProjectOrder.waiting_for_phone)
async def project_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_confirm(message, state, from_project=True)

@router.message(ProjectOrder.waiting_for_phone)
async def project_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await ask_confirm(message, state, from_project=True)

@router.message(F.text == "✅ Отправить")
async def confirm_submission(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state and current_state.startswith("Consultation"):
        await message.answer("Спасибо! Мы скоро с вами свяжемся. 🙌", reply_markup=main_kb)
        await bot.send_message(ADMIN_ID, f"Новая заявка: {data}")
    else:
        await message.answer("Благодарим за заказ! Мы скоро с вами свяжемся. 🙌", reply_markup=main_kb)
        await bot.send_message(ADMIN_ID, f"Новый проект: {data}")

    await state.clear()

async def ask_confirm(message: types.Message, state: FSMContext, from_project: bool):
    data = await state.get_data()
    text = "Подтвердите отправку заявки 👇\n\n"
    if from_project:
        text += f"Проект: {data.get('description')}\nИмя: {data.get('name')}\nТелефон: {data.get('phone')}"
        await state.set_state(ProjectOrder.waiting_for_confirm)
    else:
        text += f"Имя: {data.get('name')}\nТелефон: {data.get('phone')}"
        await state.set_state(Consultation.waiting_for_confirm)
    await message.answer(text, reply_markup=confirm_kb)

@router.message(F.text == "📞 Контакты")
async def send_contacts(message: types.Message):
    await message.answer("Email: kimpromebel@gmail.com\nTelegram: @mihailkuvila")

# fallback
@router.message()
async def fallback(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нажмите кнопку ниже 👇", reply_markup=main_kb)
    else:
        await message.answer("Завершите форму 📝 или ❌ Отмените", reply_markup=cancel_kb)

# FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    if WEBHOOK_URL:
        try:
            await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
        except Exception as e:
            print("Webhook не установлен:", e)
    else:
        print("WEBHOOK_URL не задан, пропускаем установку webhook")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
