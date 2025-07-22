import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token="7980968906:AAHlFiJRX9K0dkeMZw3M87Qszgm68E4IdOI")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

ADMIN_ID = 433698201

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Консультация")],
        [KeyboardButton(text="🛠 Заказать проект")],
        [KeyboardButton(text="📞 Контакты")]
    ],
    resize_keyboard=True
)

# Состояния
class Consultation(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class ProjectOrder(StatesGroup):
    waiting_for_description = State()
    waiting_for_name = State()
    waiting_for_phone = State()

# /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет! 👋 Я ваш помощник КИМ. Выберите ниже что вас интересует 👇",
        reply_markup=main_kb
    )

# Кнопка "Консультация"
@dp.message(lambda message: message.text == "✅ Консультация")
async def start_consultation(message: types.Message, state: FSMContext):
    await message.answer("Как вас зовут? ✍️")
    await state.set_state(Consultation.waiting_for_name)

# Кнопка "Проект"
@dp.message(lambda message: message.text == "🛠 Заказать проект")
async def start_project(message: types.Message, state: FSMContext):
    await message.answer("Расскажите, какой проект вас интересует 📐🛋")
    await state.set_state(ProjectOrder.waiting_for_description)

# Кнопка "Контакты"
@dp.message(lambda message: message.text == "📞 Контакты")
async def contacts(message: types.Message):
    await message.answer(
        "📧 Email: kimpromebel@gmail.com\n"
        "📩 Telegram: @mihailkuvila"
    )

# Обработка анкеты "Консультация"
@dp.message(Consultation.waiting_for_name)
async def consult_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{message.text}, пожалуйста, введите ваш номер телефона 📱")
    await state.set_state(Consultation.waiting_for_phone)

@dp.message(Consultation.waiting_for_phone)
async def consult_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await message.answer("Спасибо! Мы скоро с вами свяжемся! 🙌")
    await bot.send_message(
        ADMIN_ID,
        f"📩 Новая заявка на консультацию:\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🆔 От пользователя: @{message.from_user.username or 'без username'}"
    )
    await state.clear()

# Обработка анкеты "Проект"
@dp.message(ProjectOrder.waiting_for_description)
async def project_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Как вас зовут? ✍️")
    await state.set_state(ProjectOrder.waiting_for_name)

@dp.message(ProjectOrder.waiting_for_name)
async def project_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{message.text}, укажите ваш номер телефона 📱")
    await state.set_state(ProjectOrder.waiting_for_phone)

@dp.message(ProjectOrder.waiting_for_phone)
async def project_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await message.answer("Спасибо за заказ! Мы скоро с вами свяжемся. 🙌")
    await bot.send_message(
        ADMIN_ID,
        f"📐 Новый заказ проекта:\n\n"
        f"📝 Проект: {data['description']}\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🆔 От пользователя: @{message.from_user.username or 'без username'}"
    )
    await state.clear()

# Обработка остальных сообщений
@dp.message()
async def fallback(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Пожалуйста, нажмите кнопку ниже, чтобы начать 👇")
    else:
        await message.answer("Пожалуйста, завершите текущую форму 📝")
