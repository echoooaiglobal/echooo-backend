from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

class DMService:
    def __init__(self, page: Page):
        self.page = page

    async def close_dm_modal(self):
        """Attempt to close the DM modal"""
        try:
            close_btn = self.page.locator("xpath=//*[local-name()='svg' and @aria-label='Close']")
            if await close_btn.count() > 0:
                await close_btn.click()
            else:
                await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"⚠️ Warning: Could not properly close DM modal - {str(e)}")

    async def send_message(self, message: str):
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
                print("✅ Found div textbox input.")

            await text_input.click()
            await self.page.wait_for_timeout(500)
            await text_input.fill(message)
            await self.page.wait_for_timeout(1000)

            async with self.page.expect_response(
                lambda response: '/api/v1/direct_v2/threads/broadcast/text/' in response.url
            ) as response_info:
                await text_input.press("Enter")
                await self.page.wait_for_timeout(3000)

            response = await response_info.value
            send_success = response.status == 200

            if send_success:
                print("✅ DM sent successfully.")
            else:
                print(f"⚠️ Failed to send DM. Status code: {response.status}")

            await self.close_dm_modal()
            return (
                send_success,
                None if send_success else str(response.status),
                None if send_success else ("DM Restriction" if response.status == 403 else "Restriction")
            )

        except PlaywrightTimeoutError:
            print("⚠️ Timeout while interacting with the DM modal.")
            await self.close_dm_modal()
            return False, "TIMEOUT_ERROR", "DM Restriction"
        except Exception as e:
            print(f"⚠️ An error occurred: {str(e)}")
            await self.close_dm_modal()
            return False, "UNKNOWN_ERROR", str(e)