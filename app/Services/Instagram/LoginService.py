import os
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from config.settings import INSTAGRAM_URL, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, SESSION_STORAGE_PATH

class LoginService:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session_file = Path(SESSION_STORAGE_PATH)

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        await self.page.goto(INSTAGRAM_URL)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def human_type(self, locator, text, min_delay=50, max_delay=150):
        for char in text:
            await locator.type(char, delay=random.randint(min_delay, max_delay))

    async def login(self):
        if self.session_file.exists():
            await self.load_session()
            await self.page.goto(INSTAGRAM_URL)
            if await self.is_logged_in():
                return self.page

        # Perform login
        username_input = self.page.locator("input[name='username']")
        await self.human_type(username_input, INSTAGRAM_USERNAME)

        password_input = self.page.locator("input[name='password']")
        await self.human_type(password_input, INSTAGRAM_PASSWORD)

        await self.page.click("button[type='submit']")
        await self.page.wait_for_timeout(5000)

        # If Instagram asks to save login info, dismiss it
        not_now_button = self.page.locator("text=Not Now")
        await not_now_button.wait_for(state="visible", timeout=5000)
        await not_now_button.click()

        await self.page.wait_for_selector("xpath=//a[@href='/']", timeout=10000)
        await self.save_session()
        return self.page

    async def is_logged_in(self):
        home_page = self.page.get_by_role("link", name="Home")
        return await home_page.is_visible()

    async def save_session(self):
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        cookies = await self.context.cookies()
        local_storage = await self.page.evaluate("() => JSON.stringify(localStorage)")
        session_data = {
            "cookies": cookies,
            "local_storage": local_storage
        }
        self.session_file.write_text(json.dumps(session_data))

    async def load_session(self):
        session_data = json.loads(self.session_file.read_text())
        await self.context.add_cookies(session_data["cookies"])
        await self.page.evaluate(
            """(data) => {
                localStorage.clear();
                for (const [key, value] of Object.entries(data)) {
                    localStorage.setItem(key, value);
                }
            }""",
            json.loads(session_data["local_storage"])
        )