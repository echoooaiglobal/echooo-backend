from config.settings import settings
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class ProfileAnalysisService:
    def __init__(self, page):
        self.page = page
    
    async def check_profile(self, username):
        try:
            # Basic profile checks
            is_private = await self.page.locator("text=This Account is Private").is_visible()
            print(f"🔹 Profile private: {is_private}")

            dm_locator = self.page.locator("xpath=//div[@role='button' and contains(., 'Message')]")
            can_dm = await dm_locator.is_visible()
            print(f"🔹 Can DM: {can_dm}")

            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            has_story = await story_locator.is_visible()
            print(f"🔹 Has Story: {has_story}")

            # Highlight detection with multiple strategies
            highlight_locators = [
                "._acaz",  # Class-based
                "xpath=//img[contains(@alt, 'highlight story picture')]",  # Alt text
                "xpath=//div[contains(@aria-label, 'Story Highlights')]"  # Aria label
            ]
            
            has_highlights = False
            for locator in highlight_locators:
                if await self.page.locator(locator).count() > 0:
                    has_highlights = True
                    break
            
            print(f"🔹 Has Highlights: {has_highlights}")

            return {
                "is_public": not is_private,
                "can_dm": can_dm,
                "has_story": has_story,
                "has_highlights": has_highlights
            }

        except PlaywrightTimeoutError:
            print("⚠️ Timeout while analyzing profile!")
            return {
                "is_public": False,
                "can_dm": False,
                "has_story": False,
                "has_highlights": False
            }
        except Exception as e:
            print(f"⚠️ Unexpected error analyzing profile: {str(e)}")
            return {
                "is_public": False,
                "can_dm": False,
                "has_story": False,
                "has_highlights": False
            }