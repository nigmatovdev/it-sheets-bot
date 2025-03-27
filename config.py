import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# Google Sheets settings
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')

# Predefined topics
TOPICS = [
    "Hardware Issue",
    "Software Issue",
    "Network Issue",
    "Access Request",
    "Other"
]

# Sheet ranges
USERS_RANGE = 'Users!A:G'
REQUESTS_RANGE = 'Requests!A:J' 