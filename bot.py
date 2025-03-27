import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States
class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_department = State()
    waiting_for_floor = State()

class RequestStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_description = State()

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE'), scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Welcome! Please register by sharing your phone number.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Share Phone Number", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await message.answer("Please click the button below to share your phone number.")

@dp.message(F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Please enter your full name:")
    await state.set_state(RegistrationStates.waiting_for_name)

@dp.message(RegistrationStates.waiting_for_name)
async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Please enter your department:")
    await state.set_state(RegistrationStates.waiting_for_department)

@dp.message(RegistrationStates.waiting_for_department)
async def handle_department(message: types.Message, state: FSMContext):
    await state.update_data(department=message.text)
    await message.answer("Please enter your floor number:")
    await state.set_state(RegistrationStates.waiting_for_floor)

@dp.message(RegistrationStates.waiting_for_floor)
async def handle_floor(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_data['floor'] = message.text
    user_data['telegram_id'] = message.from_user.id
    user_data['username'] = message.from_user.username

    # Save to Google Sheets
    try:
        service = get_sheets_service()
        values = [[
            user_data['name'],
            user_data['phone'],
            user_data['department'],
            user_data['floor'],
            user_data['telegram_id'],
            user_data['username'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]]
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Users!A:G',
            valueInputOption='RAW',
            body=body
        ).execute()
    except HttpError as error:
        logging.error(f"An error occurred: {error}")
        await message.answer("Registration failed. Please try again later.")
        return

    await state.clear()
    await message.answer(
        "Registration completed! You can now create requests using /request command.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(Command("request"))
async def cmd_request(message: types.Message, state: FSMContext):
    await message.answer("Please enter the topic of your request:")
    await state.set_state(RequestStates.waiting_for_topic)

@dp.message(RequestStates.waiting_for_topic)
async def handle_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await message.answer("Please describe your request:")
    await state.set_state(RequestStates.waiting_for_description)

@dp.message(RequestStates.waiting_for_description)
async def handle_description(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Create request message
    request_text = (
        f"New IT Request:\n\n"
        f"From: @{message.from_user.username}\n"
        f"Topic: {user_data['topic']}\n"
        f"Description: {message.text}\n\n"
        f"To reply, use /reply {message.from_user.id} <your message>"
    )

    # Send to group
    await bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=request_text
    )

    # Save to Google Sheets
    try:
        service = get_sheets_service()
        values = [[
            message.from_user.id,
            message.from_user.username,
            user_data['topic'],
            message.text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending"
        ]]
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Requests!A:F',
            valueInputOption='RAW',
            body=body
        ).execute()
    except HttpError as error:
        logging.error(f"An error occurred: {error}")

    await state.clear()
    await message.answer("Your request has been submitted successfully!")

@dp.message(Command("reply"))
async def cmd_reply(message: types.Message):
    if str(message.chat.id) != GROUP_CHAT_ID:
        return

    try:
        _, user_id, *reply_text = message.text.split()
        reply_text = ' '.join(reply_text)
        
        await bot.send_message(
            chat_id=int(user_id),
            text=f"Reply to your request:\n{reply_text}"
        )
        await message.answer("Reply sent successfully!")
    except Exception as e:
        logging.error(f"Error sending reply: {e}")
        await message.answer("Failed to send reply. Please check the format: /reply <user_id> <message>")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 