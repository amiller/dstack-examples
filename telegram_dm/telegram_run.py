from telethon import TelegramClient
import telethon
import os
from dotenv import load_dotenv
import telegram_login
import asyncio

load_dotenv()

TELEGRAM_PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
TELEGRAM_PASSWORD = os.getenv('TELEGRAM_PASSWORD')

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')

async def main():
    client = TelegramClient('telegram', TELEGRAM_API_ID, TELEGRAM_API_HASH)

    # Connect to Telegram
    await client.connect()

    # Check if the user is already authorized
    if not await client.is_user_authorized():
        # Send code request
        print(f"Sending code request to {TELEGRAM_PHONE_NUMBER}")
        await client.send_code_request(TELEGRAM_PHONE_NUMBER)
        
        # Get the code from the login page
        code = await telegram_login.login_get_cookie(TELEGRAM_PASSWORD, TELEGRAM_PHONE_NUMBER)
        print(f"Code: {code}")

        # Sign in the user
        try:
            await client.sign_in(TELEGRAM_PHONE_NUMBER, code)
        except telethon.errors.SessionPasswordNeededError:
            await client.sign_in(password=TELEGRAM_PASSWORD)
    
    # Fetch and print dialogs
    async for dialog in client.iter_dialogs():
        print(f'{dialog.name} has ID {dialog.id}')

        # Retrieve all participants
        participants = await client.get_participants(dialog)
        
        # Print each participant's username and ID
        for participant in participants:
            username = participant.username or 'No Username'
            print(f' - {username} (ID: {participant.id})')

if __name__ == "__main__":
    asyncio.run(main())
