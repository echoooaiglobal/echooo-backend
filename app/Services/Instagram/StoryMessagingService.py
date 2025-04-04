from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class StoryMessagingService:
    def __init__(self, page):
        self.page = page

    async def reply_to_story(self, message):
        try:
            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            await story_locator.click()
            await self.page.wait_for_timeout(3000)

            message_input = self.page.locator("xpath=//textarea[contains(@placeholder, 'Reply to')]")
            await message_input.click()
            await self.page.wait_for_timeout(1000)

            message_input.fill(message)
            # for char in message:
            #     await message_input.type(char, delay=20)
            await self.page.wait_for_timeout(1000)

            await message_input.press("Enter")
            await self.page.wait_for_timeout(5000)

            # return "✅ Story Message Sent"
            return True
        
        except PlaywrightTimeoutError:
            # return "⚠️ Timeout while interacting with the story."
            return False
        except Exception as e:
            # return f"⚠️ Story Message Not Sent: {str(e)}"
            return False