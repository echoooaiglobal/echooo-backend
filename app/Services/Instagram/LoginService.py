import os
import json
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from config.settings import INSTAGRAM_URL, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, SESSION_STORAGE_PATH

class LoginService:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(INSTAGRAM_URL)
        self.session_file = Path(SESSION_STORAGE_PATH)

    def human_type(self, locator, text, min_delay=50, max_delay=150):
        for char in text:
            locator.type(char, delay=random.randint(min_delay, max_delay))

    def login(self):
        if self.session_file.exists():
            self.load_session()
            self.page.goto(INSTAGRAM_URL)
            if self.is_logged_in():
                return self.page

        # Perform login
        username_input = self.page.locator("input[name='username']")
        self.human_type(username_input, INSTAGRAM_USERNAME)

        password_input = self.page.locator("input[name='password']")
        self.human_type(password_input, INSTAGRAM_PASSWORD)

        self.page.click("button[type='submit']")
        self.page.wait_for_timeout(5000)

        # If Instagram asks to save login info, dismiss it
        not_now_button = self.page.locator("text=Not Now")
        not_now_button.wait_for(state="visible", timeout=5000)
        not_now_button.click()

        self.page.wait_for_selector("xpath=//a[@href='/']", timeout=10000)
        self.save_session()
        return self.page

    def is_logged_in(self):
        home_page = self.page.get_by_role("link", name="Home")
        return home_page.is_visible()

    def save_session(self):
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        cookies = self.context.cookies()
        local_storage = self.page.evaluate("() => JSON.stringify(localStorage)")
        session_data = {
            "cookies": cookies,
            "local_storage": local_storage
        }
        self.session_file.write_text(json.dumps(session_data))

    def load_session(self):
        # self.page.goto(INSTAGRAM_URL)
        session_data = json.loads(self.session_file.read_text())
        self.context.add_cookies(session_data["cookies"])
        self.page.evaluate(
            """(data) => {
                localStorage.clear();
                for (const [key, value] of Object.entries(data)) {
                    localStorage.setItem(key, value);
                }
            }""",
            json.loads(session_data["local_storage"])
        )

    def close(self):
        self.browser.close()
        self.playwright.stop()
