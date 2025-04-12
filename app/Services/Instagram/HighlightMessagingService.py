from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

class HighlightMessagingService:
    def __init__(self, page: Page):
        self.page = page

    async def reply_to_highlight(self, message: str):
        try:
            # 1. Find highlight
            try:
                await self.page.wait_for_selector('li._acaz', state='attached', timeout=10000)
                highlight = self.page.locator('li._acaz').first
                await highlight.wait_for(state='visible')
            except Exception as e:
                print(f"⚠️ Highlight not found or not interactable: {str(e)}")
                return False, "HIGHLIGHTS_NOT_FOUND", "No highlights found"

            # 2. Open highlight with proper loading wait
            await highlight.click()
            
            # Wait for either the reply box or the "Send Message" button to appear
            try:
                await self.page.wait_for_selector(
                    'textarea[placeholder*="Reply"], div[contenteditable="true"], div[aria-label="Send Message"]',
                    timeout=10000,
                    state='attached'
                )
            except:
                print("⚠️ Highlight content failed to load")
                await self.page.keyboard.press('Escape')
                return False, "HIGHLIGHT_LOAD_FAILED", "Highlight didn't load properly"

            # 3. Find reply box (now that we're sure content loaded)
            reply_box = await self.page.query_selector('textarea[placeholder*="Reply"], div[contenteditable="true"]')
            if not reply_box:
                print("⚠️ Reply box not found (viewer may not be allowed to reply)")
                await self.page.keyboard.press('Escape')
                return False, "REPLY_BOX_NOT_FOUND", "Replies restricted"

            # 4. Send message and verify API response
            await reply_box.click()
            await self.page.wait_for_timeout(1000)
            await reply_box.fill(message)
            await self.page.wait_for_timeout(1000)
            
            async with self.page.expect_response(
                lambda response: '/api/v1/direct_v2/threads/broadcast/reel_share/' in response.url
            ) as response_info:
                await reply_box.press("Enter")
                await self.page.wait_for_timeout(3000)  # Wait for API response

            # 5. Verify response
            response = await response_info.value
            send_success = response.status == 200
            await self.page.keyboard.press('Escape')  # Close highlight view

            if send_success:
                print("✅ Highlight reply sent successfully.")
                return True, None, None
            else:
                print(f"⚠️ Failed to send highlight reply. Status: {response.status}")
                return False, str(response.status), "Highlight Restriction"

        except PlaywrightTimeoutError:
            print("⚠️ Timeout during highlight interaction")
            await self.page.keyboard.press('Escape')
            return False, "TIMEOUT_ERROR", "Operation timed out"
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            await self.page.keyboard.press('Escape')
            return False, "UNKNOWN_ERROR", 'Unknown error'