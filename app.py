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

ADMIN_ID = 433698201  # Замени на свой ID

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Консультация")],
        [KeyboardButton(text="🛠 Заказать проект")],
        [KeyboardButton(text="📞 Контакты")]
    ],
    resize_keyboard=True
)

# Машины состояний
class Consultation(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class ProjectOrder(StatesGroup):
    waiting_for_description = State()
    waiting_for_name = State()
    waiting_for_phone = State()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет! 👋 Добро пожаловать в KIMpromebelbot. Выберите ниже что вас интересует 👇 ",
        reply_markup=main_kb
    )

@dp.message()
async def handle_buttons(message: types.Message, state: FSMContext):
    text = message.text
    current_state = await state.get_state()

    if text == "✅ Консультация":
        await message.answer("Как вас зовут? ✍️")
        await state.set_state(Consultation.waiting_for_name)

    elif current_state == Consultation.waiting_for_name.state:
        await state.update_data(name=text)
        await message.answer("Пожалуйста, введите ваш номер телефона 📱")
        await state.set_state(Consultation.waiting_for_phone)

    elif current_state == Consultation.waiting_for_phone.state:
        await state.update_data(phone=text)
        data = await state.get_data()
        name = data["name"]
        phone = data["phone"]

        await message.answer("Спасибо! Мы скоро с вами свяжемся! 🙌")
        await bot.send_message(
            ADMIN_ID,
            f"📩 Новая заявка на консультацию:\n\n👤 Имя: {name}\n📱 Телефон: {phone}\n🆔 От пользователя: @{message.from_user.username or 'без username'}"
        )
        await state.clear()

    elif text == "🛠 Заказать проект":
        await message.answer("Расскажите, какой проект вас интересует 📐🛋")
        await state.set_state(ProjectOrder.waiting_for_description)

    elif current_state == ProjectOrder.waiting_for_description.state:
        await state.update_data(description=text)
        await message.answer("Как вас зовут? ✍️")
        await state.set_state(ProjectOrder.waiting_for_name)

    elif current_state == ProjectOrder.waiting_for_name.state:
        await state.update_data(name=text)
        await message.answer("Спасибо! Теперь оставьте, пожалуйста, ваш номер телефона 📱")
        await state.set_state(ProjectOrder.waiting_for_phone)

    elif current_state == ProjectOrder.waiting_for_phone.state:
        await state.update_data(phone=text)
        data = await state.get_data()
        description = data["description"]
        name = data["name"]
        phone = data["phone"]

        await message.answer("Благодарим за заказ! Мы скоро с вами свяжемся. 🙌")
        await bot.send_message(
            ADMIN_ID,
            f"📐 Новый заказ проекта:\n\n📝 Проект: {description}\n👤 Имя: {name}\n📱 Телефон: {phone}\n🆔 От пользователя: @{message.from_user.username or 'без username'}"
        )
        await state.clear()

    elif text == "📞 Контакты":
        await message.answer(
            "📧 Email: kimpromebel@gmail.com\n"
            "📩 Telegram: @mihailkuvila\n"
        )

    else:
        await message.answer("Пожалуйста, выберите вариант ниже 👇")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
