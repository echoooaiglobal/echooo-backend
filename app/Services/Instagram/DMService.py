from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

class DMService:
    def __init__(self, page):
        self.page = page  # No reloading, using the same page instance

    def send_message(self, message):
        try:
            # Wait for the "Message" button and click it
            message_button = self.page.locator("xpath=//div[@role='button' and contains(., 'Message')]")
            message_button.click()
            print("✅ Clicked on the Message button.")
            self.page.wait_for_timeout(2000)  # Wait for the DM modal to load

            # Close notification box in DM modal if it appears
            try:
                not_now_button = self.page.locator("xpath=//button[contains(text(),'Not Now')]")
                not_now_button.wait_for(state="visible", timeout=5000)  # Wait for the button to be visible
                not_now_button.click()
                print("✅ Closed notification box in DM modal.")
                self.page.wait_for_timeout(1000)
            except Exception:
                print("⚠️ Notification box in DM modal not present or already closed.")

            # Locate the message input element (textarea or div with role=textbox)
            try:
                text_input = self.page.locator("xpath=//textarea[@placeholder='Message...']")

                if not text_input.is_visible():
                    raise Exception("Textarea not found, trying div with role=textbox.")
                print("✅ Found textarea input.")
            except Exception:
                text_input = self.page.locator("xpath=//div[@role='textbox']")
                print("✅ Found textarea input.")

            # Focus and type the message
            text_input.click()
            self.page.wait_for_timeout(500)  # Wait for the input to be focused
            text_input.type(message, delay=50)  # human typing
            self.page.wait_for_timeout(1000)

            # Press Enter to send the message
            text_input.press("Enter")
            self.page.wait_for_timeout(5000)  # Wait for the message to send

            return "✅ DM Sent"
        
        except PlaywrightTimeoutError:
            return "⚠️ Timeout while interacting with the DM modal."
        except Exception as e:
            return f"⚠️ DM Not Sent: {str(e)}"