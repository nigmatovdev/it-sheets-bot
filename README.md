# IT Department Request Bot

A Telegram bot for automating IT department requests. Users can register and submit requests that are forwarded to a designated Telegram group.

## Features

- User registration with phone number, name, department, and floor
- Request submission with topic and description
- Automatic forwarding of requests to IT department group
- Ability to reply to requests from the group
- Data storage in Google Sheets

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up Google Sheets:

   - Create a new Google Cloud Project
   - Enable the Google Sheets API
   - Create a service account and download the credentials JSON file
   - Create a new Google Spreadsheet and share it with the service account email
   - Copy the Spreadsheet ID from the URL

3. Configure environment variables:

   - Copy `.env.example` to `.env`
   - Fill in the following variables:
     - `BOT_TOKEN`: Your Telegram bot token from @BotFather
     - `GROUP_CHAT_ID`: The Telegram group ID where requests will be forwarded
     - `GOOGLE_SHEETS_CREDENTIALS_FILE`: Path to your Google Sheets credentials JSON file
     - `SPREADSHEET_ID`: Your Google Spreadsheet ID

4. Run the bot:

```bash
python bot.py
```

## Usage

1. Start the bot with `/start` command
2. Complete the registration process by sharing your phone number and providing required information
3. Use `/request` command to submit a new request
4. IT department can reply to requests using `/reply <user_id> <message>` in the group chat

## Google Sheets Structure

The bot uses two sheets in the spreadsheet:

1. `Users` sheet with columns:

   - Name
   - Phone
   - Department
   - Floor
   - Telegram ID
   - Username
   - Registration Date

2. `Requests` sheet with columns:
   - User ID
   - Username
   - Topic
   - Description
   - Date
   - Status
