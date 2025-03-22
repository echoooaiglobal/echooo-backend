from config.settings import INSTAGRAM_URL
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

class ProfileAnalysisService:
    def __init__(self, page):
        self.page = page
    
    def check_profile(self, username):
        # self.page.goto(f"{INSTAGRAM_URL}/{username}/")
        # self.page.wait_for_timeout(5000)  # Wait for the page to load

        try:
            # Check if the profile is private
            is_private = self.page.locator("text=This Account is Private").is_visible()
            print(f"🔹 Profile private: {is_private}")

            # Check if DM button exists
            dm_locator = self.page.locator("xpath=//div[@role='button' and contains(., 'Message')]")
            can_dm = dm_locator.is_visible()
            print(f"🔹 Can DM: {can_dm}")

            # Check if user has an active story
            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            has_story = story_locator.is_visible()
            print(f"🔹 Has Story: {has_story}")

            return {
                "is_public": not is_private,
                "can_dm": can_dm,
                "has_story": has_story
            }
        except PlaywrightTimeoutError:
            print("⚠️ Timeout while analyzing profile!")
            return {"is_public": False, "can_dm": False, "has_story": False}