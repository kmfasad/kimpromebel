import os
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ------------------- Конфиг -------------------
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "433698201"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN not set!")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ------------------- Клавиатуры -------------------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Консультация")],
        [KeyboardButton(text="🛠 Заказать проект")],
        [KeyboardButton(text="📞 Контакты")]
    ],
    resize_keyboard=True
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отменить")]], 
    resize_keyboard=True
)

# ------------------- Состояния -------------------
class Consultation(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class ProjectOrder(StatesGroup):
    waiting_for_description = State()
    waiting_for_name = State()
    waiting_for_phone = State()

# ------------------- Handlers -------------------
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! 👋 Выберите опцию:", reply_markup=main_kb)

@router.message(F.text == "❌ Отменить")
async def cancel_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=main_kb)

@router.message(F.text == "✅ Консультация")
async def consultation_cmd(message: types.Message, state: FSMContext):
    await message.answer("Как вас зовут?", reply_markup=cancel_kb)
    await state.set_state(Consultation.waiting_for_name)

@router.message(Consultation.waiting_for_name)
async def consultation_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Ваш номер телефона?", reply_markup=cancel_kb)
    await state.set_state(Consultation.waiting_for_phone)

@router.message(Consultation.waiting_for_phone)
async def consultation_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(f"Спасибо, {data.get('name')}! Мы свяжемся с вами.", reply_markup=main_kb)
    await bot.send_message(ADMIN_ID, f"Новая заявка: {data.get('name')}, {message.text}")
    await state.clear()

@router.message(F.text == "📞 Контакты")
async def contacts_cmd(message: types.Message):
    await message.answer("Email: kimpromebel@gmail.com\nTelegram: @mihailkuvila")

# ------------------- FastAPI -------------------
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    print("Bot starting up...")
    if WEBHOOK_URL and TOKEN:
        webhook_url = f"{WEBHOOK_URL}/webhook/{TOKEN}"
        try:
            await bot.set_webhook(webhook_url)
            print(f"Webhook set: {webhook_url}")
        except Exception as e:
            print(f"Webhook error: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    print("Bot shutting down...")
    await bot.session.close()

@app.post("/webhook/{token}")
async def webhook(request: Request, token: str):
    if token == TOKEN:
        update = types.Update(**await request.json())
        await dp.feed_update(bot, update)
        return {"ok": True}
    return {"error": "Invalid token"}

@app.get("/")
async def health_check():
    return {"status": "ok", "bot": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
