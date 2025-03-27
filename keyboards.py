from aiogram import types
from config import TOPICS

def create_topic_keyboard():
    keyboard = []
    for topic in TOPICS:
        keyboard.append([types.InlineKeyboardButton(text=topic, callback_data=f"topic_{topic}")])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_request_keyboard(request_id):
    # Ensure request_id is a string and use the full request ID
    request_id = str(request_id)
    keyboard = [
        [
            types.InlineKeyboardButton(text="Reply", callback_data=f"reply_{request_id}"),
            types.InlineKeyboardButton(text="Accept", callback_data=f"accept_{request_id}")
        ]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_solved_keyboard(request_id):
    # Ensure request_id is a string and use the full request ID
    request_id = str(request_id)
    keyboard = [
        [
            types.InlineKeyboardButton(text="Reply", callback_data=f"reply_{request_id}"),
            types.InlineKeyboardButton(text="Mark as Solved", callback_data=f"solve_{request_id}")
        ]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard) 