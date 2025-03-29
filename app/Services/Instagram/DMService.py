from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class DMService:
    def __init__(self, page):
        self.page = page

    async def send_message(self, message):
        try:
            message_button = self.page.locator("xpath=//div[@role='button' and contains(., 'Message')]")
            await message_button.click()
            print("✅ Clicked on the Message button.")
            await self.page.wait_for_timeout(2000)

            try:
                not_now_button = self.page.locator("xpath=//button[contains(text(),'Not Now')]")
                await not_now_button.wait_for(state="visible", timeout=5000)
                await not_now_button.click()
                print("✅ Closed notification box in DM modal.")
                await self.page.wait_for_timeout(1000)
            except Exception:
                print("⚠️ Notification box in DM modal not present or already closed.")

            try:
                text_input = self.page.locator("xpath=//textarea[@placeholder='Message...']")
                if not await text_input.is_visible():
                    raise Exception("Textarea not found, trying div with role=textbox.")
                print("✅ Found textarea input.")
            except Exception:
                text_input = self.page.locator("xpath=//div[@role='textbox']")
                print("✅ Found textarea input.")

            await text_input.click()
            await self.page.wait_for_timeout(500)
            await text_input.fill(message)
            # await text_input.type(message, delay=50)
            await self.page.wait_for_timeout(1000)

            await text_input.press("Enter")
            await self.page.wait_for_timeout(5000)

            return True
            # return "✅ DM Sent"
        
        except PlaywrightTimeoutError:
            # return "⚠️ Timeout while interacting with the DM modal."
            return False
        except Exception as e:
            return False
            # return f"⚠️ DM Not Sent: {str(e)}"