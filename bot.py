import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, GROUP_CHAT_ID
from database import db
from keyboards import create_topic_keyboard, create_request_keyboard, create_solved_keyboard, create_floor_keyboard

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Create main keyboard
main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="So'rov yaratish")]
    ],
    resize_keyboard=True
)

# States
class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_department = State()
    waiting_for_floor = State()

class RequestStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_description = State()
    waiting_for_reply = State()

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_data = await db.get_user_data(message.from_user.id)
    
    if user_data:
        await message.answer(
            f"Xush kelibsiz, {user_data['name']}! 'So'rov yaratish' tugmasini bosib yangi so'rov yaratishingiz mumkin.",
            reply_markup=main_keyboard
        )
    else:
        await message.answer(
            "Xush kelibsiz! Iltimos, telefon raqamingizni ulashish uchun tugmani bosing.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Telefon raqamini ulashish", request_contact=True)]],
                resize_keyboard=True
            )
        )
        await message.answer("Iltimos, telefon raqamingizni ulashish uchun quyidagi tugmani bosing.")

@dp.message(F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Iltimos, to'liq ismingizni kiriting:")
    await state.set_state(RegistrationStates.waiting_for_name)

@dp.message(RegistrationStates.waiting_for_name)
async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Iltimos, bo'limingizni kiriting:")
    await state.set_state(RegistrationStates.waiting_for_department)

@dp.message(RegistrationStates.waiting_for_department)
async def handle_department(message: types.Message, state: FSMContext):
    await state.update_data(department=message.text)
    await message.answer("Iltimos, qavatni tanlang:", reply_markup=create_floor_keyboard())
    await state.set_state(RegistrationStates.waiting_for_floor)

@dp.callback_query(F.data.startswith("floor_"))
async def handle_floor_selection(callback: types.CallbackQuery, state: FSMContext):
    floor = callback.data.split("_")[1]
    user_data = await state.get_data()
    user_data['floor'] = floor
    user_data['telegram_id'] = callback.from_user.id
    user_data['username'] = callback.from_user.username

    # Save to database
    if await db.save_user(user_data):
        await state.clear()
        await callback.message.answer(
            f"Ro'yxatdan o'tish muvaffaqiyatli yakunlandi, {user_data['name']}! Endi siz 'So'rov yaratish' tugmasini bosib so'rov yaratishingiz mumkin.",
            reply_markup=main_keyboard
        )
    else:
        await callback.message.answer("Ro'yxatdan o'tish muvaffaqiyatsiz tugadi. Iltimos, keyinroq qayta urinib ko'ring.")

@dp.message(F.text == "So'rov yaratish")
async def handle_create_request(message: types.Message, state: FSMContext):
    user_data = await db.get_user_data(message.from_user.id)
    if not user_data:
        await message.answer("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return
    
    await message.answer("Iltimos, so'rovingiz mavzusini tanlang:", reply_markup=create_topic_keyboard())
    await state.set_state(RequestStates.waiting_for_topic)

@dp.callback_query(F.data.startswith("topic_"))
async def handle_topic_selection(callback: types.CallbackQuery, state: FSMContext):
    topic = callback.data.split("_")[1]
    await state.update_data(topic=topic)
    await callback.message.answer("Iltimos, so'rovingizni tavsiflang:")
    await state.set_state(RequestStates.waiting_for_description)

@dp.message(RequestStates.waiting_for_description)
async def handle_description(message: types.Message, state: FSMContext):
    user_data = await db.get_user_data(message.from_user.id)
    request_data = await state.get_data()
    
    # Generate a unique request ID (timestamp + user_id)
    request_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{message.from_user.id}"
    logging.info(f"Creating new request with ID: '{request_id}'")
    
    # Create request message
    request_text = (
        f"Yangi So'rov:\n\n"
        f"Kimdan: {user_data['name']}\n"
        f"Bo'lim: {user_data['department']}\n"
        f"Qavat: {user_data['floor']}\n"
        f"Mavzu: {request_data['topic']}\n"
        f"Tavsif: {message.text}\n\n"
        f"So'rov ID: {request_id}"
    )

    # Save to database first
    request_data.update({
        'request_id': request_id,
        'user_id': message.from_user.id,
        'name': user_data['name'],
        'department': user_data['department'],
        'floor': user_data['floor'],
        'description': message.text
    })

    if await db.save_request(request_data):
        # Send to group with inline keyboard
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=request_text,
            reply_markup=create_request_keyboard(request_id)
        )
        await state.clear()
        await message.answer("So'rovingiz muvaffaqiyatli yuborildi!")
    else:
        await message.answer("So'rov yuborish muvaffaqiyatsiz tugadi. Iltimos, keyinroq qayta urinib ko'ring.")

@dp.callback_query(F.data.startswith("reply_"))
async def handle_reply_button(callback: types.CallbackQuery, state: FSMContext):
    # Get the full request ID from the message text
    message_text = callback.message.text
    request_id = message_text.split("So'rov ID: ")[-1].strip()
    logging.info(f"Reply button clicked for request: '{request_id}'")
    await state.update_data(request_id=request_id)
    await callback.message.answer("Iltimos, javobingizni kiriting:")
    await state.set_state(RequestStates.waiting_for_reply)

@dp.message(RequestStates.waiting_for_reply)
async def handle_reply_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    request_id = data['request_id'].strip()
    logging.info(f"Processing reply for request: '{request_id}'")
    
    # Get request details from database
    try:
        result = await db.get_request_data(request_id)
        if result:
            user_id = result['user_id']
            # Send reply to the user
            await bot.send_message(
                chat_id=int(user_id),
                text=f"So'rovingizga javob:\n{message.text}"
            )
            # Update the original message in the group
            await message.answer("Javob muvaffaqiyatli yuborildi!")
        else:
            logging.error(f"Request not found for reply: '{request_id}'")
            await message.answer("So'rov topilmadi. Iltimos, qayta urinib ko'ring.")
    except Exception as e:
        logging.error(f"Error sending reply: {e}")
        await message.answer("Javob yuborish muvaffaqiyatsiz tugadi. Iltimos, keyinroq qayta urinib ko'ring.")
    
    await state.clear()

@dp.callback_query(F.data.startswith("accept_"))
async def handle_accept_button(callback: types.CallbackQuery):
    # Get the full request ID from the message text
    message_text = callback.message.text
    request_id = message_text.split("So'rov ID: ")[-1].strip()
    logging.info(f"Accept button clicked for request: '{request_id}'")
    
    try:
        # Get request data to check if it's already accepted
        request_data = await db.get_request_data(request_id)
        if not request_data:
            logging.error(f"Request not found for acceptance: '{request_id}'")
            await callback.answer("So'rov topilmadi!")
            return
            
        if request_data['status'] == "Accepted":
            await callback.answer("Bu so'rov allaqachon qabul qilingan!")
            return
            
        if await db.update_request_status(request_id, "Accepted", callback.from_user.username):
            # Update message with new keyboard
            await callback.message.edit_reply_markup(
                reply_markup=create_solved_keyboard(request_id)
            )
            await callback.answer("So'rov qabul qilindi!")
            
            # Send notification to the user
            await bot.send_message(
                chat_id=int(request_data['user_id']),
                text=f"So'rovingiz qabul qilindi va tez orada hal qilinadi!"
            )
        else:
            await callback.answer("So'rovni qabul qilish muvaffaqiyatsiz tugadi")
    except Exception as e:
        logging.error(f"Error accepting request: {e}")
        await callback.answer("So'rovni qabul qilish muvaffaqiyatsiz tugadi")

@dp.callback_query(F.data.startswith("solve_"))
async def handle_solve_button(callback: types.CallbackQuery):
    # Get the full request ID from the message text
    message_text = callback.message.text
    request_id = message_text.split("So'rov ID: ")[-1].strip()
    logging.info(f"Solve button clicked for request: '{request_id}'")
    
    try:
        # Get request data to check if it's already solved
        request_data = await db.get_request_data(request_id)
        if not request_data:
            logging.error(f"Request not found for solving: '{request_id}'")
            await callback.answer("So'rov topilmadi!")
            return
            
        if request_data['status'] == "Solved":
            await callback.answer("Bu so'rov allaqachon hal qilingan!")
            return
            
        if request_data['accepted_by'] != callback.from_user.username:
            await callback.answer("Faqat so'rovni qabul qilgan shaxs uni hal qilgani sifatida belgilashi mumkin!")
            return
            
        if await db.update_request_status(request_id, "Solved"):
            # Remove keyboard
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.answer("So'rov hal qilingan sifatida belgilandi!")
            
            # Send notification to the user
            await bot.send_message(
                chat_id=int(request_data['user_id']),
                text=f"So'rovingiz hal qilindi!"
            )
        else:
            await callback.answer("So'rovni hal qilingan sifatida belgilash muvaffaqiyatsiz tugadi")
    except Exception as e:
        logging.error(f"Error solving request: {e}")
        await callback.answer("So'rovni hal qilingan sifatida belgilash muvaffaqiyatsiz tugadi")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 