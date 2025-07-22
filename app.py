import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router

bot = Bot(token="7980968906:AAHlFiJRX9K0dkeMZw3M87Qszgm68E4IdOI")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

ADMIN_ID = 433698201  # замени на свой ID

# Клавиатура
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
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет! 👋 Я ваш помощник КИМ. Выберите ниже что вас интересует 👇",
        reply_markup=main_kb
    )

# Кнопка "Консультация"
@router.message(F.text == "✅ Консультация")
async def start_consultation(message: types.Message, state: FSMContext):
    await message.answer("Как вас зовут? ✍️")
    await state.set_state(Consultation.waiting_for_name)

@router.message(Consultation.waiting_for_name)
async def consultation_get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{message.text}, пожалуйста, введите ваш номер телефона 📱")
    await state.set_state(Consultation.waiting_for_phone)

@router.message(Consultation.waiting_for_phone)
async def consultation_get_phone(message: types.Message, state: FSMContext):
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

# Кнопка "Проект"
@router.message(F.text == "🛠 Заказать проект")
async def start_project(message: types.Message, state: FSMContext):
    await message.answer("Расскажите, какой проект вас интересует 📐🛋")
    await state.set_state(ProjectOrder.waiting_for_description)

@router.message(ProjectOrder.waiting_for_description)
async def project_get_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Как вас зовут? ✍️")
    await state.set_state(ProjectOrder.waiting_for_name)

@router.message(ProjectOrder.waiting_for_name)
async def project_get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{message.text}, укажите ваш номер телефона 📱")
    await state.set_state(ProjectOrder.waiting_for_phone)

@router.message(ProjectOrder.waiting_for_phone)
async def project_get_phone(message: types.Message, state: FSMContext):
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

# Кнопка "Контакты"
@router.message(F.text == "📞 Контакты")
async def send_contacts(message: types.Message):
    await message.answer(
        "📧 Email: kimpromebel@gmail.com\n"
        "📩 Telegram: @mihailkuvila"
    )

# Фолбэк — если сообщение не в нужный момент
@router.message()
async def fallback(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Пожалуйста, нажмите кнопку ниже, чтобы начать 👇")
    else:
        await message.answer("Пожалуйста, завершите текущую форму 📝")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
