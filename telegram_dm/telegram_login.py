import os
import sys
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from browser_use import Agent, Controller
import json
from pydantic import BaseModel
# Define the output format as a Pydantic model
class FiveDigitCode(BaseModel):
    code: str

load_dotenv()

TELEGRAM_PASSWORD = os.getenv('TELEGRAM_PASSWORD')
TELEGRAM_PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


async def login_get_cookie(password: str, phone_number: str):

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", 
                    api_key=GEMINI_API_KEY)
    browser = Browser(
        config=BrowserConfig(
            headless=False
        )
    )

    context = await browser.new_context(
		config=BrowserContextConfig(
            cookies_file="cookies.json"
        ),
    )

    # Create the agent with detailed instructions

    task_qr = f"""Go to https://web.telegram.org/a/ and try to login with QR code.
            Wait until the main chat interface loads or a password is requested. 
            This will happen automatically as the user will facilitate offscreen. 
            The password is {password}.
            Navigate to the settings page. Visit the active sessions.
            Go to the "change password" section but quit just before actually changing the password.
            Go back to the main chat interface, and view the chat with "Telegram". 
            Scroll to the bottom.
            Output just the last 5-digit code from the chat, nothing else"""
    
    task_phone = f"""Go to https://web.telegram.org/a/ and try to login with phone number.
            You will need to click in the phone number box, and hit backspace several times first.
            The phone number is {phone_number}.
            The password is {password}.
            View the chat with "Telegram". Scroll to the bottom.
            Output just the last 5-digit code from the chat, nothing else"""
    
    agent = Agent(
        task=task_qr,
        llm=llm,
        browser_context=context
    )

    history = await agent.run(max_steps=100)  
    agent.create_history_gif(show_task=False)
    cookies = await context.session.context.cookies()
    storage_state = await context.session.context.storage_state()
    open("storage_state.json", "w").write(json.dumps(storage_state))
    await browser.close()
    code = history.final_result()
    return code

def main():    
    print(asyncio.run(login_get_cookie(TELEGRAM_PASSWORD, TELEGRAM_PHONE_NUMBER)))

if __name__ == "__main__":
    main()