from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

class StoryMessagingService:
    def __init__(self, page: Page):
        self.page = page

    async def reply_to_story(self, message: str):
        try:
            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            await story_locator.click()
            await self.page.wait_for_timeout(3000)

            message_input = self.page.locator("xpath=//textarea[contains(@placeholder, 'Reply to')]")
            
            if await message_input.count() == 0:
                print("⚠️ Reply box not found. Replies might be restricted.")
                return False, "REPLY_BOX_NOT_FOUND", "Replies Restricted"
                
            await message_input.click()
            await self.page.wait_for_timeout(1000)

            await message_input.fill(message)
            await self.page.wait_for_timeout(1000)

            async with self.page.expect_response(lambda response: '/api/v1/direct_v2/threads/broadcast/reel_share/' in response.url) as response_info:
                await message_input.press("Enter")
                await self.page.wait_for_timeout(5000)

            response = await response_info.value

            if response.status == 200:
                print("✅ Story reply sent successfully.")
                return True, None, None  # No error
            else:
                print(f"⚠️ Failed to send story reply. Status code: {response.status}")
                return False, str(response.status), "Story Restriction" if response.status == 403 else "Restriction"

        except PlaywrightTimeoutError:
            print("⚠️ Timeout while interacting with the story.")
            return False, "TIMEOUT_ERROR", "Story Restriction"
        except Exception as e:
            print(f"⚠️ An error occurred: {str(e)}")
            return False, "UNKNOWN_ERROR", "Restriction"
