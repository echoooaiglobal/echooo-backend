from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

class StoryMessagingService:
    def __init__(self, page):
        self.page = page

    def reply_to_story(self, message):
        try:
            # Wait for the story ring to be visible and click it
            story_locator = self.page.locator("xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]")
            story_locator.click()
            self.page.wait_for_timeout(3000)  # Wait for the story to load

            # Wait for the message input area to be visible and click it
            message_input = self.page.locator("xpath=//textarea[contains(@placeholder, 'Reply to')]")
            message_input.click()
            self.page.wait_for_timeout(1000)  # Wait for the input to be focused

            # Type the message character by character (simulate human typing)
            for char in message:
                message_input.type(char, delay=20)  # Delay of 20ms between keystrokes
            self.page.wait_for_timeout(1000)

            # Press Enter to send the message
            message_input.press("Enter")
            self.page.wait_for_timeout(5000)  # Wait for the message to send

            return "✅ Story Message Sent"
        
        except PlaywrightTimeoutError:
            return "⚠️ Timeout while interacting with the story."
        except Exception as e:
            return f"⚠️ Story Message Not Sent: {str(e)}"