from config.settings import INSTAGRAM_URL
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class ProfileAnalysisService:
    def __init__(self, page):
        self.page = page
    
    async def check_profile(self, username):
        try:
            is_private = await self.page.locator("text=This Account is Private").is_visible()
            print(f"🔹 Profile private: {is_private}")

            dm_locator = self.page.locator("xpath=//div[@role='button' and contains(., 'Message')]")
            can_dm = await dm_locator.is_visible()
            print(f"🔹 Can DM: {can_dm}")

            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            has_story = await story_locator.is_visible()
            print(f"🔹 Has Story: {has_story}")

            return {
                "is_public": not is_private,
                "can_dm": can_dm,
                "has_story": has_story
            }
        except PlaywrightTimeoutError:
            print("⚠️ Timeout while analyzing profile!")
            return {"is_public": False, "can_dm": False, "has_story": False}