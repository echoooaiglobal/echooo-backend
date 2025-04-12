from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

class StoryMessagingService:
    def __init__(self, page: Page):
        self.page = page

    async def close_story_view(self):
        """Attempt to close the story view by clicking the close button or pressing Escape"""
        try:
            # Try clicking the close button (X) if visible
            close_btn = self.page.locator("xpath=//div[@role='button' and .//*[local-name()='svg' and @aria-label='Close']]")
            if await close_btn.count() > 0:
                await close_btn.click()
            else:
                # Fallback to pressing Escape key
                await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"⚠️ Warning: Could not properly close story view - {str(e)}")

    async def reply_to_story(self, message: str):
        try:
            # Locate and click the story
            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            await story_locator.first.click()
            await self.page.wait_for_timeout(3000)

            # Try to find reply input
            message_input = self.page.locator("xpath=//textarea[contains(@placeholder, 'Reply to')]")
            
            if await message_input.count() == 0:
                print("⚠️ Reply box not found in story. Replies might be restricted.")
                await self.close_story_view()
                return False, "REPLY_BOX_NOT_FOUND", "Replies Restricted"
                
            await message_input.click()
            await self.page.wait_for_timeout(1000)
            await message_input.fill(message)
            await self.page.wait_for_timeout(1000)

            # Send the message
            async with self.page.expect_response(
                lambda response: '/api/v1/direct_v2/threads/broadcast/reel_share/' in response.url
            ) as response_info:
                await message_input.press("Enter")
                await self.page.wait_for_timeout(3000)  # Wait for send to complete

            response = await response_info.value
            send_success = response.status == 200

            if send_success:
                print("✅ Story reply sent successfully.")
            else:
                print(f"⚠️ Failed to send story reply. Status code: {response.status}")

            # Close the story view regardless of success
            await self.close_story_view()
            await self.page.wait_for_timeout(1000)

            return (
                send_success,
                None if send_success else str(response.status),
                None if send_success else ("Story Restriction" if response.status == 403 else "Restriction")
            )

        except PlaywrightTimeoutError:
            print("⚠️ Timeout while interacting with the story.")
            await self.close_story_view()
            return False, "TIMEOUT_ERROR", "Story Restriction"
        except Exception as e:
            print(f"⚠️ An error occurred: {str(e)}")
            await self.close_story_view()
            return False, "UNKNOWN_ERROR", 'Unknown error'