# IT Support Telegram Bot

This is a Telegram bot designed to handle IT support requests in an organization. The bot allows users to submit support requests, and IT staff to manage and respond to these requests efficiently.

## Features

- User registration with contact information
- Support request creation with predefined topics
- Real-time request status updates
- Inline keyboard navigation
- Google Sheets integration for data storage
- Multi-language support (Uzbek)

## Prerequisites

- Python 3.7 or higher
- Telegram Bot Token
- Google Sheets API credentials
- Required Python packages
- Server with SSH access (e.g., DigitalOcean, AWS, or VPS)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd it-bot
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:

```env
BOT_TOKEN=your_telegram_bot_token
GROUP_CHAT_ID=your_telegram_group_chat_id
SPREADSHEET_ID=your_google_sheets_id
GOOGLE_SHEETS_CREDENTIALS_FILE=path_to_your_credentials.json
```

4. Set up Google Sheets:
   - Create a new Google Cloud Project
   - Enable Google Sheets API
   - Create service account credentials
   - Download the credentials JSON file
   - Share your Google Sheet with the service account email

## Project Structure

```
it-bot/
├── bot.py              # Main bot logic
├── config.py           # Configuration settings
├── database.py         # Database operations
├── keyboards.py        # Keyboard layouts
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

## Usage

1. Start the bot:

```bash
python bot.py
```

2. In Telegram:
   - Start the bot with `/start` command
   - Complete registration process
   - Use "So'rov yaratish" button to create new requests
   - Select topic and provide description
   - Track request status

## Request Flow

1. User starts bot and registers
2. User creates new request
3. IT staff receives request in group chat
4. IT staff can:
   - Accept request
   - Reply to request
   - Mark request as solved
5. User receives notifications about request status

## Google Sheets Structure

### Users Sheet

- Name
- Phone
- Department
- Floor
- Telegram ID
- Username
- Registration Date

### Requests Sheet

- Request ID
- User ID
- Name
- Department
- Floor
- Topic
- Description
- Date
- Status
- Accepted By

## Deployment

### 1. Server Setup

1. Connect to your server via SSH:

```bash
ssh root@your_server_ip
```

2. Update system packages:

```bash
apt update && apt upgrade -y
```

3. Install Python and required tools:

```bash
apt install python3 python3-pip python3-venv git -y
```

4. Create a directory for the bot:

```bash
mkdir /opt/it-bot
cd /opt/it-bot
```

5. Clone the repository:

```bash
git clone <repository-url> .
```

6. Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

7. Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configuration

1. Create and edit the `.env` file:

```bash
nano .env
```

2. Add your environment variables:

```env
BOT_TOKEN=your_telegram_bot_token
GROUP_CHAT_ID=your_telegram_group_chat_id
SPREADSHEET_ID=your_google_sheets_id
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
```

3. Upload your Google Sheets credentials:

```bash
# From your local machine
scp path/to/your/credentials.json root@your_server_ip:/opt/it-bot/credentials.json
```

### 3. Systemd Service Setup

1. Create a systemd service file:

```bash
nano /etc/systemd/system/it-bot.service
```

2. Add the following content:

```ini
[Unit]
Description=IT Support Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/it-bot
Environment=PATH=/opt/it-bot/venv/bin
ExecStart=/opt/it-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable it-bot
systemctl start it-bot
```

4. Check the status:

```bash
systemctl status it-bot
```

5. View logs:

```bash
journalctl -u it-bot -f
```

### 4. Maintenance

- Restart the bot:

```bash
systemctl restart it-bot
```

- Stop the bot:

```bash
systemctl stop it-bot
```

- Update the bot:

```bash
cd /opt/it-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart it-bot
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
