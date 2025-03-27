import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import SCOPES, SPREADSHEET_ID, GOOGLE_SHEETS_CREDENTIALS_FILE, USERS_RANGE, REQUESTS_RANGE

class Database:
    def __init__(self):
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        try:
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
            self.service = build('sheets', 'v4', credentials=creds)
        except Exception as e:
            logging.error(f"Failed to initialize Google Sheets service: {e}")
            raise

    async def get_user_data(self, telegram_id):
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=USERS_RANGE
            ).execute()
            values = result.get('values', [])
            
            for row in values:
                if str(row[4]) == str(telegram_id):  # Check Telegram ID
                    return {
                        'name': row[0],
                        'phone': row[1],
                        'department': row[2],
                        'floor': row[3],
                        'telegram_id': row[4],
                        'username': row[5]
                    }
            return None
        except HttpError as error:
            logging.error(f"An error occurred while getting user data: {error}")
            return None

    async def get_request_data(self, request_id):
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=REQUESTS_RANGE
            ).execute()
            values = result.get('values', [])
            
            logging.info(f"Searching for request ID: {request_id}")
            logging.info(f"Total requests found: {len(values)}")
            
            # Skip header row
            for row in values[1:]:
                current_id = str(row[0]).strip()
                search_id = str(request_id).strip()
                logging.info(f"Comparing current_id: '{current_id}' with search_id: '{search_id}'")
                
                if current_id == search_id:
                    logging.info(f"Found matching request: {current_id}")
                    return {
                        'request_id': row[0],
                        'user_id': row[1],
                        'name': row[2],
                        'department': row[3],
                        'floor': row[4],
                        'topic': row[5],
                        'description': row[6],
                        'date': row[7],
                        'status': row[8] if len(row) > 8 else "Pending",
                        'accepted_by': row[9] if len(row) > 9 else ""
                    }
            
            logging.error(f"Request not found: {request_id}")
            return None
        except HttpError as error:
            logging.error(f"An error occurred while getting request data: {error}")
            return None

    async def save_user(self, user_data):
        try:
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
            self.service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=USERS_RANGE,
                valueInputOption='RAW',
                body=body
            ).execute()
            return True
        except HttpError as error:
            logging.error(f"An error occurred while saving user: {error}")
            return False

    async def save_request(self, request_data):
        try:
            values = [[
                request_data['request_id'],
                request_data['user_id'],
                request_data['name'],
                request_data['department'],
                request_data['floor'],
                request_data['topic'],
                request_data['description'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Pending",
                ""  # Accepted by
            ]]
            body = {'values': values}
            self.service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=REQUESTS_RANGE,
                valueInputOption='RAW',
                body=body
            ).execute()
            logging.info(f"Request saved successfully: {request_data['request_id']}")
            return True
        except HttpError as error:
            logging.error(f"An error occurred while saving request: {error}")
            return False

    async def update_request_status(self, request_id, status, accepted_by=None):
        try:
            # Find the row with the request_id
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=REQUESTS_RANGE
            ).execute()
            values = result.get('values', [])
            
            logging.info(f"Updating status for request ID: {request_id}")
            logging.info(f"Total requests found: {len(values)}")
            
            # Skip header row and start from row 2
            for i, row in enumerate(values[1:], start=2):
                current_id = str(row[0]).strip()
                search_id = str(request_id).strip()
                logging.info(f"Comparing current_id: '{current_id}' with search_id: '{search_id}'")
                
                if current_id == search_id:
                    logging.info(f"Found matching request for update: {current_id}")
                    # Update status and accepted_by
                    body = {'values': [[status, accepted_by if accepted_by else row[9] if len(row) > 9 else ""]]}
                    self.service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f'Requests!I{i}:J{i}',
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    logging.info(f"Request status updated successfully: {request_id}")
                    return True
            
            logging.error(f"Request not found for status update: {request_id}")
            return False
        except HttpError as error:
            logging.error(f"An error occurred while updating request status: {error}")
            return False

# Create a singleton instance
db = Database() 